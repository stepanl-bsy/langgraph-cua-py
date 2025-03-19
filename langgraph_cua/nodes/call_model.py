from typing import Any, Dict, Optional

from langchain_core.messages import AIMessageChunk, ToolMessage
from langchain_openai import ChatOpenAI

from ..types import CUAState


def get_openai_env_from_state_env(env: str) -> str:
    """
    Converts one of "web", "ubuntu", or "windows" to OpenAI environment string.

    Args:
        env: The environment to convert.

    Returns:
        The corresponding OpenAI environment string.

    Raises:
        ValueError: If the environment is invalid.
    """
    if env == "web":
        return "browser"
    elif env == "ubuntu":
        return "ubuntu"
    elif env == "windows":
        return "windows"


# Scrapybara does not allow for configuring this. Must use a hardcoded value.
DEFAULT_DISPLAY_WIDTH = 1024
DEFAULT_DISPLAY_HEIGHT = 768


async def call_model(state: CUAState) -> Dict[str, Any]:
    """
    Invokes the computer preview model with the given messages.

    Args:
        state: The current state of the thread.

    Returns:
        The updated state with the model's response.
    """
    last_message = state.get("messages", [])[-1] if state.get("messages", []) else None
    previous_response_id: Optional[str] = None

    if (
        last_message
        and getattr(last_message, "type", None) == "ai"
        and hasattr(last_message, "response_metadata")
    ):
        previous_response_id = last_message.response_metadata["id"]

    llm = ChatOpenAI(
        model="computer-use-preview",
        model_kwargs={"truncation": "auto", "previous_response_id": previous_response_id},
    )

    tool = {
        "type": "computer_use_preview",
        "display_width": DEFAULT_DISPLAY_WIDTH,
        "display_height": DEFAULT_DISPLAY_HEIGHT,
        "environment": get_openai_env_from_state_env(state.get("environment", "web")),
    }
    llm_with_tools = llm.bind_tools([tool])

    response: AIMessageChunk
    if state.get("computer_call_output"):
        tool_msg = ToolMessage(
            content=state.get("computer_call_output").get("output"),
            tool_call_id=state.get("computer_call_output").get("call_id"),
        )
        # TODO: How to pass back computer call outputs?
        response = await llm_with_tools.ainvoke([tool_msg])
    else:
        response = await llm_with_tools.ainvoke(state.get("messages", []))

    return {
        "messages": response,
    }
