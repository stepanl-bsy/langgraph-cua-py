from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from langgraph_cua import create_cua
from langgraph_cua.types import CUAState

# Load environment variables from .env file
load_dotenv()


# Create the CUA graph
cua_graph = create_cua()


class PriceFinderState(CUAState):
    pass


def process_input(state: PriceFinderState):
    # Take user's input. if they want to get the price of something, route to computer use
    # else, route to respond
    pass


def respond(state: PriceFinderState):
    # pass in full message history, reply to user
    pass


def route_after_processing_input(state: PriceFinderState):
    # Route to computer use or respond based on input
    pass


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
