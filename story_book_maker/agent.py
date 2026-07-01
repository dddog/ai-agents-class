from google.genai import types
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
import base64
from .sub_agents.agent import generator_agent
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
            f"사용자의 입력: '{text}'\n\n"
            f"이 내용이 성인물, 잔혹성, 폭력, 욕설 등 어린이에게 명백히 유해한 내용(NSFW)인지 판별하십시오. "
            f"단순한 문장, 잡담, 상황 묘사 등 유해하지 않은 모든 평범한 입력은 무조건 'PASS'라고 대답하십시오. "
            f"오직 어린이에게 명백하게 유해한 악의적 콘텐츠인 경우에만 'BLOCK'이라고 대답하십시오. "
            f"설명 없이 오직 'PASS' 또는 'BLOCK' 단어 한 개로만 답변하십시오."
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
        AgentTool(agent=generator_agent),
    ],
    before_model_callback=before_model_callback,
)

root_agent = story_book_producer_agent
