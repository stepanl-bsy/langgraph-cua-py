import pytest
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, SystemMessage

from langgraph_cua import create_cua

# Load environment variables from .env file
load_dotenv()


@pytest.mark.asyncio
async def test_browser_interaction():
    """
    Test that the agent can interact with the browser.
    This is a port of the TypeScript test to Python.
    """
    graph = create_cua()

    # Create input messages similar to the TypeScript test
    messages = [
        SystemMessage(
            content=(
                "You're an advanced AI computer use assistant. The browser you are using "
                "is already initialized, and visiting google.com."
            )
        ),
        HumanMessage(
            content=(
                "I'm looking for a new camera. Help me find the best one. It should be 4k resolution, "
                "by Cannon, and under $1000. I want a digital camera, and I'll be using it mainly for photography."
            )
        ),
    ]

    # Stream the graph execution
    stream = graph.astream({"messages": messages}, {"streamMode": ["custom", "updates"]})

    # Process the stream updates
    async for update in stream:
        print("\n---UPDATE---\n")

        if "take_computer_action" in update:
            print("Computer Action:")
            if update.get("take_computer_action", {}).get("computer_call_output"):
                output_dict = update["take_computer_action"]["computer_call_output"]
                # Handle image_url specially - truncate to 100 chars
                if output_dict.get("output", {}).get("image_url"):
                    image_url = output_dict["output"]["image_url"]
                    output_dict["output"]["image_url"] = (
                        image_url[:100] + "..." if len(image_url) > 100 else image_url
                    )
                print(output_dict)
        elif "call_model" in update:
            print("Model Call:")
            if update.get("call_model", {}).get("messages"):
                print(update["call_model"]["messages"].additional_kwargs["tool_outputs"])
        else:
            print(update)
