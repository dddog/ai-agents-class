import os
from typing import TypedDict, List, Dict, Any
from typing_extensions import Annotated
import operator
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Send, Command
from langchain.chat_models import init_chat_model
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
from dotenv import load_dotenv

# .env 파일 로드 (LANGCHAIN_API_KEY, OPENAI_API_KEY 등을 .env에서 주입)
load_dotenv()

# LangSmith 연동 설정
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "Country_Guessing_Game"

# 1. State 및 스키마 정의
class State(TypedDict):
    theme: str                     # 예: "유럽 국가"
    quiz_count: int                # 출제할 문제 수
    target_countries: List[str]    # 대상 국가 이름 (정답 목록)
    quizzes: Annotated[List[Dict[str, str]], operator.add]  # 병렬 취합용 퀴즈 목록 (question, answer)
    user_answers: List[str]        # 사용자가 제출한 정답 목록
    evaluation_report: str         # 채점 결과 보고서
    score: int                     # 최종 점수
    hint: str                      # 오답 재도전 힌트 메시지

class CountryTask(TypedDict):
    country: str

class CountryQuiz(BaseModel):
    question: str = Field(description="나라 이름을 직접 언급하지 않고, 랜드마크, 수도, 특징 등을 설명하여 나라를 맞추게 하는 퀴즈 문장")
    answer: str = Field(description="실제 정답 (나라 이름)")

# LLM 및 위키피디아 툴 셋업
llm = init_chat_model("openai:gpt-4o-mini")
wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(lang="ko", top_k_results=1, doc_content_chars_max=1000))
llm_with_tools = llm.bind_tools([wiki_tool])

# 2. 게임 노드 로직
def select_countries(state: State) -> Dict[str, Any]:
    print("--- [노드] select_countries: 테마 기반 국가 선정 ---")
    theme = state.get("theme", "전세계 유명 국가")
    count = state.get("quiz_count", 3)
    
    prompt = f"""
    주제: '{theme}'
    위 주제에 부합하는 나라 이름을 정확히 {count}개 추천해주세요.
    부연 설명이나 기호 없이 한 줄에 한 국가 이름만 작성해주세요.
    """
    response = llm.invoke(prompt)
    countries = [line.strip() for line in response.content.split("\n") if line.strip()]
    countries = countries[:count]
    return {"target_countries": countries}

def dispatch_quizzes(state: State):
    countries = state.get("target_countries", [])
    print(f"--- [라우팅] {len(countries)}개 국가 퀴즈 생성을 병렬 배분 ---")
    return [Send("generate_country_quiz", {"country": c}) for c in countries]

def generate_country_quiz(task: CountryTask) -> Dict[str, Any]:
    target = task["country"]
    print(f"--- [노드(병렬)] generate_country_quiz: '{target}' 퀴즈 생성 중 ---")
    
    try:
        wiki_info = wiki_tool.invoke({"query": target})
    except Exception:
        wiki_info = "해당 국가에 대한 상세 정보 검색 실패."

    prompt = f"""
    위키피디아 정보:
    {wiki_info}
    
    이 정보를 바탕으로, 해당 국가가 어디인지 맞출 수 있는 퀴즈를 생성하세요.
    절대 질문 안에 정답 국가 이름({target})이 직접적으로 노출되어서는 안 됩니다.
    """
    
    structured_llm = llm.with_structured_output(CountryQuiz)
    quiz_data = structured_llm.invoke(prompt)
    
    return {
        "quizzes": [{
            "question": quiz_data.question,
            "answer": target
        }]
    }

def aggregate_quizzes(state: State) -> Dict[str, Any]:
    print("--- [노드] aggregate_quizzes: 병렬 생성된 퀴즈 취합 완료 ---")
    return {}

def quiz_interrupt(state: State) -> Dict[str, Any]:
    print("--- [노드] quiz_interrupt (대기) ---")
    hint = state.get("hint", "")
    if hint:
        print(f"[추가 힌트 시스템]:\n{hint}")
        
    quizzes = state.get("quizzes", [])
    answer = interrupt({
        "questions": [q["question"] for q in quizzes],
        "instruction": "각 퀴즈 번호에 맞는 정답(나라 이름)을 작성하여 전송하세요."
    })
    if isinstance(answer, list):
        return {"user_answers": answer}
    elif isinstance(answer, dict):
        return {"user_answers": answer.get("user_answers", [])}
    return {"user_answers": []}

def grade_quiz(state: State) -> Dict[str, Any]:
    print("--- [노드] grade_quiz: 채점 진행 ---")
    quizzes = state.get("quizzes", [])
    user_answers = state.get("user_answers", [])
    
    report_lines = ["### 게임 채점 결과"]
    correct_count = 0
    total = len(quizzes)
    
    for idx, (quiz, u_ans) in enumerate(zip(quizzes, user_answers)):
        correct_ans = str(quiz["answer"]).strip().lower()
        u_ans_clean = str(u_ans).strip().lower()
        
        is_correct = correct_ans in u_ans_clean or u_ans_clean in correct_ans
        if is_correct:
            correct_count += 1
            report_lines.append(f"Q{idx+1}. 정답! ({correct_ans})")
        else:
            report_lines.append(f"Q{idx+1}. 오답 (제출: {u_ans_clean} / 정답: {correct_ans})")
            
    score = int((correct_count / total) * 100) if total > 0 else 0
    report_lines.append(f"\n최종 점수: {score}점")
    return {"evaluation_report": "\n".join(report_lines), "score": score}

def check_score(state: State) -> str:
    score = state.get("score", 0)
    print(f"--- [조건] check_score: 현재 점수 {score}점 ---")
    if score >= 100:
        return "pass"
    return "fail"

def generate_extra_hint(state: State) -> Dict[str, Any]:
    print("--- [노드] generate_extra_hint: 오답 힌트 생성 ---")
    quizzes = state.get("quizzes", [])
    user_answers = state.get("user_answers", [])
    
    hint_lines = ["틀린 문제에 대한 힌트입니다."]
    for idx, (quiz, u_ans) in enumerate(zip(quizzes, user_answers)):
        correct_ans = str(quiz["answer"]).strip()
        u_ans_clean = str(u_ans).strip().lower()
        
        if correct_ans.lower() not in u_ans_clean:
            first_char = correct_ans[0] if len(correct_ans) > 0 else "?"
            hint_lines.append(f"Q{idx+1} 힌트: 정답은 '{first_char}' (으)로 시작합니다.")
            
    return {"hint": "\n".join(hint_lines)}

# 3. 그래프 조립 및 컴파일
graph_builder = StateGraph(State)

graph_builder.add_node("select_countries", select_countries)
graph_builder.add_node("generate_country_quiz", generate_country_quiz)
graph_builder.add_node("aggregate_quizzes", aggregate_quizzes)
graph_builder.add_node("quiz_interrupt", quiz_interrupt)
graph_builder.add_node("grade_quiz", grade_quiz)
graph_builder.add_node("generate_extra_hint", generate_extra_hint)

graph_builder.add_edge(START, "select_countries")
graph_builder.add_conditional_edges("select_countries", dispatch_quizzes, ["generate_country_quiz"])
graph_builder.add_edge("generate_country_quiz", "aggregate_quizzes")
graph_builder.add_edge("aggregate_quizzes", "quiz_interrupt")
graph_builder.add_edge("quiz_interrupt", "grade_quiz")

graph_builder.add_conditional_edges("grade_quiz", check_score, {"pass": END, "fail": "generate_extra_hint"})
graph_builder.add_edge("generate_extra_hint", "quiz_interrupt")

graph = graph_builder.compile(name="agent")
