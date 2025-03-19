import time
from typing import Any, Dict, Optional

from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig
from langgraph.config import get_stream_writer
from openai.types.responses.response_computer_tool_call import ResponseComputerToolCall
from scrapybara.types import ComputerResponse, InstanceGetStreamUrlResponse

from ..types import ComputerCallOutput, CUAState
from ..utils import init_or_load, is_computer_tool_call


def take_computer_action(state: CUAState, config: RunnableConfig) -> Dict[str, Any]:
    """
    Executes computer actions based on the tool call in the last message.

    Args:
        state: The current state of the CUA agent.
        config: The runnable configuration.

    Returns:
        A dictionary with updated state information.
    """
    message: AnyMessage = state.get("messages", [])[-1]
    assert message.type == "ai", "Last message must be an AI message"
    tool_outputs = message.additional_kwargs.get("tool_outputs")

    if not is_computer_tool_call(tool_outputs):
        # This should never happen, but include the check for proper type safety.
        raise ValueError("Cannot take computer action without a computer call in the last message.")

    # Cast tool_outputs as list[ResponseComputerToolCall] since is_computer_tool_call is true
    tool_outputs: list[ResponseComputerToolCall] = tool_outputs

    instance = init_or_load(state, config)

    stream_url: Optional[str] = state.get("stream_url")
    if not stream_url:
        # If the stream_url is not yet defined in state, fetch it, then write to the custom stream
        # so that it's made accessible to the client (or whatever is reading the stream) before any actions are taken.
        stream_url_response: InstanceGetStreamUrlResponse = instance.get_stream_url()
        stream_url = stream_url_response.stream_url

        writer = get_stream_writer()
        writer({"stream_url": stream_url})

    action = tool_outputs[0].get("action")
    computer_call_output: Optional[ComputerCallOutput] = None

    try:
        computer_response: Optional[ComputerResponse] = None
        action_type = action.get("type")

        if action_type == "click":
            computer_response = instance.computer(
                action="click_mouse",
                button="middle" if action.get("button") == "wheel" else action.get("button"),
                coordinates=[action.get("x"), action.get("y")],
            )
        elif action_type == "double_click":
            computer_response = instance.computer(
                action="click_mouse",
                button="left",
                coordinates=[action.get("x"), action.get("y")],
                num_clicks=2,
            )
        elif action_type == "drag":
            computer_response = instance.computer(
                action="drag_mouse",
                path=[[point.get("x"), point.get("y")] for point in action.get("path")],
            )
        elif action_type == "keypress":
            computer_response = instance.computer(action="press_key", keys=action.get("keys"))
        elif action_type == "move":
            computer_response = instance.computer(
                action="move_mouse", coordinates=[action.get("x"), action.get("y")]
            )
        elif action_type == "screenshot":
            computer_response = instance.computer(action="take_screenshot")
        elif action_type == "wait":
            # Sleep for 2000ms (2 seconds)
            time.sleep(2)
        elif action_type == "scroll":
            computer_response = instance.computer(
                action="scroll",
                delta_x=action.get("scroll_x"),
                delta_y=action.get("scroll_y"),
                coordinates=[action.get("x"), action.get("y")],
            )
        elif action_type == "type":
            computer_response = instance.computer(action="type_text", text=action.get("text"))
        else:
            raise ValueError(f"Unknown computer action received: {action}")

        if computer_response:
            computer_call_output = {
                "call_id": tool_outputs[0].get("call_id"),
                "type": "computer_call_output",
                "output": {
                    "type": "computer_screenshot",
                    "image_url": f"data:image/png;base64,{computer_response.base_64_image}",
                },
            }
    except Exception as e:
        print(f"\n\nFailed to execute computer call: {e}\n\n")
        print(f"Computer call details: {tool_outputs[0]}\n\n")

    return {
        "computer_call_output": computer_call_output,
        "instance_id": instance.id,
        "stream_url": stream_url,
    }
