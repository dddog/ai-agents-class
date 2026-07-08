from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver
from langchain.chat_models import init_chat_model

# 1. State 정의
class State(TypedDict):
    learning_material: str           # 학습자가 제공한 원본 학습용 텍스트 자료
    concepts: List[str]              # 원본 자료에서 추출한 핵심 개념/키워드 리스트
    flashcards: List[Dict[str, str]] # Q&A 쌍으로 구성된 플래시카드 객체 리스트
    user_answers: List[str]          # interrupt를 통해 수집된 사용자의 퀴즈 답변들
    evaluation_report: str           # 최종 채점 결과 및 피드백 보고서

# LLM 초기화 (한글 처리를 위해 OpenAI gpt-4o-mini 모델 활용)
llm = init_chat_model("openai:gpt-4o-mini")

# 2. 노드 정의
def parse_material(state: State) -> Dict[str, Any]:
    print("--- [노드] parse_material 실행 ---")
    material = state.get("learning_material", "")
    
    # 한글 프롬프트 설계
    prompt = f"""
    제공된 학습 자료에서 핵심적인 교육 개념이나 전문 용어를 추출해 주세요.
    각 개념은 불필요한 서술이나 번호, 불릿 기호 없이 한 줄에 하나씩 명확한 단어나 핵심 어구로만 추출해 주세요.
    
    학습 자료:
    {material}
    """
    
    response = llm.invoke(prompt)
    concepts = [line.strip() for line in response.content.split("\n") if line.strip()]
    return {"concepts": concepts}

def generate_flashcards(state: State) -> Dict[str, Any]:
    print("--- [노드] generate_flashcards 실행 ---")
    concepts = state.get("concepts", [])
    flashcards = []
    
    for i, concept in enumerate(concepts):
        # 3단계 고도화: 각 핵심 개념에 대한 쉬운 정의를 LLM을 사용하여 한국어로 동적 생성
        prompt = f"""
        학습용 플래시카드를 작성하고 있습니다. 다음 핵심 개념에 대한 쉽고 명확한 정의와 설명을 한국어로 작성해 주세요.
        답변은 1~2문장의 명확한 한국어 설명으로만 작성해 주세요.
        
        핵심 개념:
        {concept}
        """
        response = llm.invoke(prompt)
        
        # 한글 기반의 질문 생성
        flashcards.append({
            "id": i + 1,
            "question": f"'{concept}'의 개념과 정의는 무엇인가요?",
            "answer": response.content.strip()
        })
    return {"flashcards": flashcards}

def quiz_interrupt(state: State) -> Dict[str, Any]:
    print("--- [노드] quiz_interrupt 실행 (사용자 피드백 대기) ---")
    flashcards = state.get("flashcards", [])
    
    # 한글 안내 적용
    answer = interrupt({
        "questions": [card["question"] for card in flashcards],
        "instruction": "'user_answers' 키값에 각 질문에 대한 답변 목록을 담아 전송해 주세요."
    })
    return {
        "user_answers": answer.get("user_answers", [])
    }

def grade_quiz(state: State) -> Dict[str, Any]:
    print("--- [노드] grade_quiz 실행 ---")
    flashcards = state.get("flashcards", [])
    user_answers = state.get("user_answers", [])
    
    report = "### 퀴즈 평가 결과 보고서\n"
    for i, card in enumerate(flashcards):
        u_ans = user_answers[i] if i < len(user_answers) else "답변 없음"
        report += f"\n질문 {card['id']}: {card['question']}\n- 제출한 답변: {u_ans}\n- 모범 답안: {card['answer']}\n"
    
    return {"evaluation_report": report}

# 3. 그래프 연결 및 컴파일
graph_builder = StateGraph(State)

graph_builder.add_node("parse_material", parse_material)
graph_builder.add_node("generate_flashcards", generate_flashcards)
graph_builder.add_node("quiz_interrupt", quiz_interrupt)
graph_builder.add_node("grade_quiz", grade_quiz)

graph_builder.add_edge(START, "parse_material")
graph_builder.add_edge("parse_material", "generate_flashcards")
graph_builder.add_edge("generate_flashcards", "quiz_interrupt")
graph_builder.add_edge("quiz_interrupt", "grade_quiz")
graph_builder.add_edge("grade_quiz", END)

memory = InMemorySaver()
graph = graph_builder.compile(checkpointer=memory)

# 4. 개별 노드 단위 테스트 드라이버 함수 정의
def test_parse_material_node():
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
        "learning_material": material_data
    }
    output = parse_material(mock_state)
    print("\n--- 추출된 개념 결과 ---")
    concepts = output.get("concepts", [])
    for c in concepts:
        print(f"- {c}")
    assert len(concepts) > 0, "오류: 핵심 개념이 추출되지 않았습니다."
    print("\n>> 2단계 parse_material 단위 테스트 통과!")

def test_generate_flashcards_node():
    print("\n=============================================")
    print("[단위 테스트] 3단계: generate_flashcards 노드 검증")
    print("=============================================")
    mock_state = {
        "concepts": ["지도학습", "비지도학습"]
    }
    output = generate_flashcards(mock_state)
    print("\n--- 생성된 플래시카드 결과 ---")
    flashcards = output.get("flashcards", [])
    for card in flashcards:
        print(f"\n[카드 {card['id']}]")
        print(f"질문: {card['question']}")
        print(f"답변: {card['answer']}")
    assert len(flashcards) == len(mock_state["concepts"]), "오류: 개념 수와 플래시카드 수가 일치하지 않습니다."
    print("\n>> 3단계 generate_flashcards 단위 테스트 통과!")

def run_integration_test():
    import os
    print("\n=============================================")
    print("[통합 테스트] 4단계 진입 전까지 전체 흐름 실행")
    print("=============================================")
    config = {"configurable": {"thread_id": "demo_session_korean"}}
    
    file_path = os.path.join(os.path.dirname(__file__), "learning_material.txt")
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            material_data = f.read()
    else:
        material_data = "인공지능 머신러닝 지도학습 비지도학습"
        
    initial_state = {"learning_material": material_data}
    print("그래프 실행 시작...")
    result = graph.invoke(initial_state, config=config)
    print("\n인터럽트 중단 상태 도달. (퀴즈 답변 대기 중)")

if __name__ == "__main__":
    # 개별 노드 단위 테스트 실행
    test_parse_material_node()
    test_generate_flashcards_node()
    
    # 통합 테스트 실행 (인터럽트 지점까지)
    run_integration_test()
