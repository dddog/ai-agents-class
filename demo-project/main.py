from typing import TypedDict, List, Dict, Any
from typing_extensions import Annotated
import operator
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Send, Command
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

# 1. State 및 구조체 정의
class State(TypedDict):
    learning_material: str           # 학습자가 제공한 원본 학습용 텍스트 자료
    concepts: List[str]              # 원본 자료에서 추출한 핵심 개념/키워드 리스트
    # 병렬 병합을 위한 Reducer(operator.add) 적용
    flashcards: Annotated[List[Dict[str, str]], operator.add]
    user_answers: List[str]          # interrupt를 통해 수집된 사용자의 퀴즈 답변들
    evaluation_report: str           # 최종 채점 결과 및 피드백 보고서
    score: int                       # 퀴즈 최종 점수
    hint: str                        # 오답 피드백 힌트 메시지
    flashcard_limit: int             # 플래시카드 최대 생성 제한 수

# Send API용 작업 구조체
class FlashcardTask(TypedDict):
    concept: str

# 구조화 출력 스키마
class SingleFlashcard(BaseModel):
    question: str = Field(description="주어진 개념에 대해 묻는 한글 질문")
    answer: str = Field(description="위키피디아 등 검색된 배경지식을 포함한 명확한 개념 설명")

# LLM 초기화 (한글 처리를 위해 OpenAI gpt-4o-mini 모델 활용)
llm = init_chat_model("openai:gpt-4o-mini")

# 위키피디아 툴 셋업 (한국어 설정)
wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper(lang="ko", top_k_results=1, doc_content_chars_max=1000))

# 2. 노드 정의
def parse_material(state: State) -> Dict[str, Any]:
    print("--- [노드] parse_material 실행 ---")
    material = state.get("learning_material", "")
    limit = state.get("flashcard_limit", 5)  # 설정된 생성 제한 수 (기본값 5)
    
    prompt = f"""
    제공된 학습 자료에서 핵심적인 교육 개념이나 전문 용어를 최대 {limit}개만 추출해 주세요.
    각 개념은 불필요한 서술이나 번호, 불릿 기호 없이 한 줄에 하나씩 명확한 단어나 핵심 어구로만 추출해 주세요.
    
    학습 자료:
    {material}
    """
    
    response = llm.invoke(prompt)
    concepts = [line.strip() for line in response.content.split("\n") if line.strip()]
    concepts = concepts[:limit]  # 확실하게 개수 제한 슬라이싱
    return {"concepts": concepts}

def dispatch_flashcards(state: State):
    print(f"--- [라우팅] {len(state.get('concepts', []))}개의 개념을 Send로 병렬 분배 ---")
    return [Send("generate_flashcard", {"concept": c}) for c in state.get("concepts", [])]

def generate_flashcard(task: FlashcardTask) -> Dict[str, Any]:
    concept = task["concept"]
    print(f"--- [노드(병렬)] generate_flashcard: '{concept}' 처리 중 ---")
    
    # 위키피디아 툴을 활용한 배경지식 검색 연동
    try:
        wiki_info = wiki_tool.invoke({"query": concept})
    except Exception:
        wiki_info = "검색 결과 없음"
        
    prompt = f"""
    개념 '{concept}'에 대한 플래시카드를 작성하세요.
    위키피디아 검색 결과를 적극 참고하여 양질의 설명을 만드세요.
    
    위키피디아 검색 결과:
    {wiki_info}
    """
    
    structured_llm = llm.with_structured_output(SingleFlashcard)
    card_data = structured_llm.invoke(prompt)
    
    return {
        "flashcards": [{
            "question": card_data.question,
            "answer": card_data.answer
        }]
    }

def aggregate_flashcards(state: State) -> Dict[str, Any]:
    print("--- [노드] aggregate_flashcards: 모든 병렬 생성 취합 완료 ---")
    return {}

def quiz_interrupt(state: State) -> Dict[str, Any]:
    print("--- [노드] quiz_interrupt 실행 (사용자 피드백 대기) ---")
    hint = state.get("hint", "")
    if hint:
        print(f"[시스템 힌트]: {hint}")
        
    flashcards = state.get("flashcards", [])
    answer = interrupt({
        "questions": [card["question"] for card in flashcards],
        "instruction": "'user_answers' 키값에 각 질문에 대한 답변 목록을 담아 전송해 주세요."
    })
    return {
        "user_answers": answer.get("user_answers", [])
    }

def grade_quiz(state: State) -> Dict[str, Any]:
    print("--- [노드] grade_quiz 실행 ---")
    user_answers = state.get("user_answers", [])
    correct_count = sum([1 for a in user_answers if len(str(a)) > 2])
    total = len(state.get("flashcards", []))
    score = int((correct_count / total) * 100) if total > 0 else 0
    
    report = f"### 퀴즈 평가 결과 보고서\n- 현재 점수: {score}점\n"
    return {"evaluation_report": report, "score": score}

def check_score(state: State) -> str:
    score = state.get("score", 0)
    print(f"--- [조건] check_score: 현재 점수 {score}점 ---")
    if score >= 80:
        return "pass"
    return "fail"

def generate_hint(state: State) -> Dict[str, Any]:
    print("--- [노드] generate_hint (오답 루프 진입) ---")
    hint_msg = "점수가 80점 미만입니다. 개념의 뜻을 다시 한 번 자세히 생각해 보고 재도전하세요!"
    return {"hint": hint_msg}

# 3. 그래프 연결 및 컴파일
graph_builder = StateGraph(State)

graph_builder.add_node("parse_material", parse_material)
graph_builder.add_node("generate_flashcard", generate_flashcard)
graph_builder.add_node("aggregate_flashcards", aggregate_flashcards)
graph_builder.add_node("quiz_interrupt", quiz_interrupt)
graph_builder.add_node("grade_quiz", grade_quiz)
graph_builder.add_node("generate_hint", generate_hint)

graph_builder.add_edge(START, "parse_material")
graph_builder.add_conditional_edges("parse_material", dispatch_flashcards, ["generate_flashcard"])
graph_builder.add_edge("generate_flashcard", "aggregate_flashcards")
graph_builder.add_edge("aggregate_flashcards", "quiz_interrupt")
graph_builder.add_edge("quiz_interrupt", "grade_quiz")

graph_builder.add_conditional_edges("grade_quiz", check_score, {"pass": END, "fail": "generate_hint"})
graph_builder.add_edge("generate_hint", "quiz_interrupt")

memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# 4. 개별 노드 단위 테스트 드라이버 함수 정의
def test_parse_material_node() -> List[str]:
    print("\n=============================================")
    print("[단위 테스트] 2단계: parse_material 노드 검증")
    print("=============================================")
    import os
    file_path = os.path.join(os.path.dirname(__file__), "learning_material.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            material_data = f.read()
    else:
        material_data = "지도학습은 정답이 있는 데이터를 학습합니다.\n비지도학습은 정답이 없는 데이터를 학습합니다."
        
    mock_state = {
        "learning_material": material_data,
        "flashcard_limit": 5
    }
    output = parse_material(mock_state)
    print("\n--- 추출된 개념 결과 ---")
    concepts = output.get("concepts", [])
    for c in concepts:
        print(f"- {c}")
    assert len(concepts) > 0, "오류: 핵심 개념이 추출되지 않았습니다."
    print("\n>> 2단계 parse_material 단위 테스트 통과!")
    return concepts

def test_generate_flashcards_node(concepts: List[str]):
    print("\n=============================================")
    print("[단위 테스트] 3단계: generate_flashcard 노드 검증")
    print("=============================================")
    if not concepts:
        concepts = ["대한민국"]
        
    target_concept = concepts[0]
    test_task = {"concept": target_concept}
    print(f"--- 테스트 타겟 개념: '{target_concept}' ---")
    res = generate_flashcard(test_task)
    print("\n--- 생성된 카드 결과 ---")
    flashcards = res.get("flashcards", [])
    for card in flashcards:
        print(f"질문: {card['question']}")
        print(f"답변: {card['answer']}")
    assert len(flashcards) == 1, "오류: 플래시카드가 생성되지 않았습니다."
    print("\n>> 3단계 generate_flashcard 단위 테스트 통과!")

def run_integration_test():
    import os
    print("\n=============================================")
    print("[통합 테스트 1] 최초 실행 및 interrupt 진입 검증")
    print("=============================================")
    config = {"configurable": {"thread_id": "demo_session_korean"}}
    
    file_path = os.path.join(os.path.dirname(__file__), "learning_material.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            material_data = f.read()
    else:
        material_data = "인공지능 머신러닝 지도학습 비지도학습"
        
    initial_state = {"learning_material": material_data, "flashcard_limit": 5}
    print("그래프 실행 시작...")
    result = graph.invoke(initial_state, config=config)
    print("\n인터럽트 중단 상태 도달. (퀴즈 답변 대기 중)")
    return config

def run_resume_test(config):
    print("\n=============================================")
    print("[통합 테스트 2] Command(resume) 사용자 답변 전송 및 완료 검증")
    print("=============================================")
    
    mock_user_answers = [
        "지도학습은 정답 레이블이 있는 학습입니다.",
        "비지도학습은 정답이 없는 데이터 학습 방식입니다.",
        "강화학습은 보상을 최대화하는 에이전트의 움직임입니다.",
        "분류는 데이터를 군집별 영역으로 가르는 행위입니다.",
        "회귀는 연속적인 값 실수를 찾아내는 모델입니다."
    ]
    
    print("가상 사용자 답변 전송 중...")
    final_result = graph.invoke(
        Command(resume={"user_answers": mock_user_answers}),
        config=config
    )
    
    print("\n=== 최종 실행 결과 스냅샷 ===")
    print(f"퀴즈 최종 점수: {final_result.get('score')}점")
    print(f"평가 리포트:\n{final_result.get('evaluation_report')}")
    print(f"최종 힌트: {final_result.get('hint', '없음 (성공)')}")

if __name__ == "__main__":
    # 1. 개별 노드 단위 테스트 실행
    extracted_concepts = test_parse_material_node()
    test_generate_flashcards_node(extracted_concepts)
    
    # 2. 통합 최초 실행 테스트
    session_config = run_integration_test()
    
    # 3. 통합 재개(resume) 테스트 실행
    run_resume_test(session_config)
