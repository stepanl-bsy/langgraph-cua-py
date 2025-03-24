from typing import List, Literal

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage, HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, Field

from langgraph_cua import create_cua
from langgraph_cua.types import CUAState

# Load environment variables from .env file
load_dotenv()


# Create the CUA graph
cua_graph = create_cua()


class PriceFinderState(CUAState):
    route: Literal["respond", "computer_use_agent"]


def process_input(state: PriceFinderState):
    system_message = SystemMessage(
        content=(
            "You're an advanced AI assistant tasked with routing the user's query to the appropriate node."
            + "Your options are: computer use or respond. You should pick computer use if the user's request requires "
            + "using a computer (e.g. looking up a price on a website), and pick respond for ANY other inputs."
        )
    )

    class RoutingToolSchema(BaseModel):
        """Route the user's request to the appropriate node."""

        route: Literal["respond", "computer_use_agent"] = Field(
            ...,
            description="The node to route to, either 'computer_use_agent' for any input which might require using a computer to assist the user, or 'respond' for any other input",
        )

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    model_with_tools = model.with_structured_output(RoutingToolSchema)

    messages = [system_message, HumanMessage(content=state.messages[-1].content)]

    response = model_with_tools.invoke(messages)
    return {"route": response.route}


def respond(state: PriceFinderState):
    def format_messages(messages: List[AnyMessage]) -> str:
        return "\n".join([f"{message.type}: {message.content}" for message in messages])

    system_message = SystemMessage(
        content=(
            "You're an advanced AI assistant tasked with responding to the user's input."
            + "You're provided with the full conversation between the user, and the AI assistant. "
            + "This conversation may include messages from a computer use agent, along with "
            + "general user inputs and AI responses. \n\n"
            + "Given all of this, please RESPOND to the user. If there is nothing to respond to, you may return something like 'Let me know if you have any other questions.'"
        )
    )
    human_message = HumanMessage(
        content="Here are all of the messages in the conversation:\n\n"
        + format_messages(state.messages)
    )

    model = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    response = model.invoke([system_message, human_message])
    return {"response": response}


def route_after_processing_input(state: PriceFinderState):
    # Route to computer use or respond based on input
    return state.get("route")


workflow = StateGraph(PriceFinderState)
workflow.add_node("process_input", process_input)
workflow.add_node("respond", respond)
workflow.add_node("computer_use_agent", cua_graph)

workflow.add_edge(START, "process_input")
workflow.add_conditional_edges("process_input", route_after_processing_input)
workflow.add_edge("respond", END)
workflow.add_edge("computer_use_agent", END)

graph = workflow.compile()
graph.name = "Price Finder"


async def main():
    # Define the input messages
    messages = [
        SystemMessage(
            content=(
                "You're an advanced AI computer use assistant. The browser you are using "
                "is already initialized, and visiting google.com."
            )
        ),
        HumanMessage(
            content=(
                "Can you find the best price for new all season tires which will fit on my 2019 Subaru Forester?"
            )
        ),
    ]

    # Stream the graph execution
    stream = graph.astream({"messages": messages}, {"streamMode": "updates"})
    print("Stream started")
    # Process the stream updates
    async for update in stream:
        if "create_vm_instance" in update:
            print("VM instance created")
            stream_url = update.get("create_vm_instance", {}).get("stream_url")
            # Open this URL in your browser to view the CUA stream
            print(f"Stream URL: {stream_url}")

    print("Done")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
