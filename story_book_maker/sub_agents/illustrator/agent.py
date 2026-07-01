from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_response import LlmResponse
from google.genai import types
import base64
from .prompt import ILLUSTRATOR_DESCRIPTION, ILLUSTRATOR_PROMPT
from .tools import generate_illustrations, combine_story_book

MODEL = LiteLlm(model="openai/gpt-4o")

async def inject_image(callback_context: CallbackContext, llm_response: LlmResponse) -> LlmResponse:
    last_base64 = callback_context.state.get("last_image_base64")
    if last_base64 and llm_response.content and llm_response.content.parts:
        image_bytes = base64.b64decode(last_base64)
        image_part = types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes))
        llm_response.content.parts.append(image_part)
        callback_context.state["last_image_base64"] = None
    return llm_response

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
    after_model_callback=inject_image,
)
