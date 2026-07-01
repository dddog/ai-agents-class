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


MODEL = LiteLlm(model="openai/gpt-4o")

story_writer_agent = Agent(
    name="StoryWriterAgent",
    description=STORY_WRITER_DESCRIPTION,
    instruction=STORY_WRITER_PROMPT,
    model=MODEL,
    output_schema=PagePlan,
    output_key="story_writer_output",
)
