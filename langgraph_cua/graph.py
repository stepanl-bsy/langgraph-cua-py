from langgraph.graph import END, START, StateGraph

from langgraph_cua.nodes import call_model, take_computer_action
from langgraph_cua.types import CUAState
from langgraph_cua.utils import is_computer_tool_call


def take_action_or_end(state: CUAState):
    """
    Routes to the take_computer_action node if a computer call is present
    in the last message, otherwise routes to END.

    Args:
        state: The current state of the thread.

    Returns:
        "take_computer_action" or END depending on if a computer call is present.
    """
    if not state.messages:
        return END

    last_message = state.messages[-1]
    additional_kwargs = getattr(last_message, "additional_kwargs", None)

    if not additional_kwargs:
        return END

    tool_outputs = additional_kwargs.get("tool_outputs")

    if not is_computer_tool_call(tool_outputs):
        return END

    return "take_computer_action"


def reinvoke_model_or_end(state: CUAState):
    """
    Routes to the call_model node if a computer call output is present,
    otherwise routes to END.

    Args:
        state: The current state of the thread.

    Returns:
        "call_model" or END depending on if a computer call output is present.
    """
    if state.computer_call_output:
        return "call_model"

    return END


workflow = StateGraph(CUAState)

workflow.add_node("call_model", call_model)
workflow.add_node("take_computer_action", take_computer_action)

workflow.add_edge(START, "call_model")
workflow.add_conditional_edges("call_model", take_action_or_end)
workflow.add_conditional_edges("take_computer_action", reinvoke_model_or_end)

graph = workflow.compile()
graph.name = "Computer Use Agent"


# TODO: What else do I need to do to this to match the other create functions?
def create_cua():
    return graph


__all__ = ["create_cua", graph]
