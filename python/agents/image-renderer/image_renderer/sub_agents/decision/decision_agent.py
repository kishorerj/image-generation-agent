from ... import config
from google.adk.agents import Agent
from .prompt import DECISION_PROMPT
from google.adk.tools import ToolContext, LongRunningFunctionTool


decision_prompt_agent = Agent(
    name="decision_prompt_agent",
    model=config.GENAI_MODEL,
    description=(
        "You are an expert in deciding the suitable model and intent for image generation"
    ),
    instruction=(DECISION_PROMPT),
    tools=[],
    output_key="imagen_prompt",
)
