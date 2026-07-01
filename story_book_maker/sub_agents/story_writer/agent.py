from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import STORY_WRITER_DESCRIPTION, STORY_WRITER_PROMPT
from pydantic import BaseModel, Field


class PagePlan(BaseModel):
    page_number: int = Field(description="현재 작성 중인 동화책의 페이지 번호 (1에서 5 사이)")
    text: str = Field(description="해당 페이지에 인쇄될 최종 동화 텍스트 문장")
    visual_description: str = Field(
        description="해당 페이지의 그림(일러스트) 생성을 위한 시각적 설명. 짱구는 못말려 스타일로 그리기 좋게 묘사합니다."
    )
    character_description: str = Field(
        description="동화책 전반에 걸쳐 주인공 캐릭터의 외모(크기, 색상, 고유 특징)가 달라지지 않도록 보장하기 위한 고정 캐릭터 상세 묘사"
    )


from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.adk.models.llm_request import LlmRequest
from google.genai import types
import json
import re


MODEL = LiteLlm(model="openai/gpt-4o")


async def format_story_output(
    callback_context: CallbackContext, llm_response: LlmResponse
) -> LlmResponse:
    if llm_response.content and llm_response.content.parts:
        raw_text = llm_response.content.parts[0].text
        
        # JSON 블록만 정규식으로 추출 (마크다운 및 trailing 부연설명 무시)
        json_match = re.search(r"\{.*\}", raw_text, re.DOTALL)
        if json_match:
            clean_json_text = json_match.group(0)
            try:
                data = json.loads(clean_json_text)
                
                # ADK의 output_schema가 해주던 State 저장 역할을 여기서 수동으로 대신 수행
                callback_context.state["story_writer_output"] = data
                
                formatted_text = (
                    f"### 📖 동화책 페이지 생성 결과\n\n"
                    f"* **페이지 번호**: {data.get('page_number')}페이지\n"
                    f"* **동화 텍스트**: {data.get('text')}\n"
                    f"* **일러스트 묘사**: {data.get('visual_description')}\n"
                    f"* **캐릭터 묘사**: {data.get('character_description')}"
                )
                llm_response.content.parts[0].text = formatted_text
            except Exception as e:
                llm_response.content.parts.append(types.Part(text=f"\n[파싱 오류 발생: {e}]"))
    return llm_response


async def prepare_story_writer_input(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
):
    pages_data = callback_context.state.get("pages_data", {})
    if pages_data:
        try:
            existing_pages = [int(p) for p in pages_data.keys()]
            next_page = max(existing_pages) + 1
        except Exception:
            next_page = len(pages_data) + 1
    else:
        next_page = 1

    if next_page > 5:
        next_page = 5

    if llm_request.contents:
        last_message = llm_request.contents[-1]
        if last_message.role == "user" and last_message.parts:
            orig_text = last_message.parts[0].text
            augmented_text = (
                f"[입력 양식]\n"
                f"- 현재 작성해야 할 대상 페이지 번호: {next_page}\n"
                f"- 기존에 작성 완료된 페이지 데이터: {json.dumps(pages_data, ensure_ascii=False)}\n"
                f"- 사용자 입력 원문 줄거리: {orig_text}\n"
            )
            last_message.parts[0].text = augmented_text
    return None


story_writer_agent = Agent(
    name="StoryWriterAgent",
    description=STORY_WRITER_DESCRIPTION,
    instruction=STORY_WRITER_PROMPT,
    model=MODEL,
    before_model_callback=prepare_story_writer_input,
    after_model_callback=format_story_output,
)
