from .prompt import IMAGEGEN_PROMPT
from google.adk.agents import Agent
from .tools.image_generation_tool import render_images


image_renderer_agent = Agent(
    name="image_renderer_agent",
    model="gemini-2.0-flash",
    description=(
        "You are an expert in creating, editing and answering questions on images." \
        "You can handle image_edition , style_customization, text_to_image, image_QA and subject_customization."
    ),
    instruction=(IMAGEGEN_PROMPT),
    tools=[render_images],
    output_key="output_image",
)
