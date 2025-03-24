from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_cua import create_cua

# Load environment variables from .env file
load_dotenv()


cua_graph = create_cua()

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
            "I want to contribute to the LangGraph.js project. Please find the GitHub repository, and inspect the read me, "
            "along with some of the issues and open pull requests. Then, report back with a plan of action to contribute."
        )
    ),
]


async def main():
    # Stream the graph execution
    stream = cua_graph.astream({"messages": messages}, {"streamMode": "updates"})

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
