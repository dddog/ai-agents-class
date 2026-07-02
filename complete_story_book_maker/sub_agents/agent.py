from google.adk.agents import SequentialAgent
from .story_writer.agent import story_writer_agent
from .illustrator.agent import parallel_illustrator_agent

pipeline_agent = SequentialAgent(
    name="StoryBookPipelineAgent",
    description="스토리 작성, 병렬 일러스트 생성, 최종 병합을 순차적으로 관리하는 파이프라인 에이전트입니다.",
    sub_agents=[
        story_writer_agent,
        parallel_illustrator_agent,
    ],
)
