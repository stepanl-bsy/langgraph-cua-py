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
        if isinstance(update, list):
            if update[0] == "custom":
                print("\n---CUSTOM---\n")
                print(update[1])
            else:
                print("\n---UPDATE---\n")
                if "call_model" in update[1]:
                    messages = update[1]["call_model"].get("messages")
                    if messages:
                        print(
                            {
                                "additional_kwargs": getattr(messages, "additional_kwargs", None),
                                "content": getattr(messages, "content", None),
                            }
                        )
                elif "take_computer_action" in update[1]:
                    computer_call_output = update[1]["take_computer_action"].get(
                        "computer_call_output"
                    )
                    if computer_call_output:
                        # Truncate image_url to avoid excessive output
                        output = computer_call_output.get("output", {})
                        image_url = output.get("image_url", "")
                        truncated_output = {
                            **output,
                            "image_url": image_url[:100] if image_url else None,
                        }

                        print(
                            {
                                "computer_call_output": {
                                    **computer_call_output,
                                    "output": truncated_output,
                                }
                            }
                        )
                else:
                    print(update[1])
        else:
            print("\n---UPDATE (not array)---\n")
            print(update)
