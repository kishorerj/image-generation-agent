from ... import config
from google.adk.agents import Agent
from .prompt import DECISION_PROMPT
from ..tools.fetch_policy_tool import get_policy
from google.adk.tools import ToolContext, LongRunningFunctionTool




# --- HITL Tool for failed command resolution (MODIFIED) ---
def get_human_input_for_model(
    tool_context: ToolContext,
    prompt_for_user: str
) -> dict[str, str]:
    """
   Signals that human input is pending to confirm the model for image generation.
    The ADK framework will handle the user interaction.
    This function itself only signals that the input is pending.
    Args:
       
        prompt_for_user: The message/question to display to the user (should include identified model name).
    Returns:
        A dictionary indicating that human input is pending. E.g. {'status': 'pending_human_input'}
    """
    print(f"HITL - Initiating request for confirming identified model for image generation. Prompt to be shown: {prompt_for_user}")
    details_for_prompt = {
        'identitied_model': prompt_for_user
    }
    tool_context.actions.transfer_to_agent
    return {'status': 'pending_human_input', 'input_needed': 'imagen_model_identification', 'details': prompt_for_user, 'context': details_for_prompt}

hitl_image_generation_decision_tool = LongRunningFunctionTool(
    func=get_human_input_for_model
)

decision_prompt_agent = Agent(
    name="image_generation_prompt_agent",
    model=config.GENAI_MODEL,
    description=("You are an expert in deciding the suitable model and intent for image generation"),
    instruction=(DECISION_PROMPT),
    tools=[],
    output_key="imagen_prompt",  # gets stored in session.state
)


