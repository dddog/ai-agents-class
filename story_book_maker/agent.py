from google.genai import types
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from .sub_agents.story_writer.agent import story_writer_agent
from .sub_agents.illustrator.agent import illustrator_agent
from .prompt import STORY_BOOK_PRODUCER_DESCRIPTION, STORY_BOOK_PRODUCER_PROMPT

MODEL = LiteLlm(model="openai/gpt-4o")


def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):
    """사용자 입력이 동화책 만들기와 무관하거나 어린이에게 부적절한지 판별하여 사전에 차단합니다."""
    history = llm_request.contents
    if not history:
        return None

    last_message = history[-1]
    if last_message.role == "user":
        text = last_message.parts[0].text

        validation_prompt = (
            f"다음은 어린이 동화책 제작 에이전트에 들어온 사용자의 요청입니다:\n"
            f"'{text}'\n\n"
            f"이 요청이 동화책의 테마 제안, 스토리 내용 추가 등 동화책 제작 목적에 적합한 내용인지 판단하십시오. "
            f"만약 '오늘 날씨 어때?' 같은 일상 잡담, 동화책과 전혀 무관한 무의미한 질문, 혹은 "
            f"어린이에게 부적절한 내용(성인물, 잔혹성, 폭력, 15세 이상 연령가 수준 등)이라면 반드시 'BLOCK'이라고 대답하고, "
            f"동화책 제작에 적합한 어린이 친화적 이야기라면 'PASS'라고 대답하십시오. "
            f"추가 설명이나 부연 없이 오직 'PASS' 또는 'BLOCK' 단어 한 개로만 답변하십시오."
        )

        try:
            import openai
            client = openai.OpenAI()
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": validation_prompt}],
                max_tokens=10,
            )
            decision = response.choices[0].message.content.strip().upper()
            if "BLOCK" in decision:
                return LlmResponse(
                    content=types.Content(
                        parts=[
                            types.Part(
                                text="죄송합니다. 어린이 동화책 만들기에 적절하지 않은 요청이거나 무관한 질문은 처리할 수 없습니다. 동화책을 만들기 위한 알맞은 테마나 내용을 입력해 주세요."
                            )
                        ],
                        role="model",
                    )
                )
        except Exception as e:
            print(f"⚠️ 안전 필터링 실행 중 예외 발생: {e}")

    return None


story_book_producer_agent = Agent(
    name="StoryBookProducerAgent",
    model=MODEL,
    description=STORY_BOOK_PRODUCER_DESCRIPTION,
    instruction=STORY_BOOK_PRODUCER_PROMPT,
    tools=[
        AgentTool(agent=story_writer_agent),
        AgentTool(agent=illustrator_agent),
    ],
    before_model_callback=before_model_callback,
)

root_agent = story_book_producer_agent
