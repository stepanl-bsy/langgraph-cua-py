from typing import Any, Dict, Optional

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from openai.types.responses.response_computer_tool_call import ResponseComputerToolCall
from scrapybara.types import ComputerResponse, InstanceGetStreamUrlResponse

from ..types import ComputerCallOutput, CUAState
from ..utils import ainit_or_load, is_computer_tool_call


async def take_computer_action(state: CUAState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Executes computer actions based on the tool call in the last message.

    Args:
        state: The current state of the CUA agent.
        config: The runnable configuration.

    Returns:
        A dictionary with updated state information.
    """
    message: AnyMessage = state.messages[-1]
    assert message.type == "ai", "Last message must be an AI message"
    tool_outputs = message.additional_kwargs.get("tool_outputs")

    if not is_computer_tool_call(tool_outputs):
        # This should never happen, but include the check for proper type safety.
        raise ValueError("Cannot take computer action without a computer call in the last message.")

    # Cast tool_outputs as list[ResponseComputerToolCall] since is_computer_tool_call is true
    tool_outputs: list[ResponseComputerToolCall] = tool_outputs

    instance = await ainit_or_load(state, config)

    stream_url: Optional[str] = state.stream_url
    if not stream_url:
        # If the stream_url is not yet defined in state, fetch it, then write to the custom stream
        # so that it's made accessible to the client (or whatever is reading the stream) before any actions are taken.
        stream_url_response: InstanceGetStreamUrlResponse = await instance.get_stream_url()
        stream_url = stream_url_response.stream_url

        writer = get_stream_writer()
        writer({"stream_url": stream_url})

    action = tool_outputs[0].action
    computer_call_output: Optional[ComputerCallOutput] = None

    try:
        computer_response: Optional[ComputerResponse] = None
        action_type = action.type

        if action_type == "click":
            computer_response = await instance.computer(
                {
                    "action": "click_mouse",
                    "button": "middle" if action.button == "wheel" else action.button,
                    "coordinates": [action.x, action.y],
                }
            )
        elif action_type == "double_click":
            computer_response = await instance.computer(
                {
                    "action": "click_mouse",
                    "button": "left",
                    "coordinates": [action.x, action.y],
                    "num_clicks": 2,
                }
            )
        elif action_type == "drag":
            computer_response = await instance.computer(
                {"action": "drag_mouse", "path": [[point.x, point.y] for point in action.path]}
            )
        elif action_type == "keypress":
            computer_response = await instance.computer(
                {"action": "press_key", "keys": action.keys}
            )
        elif action_type == "move":
            computer_response = await instance.computer(
                {"action": "move_mouse", "coordinates": [action.x, action.y]}
            )
        elif action_type == "screenshot":
            computer_response = await instance.computer({"action": "take_screenshot"})
        elif action_type == "wait":
            computer_response = await instance.computer(
                {
                    "action": "wait",
                    # Default timeout of 2000ms (2 seconds)
                    "duration": 2000,
                }
            )
        elif action_type == "scroll":
            computer_response = await instance.computer(
                {
                    "action": "scroll",
                    "delta_x": action.scroll_x,
                    "delta_y": action.scroll_y,
                    "coordinates": [action.x, action.y],
                }
            )
        elif action_type == "type":
            computer_response = await instance.computer(
                {"action": "type_text", "text": action.text}
            )
        else:
            raise ValueError(f"Unknown computer action received: {action}")

        if computer_response:
            computer_call_output = {
                "call_id": tool_outputs[0].call_id,
                "type": "computer_call_output",
                "output": {
                    "type": "computer_screenshot",
                    "image_url": f"data:image/png;base64,{computer_response.base_64_image}",
                },
            }
    except Exception as e:
        print(f"Failed to execute computer call: {e}")
        print(f"Computer call details: {tool_outputs[0]}")

    return {
        "computer_call_output": computer_call_output,
        "instance_id": instance.id,
        "stream_url": stream_url,
    }
