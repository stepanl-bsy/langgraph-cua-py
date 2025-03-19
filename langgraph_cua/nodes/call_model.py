from typing import Any, Dict, Optional

from langchain_core.messages import AIMessageChunk
from langchain_openai import ChatOpenAI

from ..types import CUAEnvironment, CUAState


def get_openai_env_from_state_env(env: CUAEnvironment) -> str:
    """
    Converts CUAEnvironment to OpenAI environment string.

    Args:
        env: The CUAEnvironment to convert.

    Returns:
        The corresponding OpenAI environment string.

    Raises:
        ValueError: If the environment is invalid.
    """
    if env == CUAEnvironment.WEB:
        return "browser"
    elif env == CUAEnvironment.UBUNTU:
        return "ubuntu"
    elif env == CUAEnvironment.WINDOWS:
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

    model = ChatOpenAI(model="computer-use-preview", use_responses_api=True)

    model = model.bind_tools(
        [
            {
                "type": "computer-preview",
                "display_width": DEFAULT_DISPLAY_WIDTH,
                "display_height": DEFAULT_DISPLAY_HEIGHT,
                "environment": get_openai_env_from_state_env(state.get("environment")),
            }
        ]
    )

    model = model.bind(
        {
            "truncation": "auto",
            "previous_response_id": previous_response_id,
        }
    )

    response: AIMessageChunk
    if state.get("computer_call_output"):
        # TODO: How to pass back computer call outputs?
        response = await model.ainvoke([state.get("computer_call_output")])
    else:
        response = await model.ainvoke(state.get("messages", []))

    return {
        "messages": response,
    }
