import datetime, uuid
from zoneinfo import ZoneInfo
from .sub_agents.decision import decision_prompt_agent
from .sub_agents.image import image_renderer_agent
from google.adk.agents import SequentialAgent, LlmAgent
from google.adk.agents.callback_context import CallbackContext
from .config import *


def set_session(callback_context: CallbackContext):
    """
    Sets a unique ID and timestamp in the callback context's state.
    This function is called before the main_loop_agent executes.
    """

    callback_context.state["unique_id"] = str(uuid.uuid4())
    callback_context.state["timestamp"] = datetime.datetime.now(
        ZoneInfo("UTC")
    ).isoformat()


# This agent is responsible for generating and scoring images based on input text.
# It uses a sequential process to:
# 1. Create an image generation prompt from the input text
# 2. Generate images using the prompt
# 3. Score the generated images
# The process continues until either:
# - The image score meets the quality threshold
# - The maximum number of iterations is reached

image_renderer_agent = SequentialAgent(
    name="image_renderer_agent",
    description=(
        """
        You are expert in generating inages, editing existing images and answering questions on images
        
        You will choose the best model and identify the intent for Image generation or edit based on the Users requirement."
        1. Invoke the image_generation_prompt_agent agent to generate the prompt for generating images
        2. Invoke the image_generation_agent agent to generate the images

            """
    ),
    sub_agents=[decision_prompt_agent, image_renderer_agent],
)


root_agent = LlmAgent(
    name="image_renderer_root_agent",
    model=GENAI_MODEL,
    instruction="""
    You are a friendly and helpful Image Renderer agent.

    1.  When the user starts a conversation with a greeting like "hi" or "hello", respond with a warm welcome.
    2.  Introduce yourself and explain your capabilities. You can:
        - Generate images from a text description.
        - Edit existing images based on instructions.
        - Answer questions about an image (Live Q&A).
        - Customize the style or subject of an image.
    3.  After your introduction, ask the user "How can I help you today?".
    4.  Wait for the user's response. **Do not** transfer to the `image_renderer_agent` agent for simple conversation.
    5.  Only when the user provides a clear prompt to generate, edit, or analyze an image, you should then delegate the task to the `image_scoring` agent to handle the request.
    """,
    sub_agents=[image_renderer_agent],
    before_agent_callback=set_session,
)
