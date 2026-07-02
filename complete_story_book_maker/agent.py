from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.agent_tool import AgentTool
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from .prompt import PRODUCER_DESCRIPTION, PRODUCER_PROMPT
from .sub_agents.agent import pipeline_agent

MODEL = LiteLlm(model="openai/gpt-4o")

def before_producer_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):
    # 사용자가 스토리 주제를 입력하면 진행 상태를 세팅하여 UI/로그에 반영
    # callback_context.state["progress_status"] = "어린이 동화책 만들기 시작"
    # print(f"✅ 상태 업데이트: {callback_context.state['progress_status']}")
    return None

producer_agent = Agent(
    name="StoryBookProducerAgent",
    description=PRODUCER_DESCRIPTION,
    instruction=PRODUCER_PROMPT,
    model=MODEL,
    before_model_callback=before_producer_callback,
    tools=[
        AgentTool(agent=pipeline_agent)
    ]
)

root_agent = producer_agent
