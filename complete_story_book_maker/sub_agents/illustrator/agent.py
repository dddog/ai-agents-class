from google.adk.agents import Agent, ParallelAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from .prompt import ILLUSTRATOR_DESCRIPTION, ILLUSTRATOR_PROMPT
from .tools import generate_page_illustration

MODEL = LiteLlm(model="openai/gpt-4o")

# 콜백 빌더 함수 (클로저 바인딩)
def make_before_callback(page_num: int):
    def callback(callback_context: CallbackContext, llm_request: LlmRequest):
        callback_context.state["progress_status"] = f"이미지 {page_num}/5 생성 중..."
        print(f"⏳ [진행상황] {callback_context.state['progress_status']}")
        return None
    return callback

def make_after_callback(page_num: int):
    def callback(callback_context: CallbackContext, llm_response: LlmResponse):
        callback_context.state["progress_status"] = f"이미지 {page_num}/5 생성 완료"
        print(f"✅ [진행상황] {callback_context.state['progress_status']}")
        return llm_response
    return callback

# 개별 에이전트의 지시문 빌더
def make_illustrator_instruction(page_num: int) -> str:
    return (
        f"{ILLUSTRATOR_PROMPT}\n\n"
        f"당신은 현재 동화책의 **{page_num}페이지** 삽화 생성을 전담하고 있습니다.\n"
        f"반드시 `generate_page_illustration` 도구를 호출할 때 `page_number` 아규먼트에 값 **{page_num}**을 전달하여 실행하십시오."
    )

# 5개의 일러스트 에이전트 인스턴스 생성 (단일 툴 공유 방식)
illustrator_page1 = Agent(
    name="IllustratorAgent_Page1",
    description="1페이지 동화 삽화를 생성합니다.",
    instruction=make_illustrator_instruction(1),
    model=MODEL,
    tools=[generate_page_illustration],
    before_model_callback=make_before_callback(1),
    after_model_callback=make_after_callback(1),
)

illustrator_page2 = Agent(
    name="IllustratorAgent_Page2",
    description="2페이지 동화 삽화를 생성합니다.",
    instruction=make_illustrator_instruction(2),
    model=MODEL,
    tools=[generate_page_illustration],
    before_model_callback=make_before_callback(2),
    after_model_callback=make_after_callback(2),
)

illustrator_page3 = Agent(
    name="IllustratorAgent_Page3",
    description="3페이지 동화 삽화를 생성합니다.",
    instruction=make_illustrator_instruction(3),
    model=MODEL,
    tools=[generate_page_illustration],
    before_model_callback=make_before_callback(3),
    after_model_callback=make_after_callback(3),
)

illustrator_page4 = Agent(
    name="IllustratorAgent_Page4",
    description="4페이지 동화 삽화를 생성합니다.",
    instruction=make_illustrator_instruction(4),
    model=MODEL,
    tools=[generate_page_illustration],
    before_model_callback=make_before_callback(4),
    after_model_callback=make_after_callback(4),
)

illustrator_page5 = Agent(
    name="IllustratorAgent_Page5",
    description="5페이지 동화 삽화를 생성합니다.",
    instruction=make_illustrator_instruction(5),
    model=MODEL,
    tools=[generate_page_illustration],
    before_model_callback=make_before_callback(5),
    after_model_callback=make_after_callback(5),
)

# ParallelAgent로 에이전트 병렬화
parallel_illustrator_agent = ParallelAgent(
    name="ParallelIllustratorAgent",
    description=ILLUSTRATOR_DESCRIPTION,
    sub_agents=[
        illustrator_page1,
        illustrator_page2,
        illustrator_page3,
        illustrator_page4,
        illustrator_page5,
    ],
)
