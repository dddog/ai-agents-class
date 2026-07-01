from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from .prompt import ILLUSTRATOR_DESCRIPTION, ILLUSTRATOR_PROMPT
from .tools import generate_illustrations, combine_story_book

MODEL = LiteLlm(model="openai/gpt-4o")

illustrator_agent = Agent(
    name="IllustratorAgent",
    description=ILLUSTRATOR_DESCRIPTION,
    instruction=ILLUSTRATOR_PROMPT,
    model=MODEL,
    tools=[
        generate_illustrations,
        combine_story_book,
    ],
    output_key="illustrator_output",
)
