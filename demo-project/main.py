from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver

# 1. State 정의
class State(TypedDict):
    learning_material: str
    concepts: List[str]
    flashcards: List[Dict[str, str]]
    user_answers: List[str]
    evaluation_report: str

# 2. 노드 정의
def parse_material(state: State) -> Dict[str, Any]:
    print("--- [Node] parse_material ---")
    material = state.get("learning_material", "")
    concepts = [f"Concept: {line.strip()}" for line in material.split("\n") if line.strip()]
    return {"concepts": concepts}

def generate_flashcards(state: State) -> Dict[str, Any]:
    print("--- [Node] generate_flashcards ---")
    concepts = state.get("concepts", [])
    flashcards = []
    for i, concept in enumerate(concepts):
        flashcards.append({
            "id": i + 1,
            "question": f"What is the definition of '{concept}'?",
            "answer": f"This is the description for '{concept}'."
        })
    return {"flashcards": flashcards}

def quiz_interrupt(state: State) -> Dict[str, Any]:
    print("--- [Node] quiz_interrupt ---")
    flashcards = state.get("flashcards", [])
    answer = interrupt({
        "questions": [card["question"] for card in flashcards],
        "instruction": "Please provide answers to the questions in 'user_answers'."
    })
    return {
        "user_answers": answer.get("user_answers", [])
    }

def grade_quiz(state: State) -> Dict[str, Any]:
    print("--- [Node] grade_quiz ---")
    flashcards = state.get("flashcards", [])
    user_answers = state.get("user_answers", [])
    
    report = "### Quiz Evaluation Report\n"
    for i, card in enumerate(flashcards):
        u_ans = user_answers[i] if i < len(user_answers) else "No Answer"
        report += f"\nQ{card['id']}: {card['question']}\n- Your Answer: {u_ans}\n- Correct Answer: {card['answer']}\n"
    
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

if __name__ == "__main__":
    # 로컬 테스트 실행 코드 예시
    config = {"configurable": {"thread_id": "demo_session"}}
    
    # 1단계: 학습 데이터 주입 및 interrupt 발생 지점까지 실행
    initial_state = {"learning_material": "Supervised Learning\nUnsupervised Learning\nReinforcement Learning"}
    print("Starting graph execution...")
    result = graph.invoke(initial_state, config=config)
    
    # interrupt 대기 상태
    print("Interrupted. Current State:", result)
