from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types
import base64
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
