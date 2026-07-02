from google.adk.agents import SequentialAgent
from .story_writer.agent import story_writer_agent

# 추후 2단계, 3단계 구현 시 병렬 생성(Illustrator) 및 어셈블러 에이전트가 여기에 추가됩니다.
# 1단계 테스트를 위해 PipelineAgent에는 우선 story_writer_agent만 배치합니다.

pipeline_agent = SequentialAgent(
    name="StoryBookPipelineAgent",
    description="스토리 작성, 병렬 일러스트 생성, 최종 병합을 순차적으로 관리하는 파이프라인 에이전트입니다.",
    sub_agents=[
        story_writer_agent,
    ],
)
