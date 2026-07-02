from pydantic import BaseModel, Field
from typing import List
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from .prompt import STORY_WRITER_DESCRIPTION, STORY_WRITER_PROMPT

class PageInfo(BaseModel):
    page_number: int = Field(description="페이지 번호 (1부터 5까지)")
    text: str = Field(description="해당 페이지에 들어갈 동화 내용 텍스트")
    visual_description: str = Field(description="해당 페이지 그림 생성을 위한 구체적인 시각 묘사")

class StoryBookPlan(BaseModel):
    characters_description: str = Field(description="일관된 캐릭터 유지를 위한 주인공 외형의 구체적 묘사")
    pages: List[PageInfo] = Field(description="정확히 5개의 페이지 정보 배열")

MODEL = LiteLlm(model="openai/gpt-4o")

def before_story_writer_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):
    callback_context.state["progress_status"] = "스토리 작성 중..."
    
    print(f"✅ 상태 업데이트: {callback_context.state['progress_status']}")
    return None

def after_story_writer_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
):
    callback_context.state["progress_status"] = "스토리 작성 완료"
    print(f"✅ 상태 업데이트: {callback_context.state['progress_status']}")
    # 텍스트 치환 제거: 순수 JSON을 반환하게 두어 ADK가 output_schema(StoryBookPlan)로 자동 파싱하도록 위임.
    return llm_response

story_writer_agent = Agent(
    name="StoryWriterAgent",
    description=STORY_WRITER_DESCRIPTION,
    instruction=STORY_WRITER_PROMPT,
    model=MODEL,
    output_schema=StoryBookPlan,
    output_key="story_writer_output",
    before_model_callback=before_story_writer_callback,
    after_model_callback=after_story_writer_callback,
)
