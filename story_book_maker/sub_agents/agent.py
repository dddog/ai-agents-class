from google.adk.agents import SequentialAgent
from .story_writer.agent import story_writer_agent
from .illustrator.agent import illustrator_agent

generator_agent = SequentialAgent(
    name="GeneratorAgent",
    description="동화 스토리를 기획하고 이에 알맞은 일러스트를 연달아 순차적으로 생성하는 직렬(Pipeline) 에이전트입니다.",
    sub_agents=[
        story_writer_agent,
        illustrator_agent,
    ],
)
