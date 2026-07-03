from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from .prompt import BOOK_ASSEMBLER_DESCRIPTION, BOOK_ASSEMBLER_PROMPT
from .tools import assemble_story_book_pdf

MODEL = LiteLlm(model="openai/gpt-4o")

def before_assembler_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):
    callback_context.state["progress_status"] = "동화책 조립 및 PDF 변환 중..."
    print(f"⏳ [진행상황] {callback_context.state['progress_status']}")
    return None

def after_assembler_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
):
    if callback_context.state.get("progress_status") == "동화책 완성!":
        return llm_response
    callback_context.state["progress_status"] = "동화책 완성!"
    print(f"✅ [진행상황] {callback_context.state['progress_status']}")
    return llm_response

book_assembler_agent = Agent(
    name="BookAssemblerAgent",
    description=BOOK_ASSEMBLER_DESCRIPTION,
    instruction=BOOK_ASSEMBLER_PROMPT,
    model=MODEL,
    tools=[assemble_story_book_pdf],
    before_model_callback=before_assembler_callback,
    after_model_callback=after_assembler_callback,
)
