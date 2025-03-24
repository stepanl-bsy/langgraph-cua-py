# 🤖 LangGraph Computer Use Agent (CUA)

> [!WARNING]
> **THIS REPO IS A WORK IN PROGRESS AND NOT INTENDED FOR USE YET**

A Python library for creating computer use agent (CUA) systems using [LangGraph](https://github.com/langchain-ai/langgraph). A CUA is a type of agent which has the ability to interact with a computer to preform tasks.

Short demo video:
<video src="https://github.com/user-attachments/assets/7fd0ab05-fecc-46f5-961b-6624cb254ac2" controls></video>

> [!TIP]
> This demo used the following prompt:
> ```
> I want to contribute to the LangGraph.js project. Please find the GitHub repository, and inspect the read me,
> along with some of the issues and open pull requests. Then, report back with a plan of action to contribute.
> ```

## Features

- **ADD FEATURES HERE**

This library is built on top of [LangGraph](https://github.com/langchain-ai/langgraph), a powerful framework for building agent applications, and comes with out-of-box support for [streaming](https://langchain-ai.github.io/langgraph/how-tos/#streaming), [short-term and long-term memory](https://langchain-ai.github.io/langgraph/concepts/memory/) and [human-in-the-loop](https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/).

## Installation

```bash
pip install langgraph-cua langgraph langchain-core langchain-openai
```

## Quickstart

This project by default uses [Scrapybara](https://scrapybara.com/) for accessing a virtual machine to run the agent. To use LangGraph CUA, you'll need both OpenAI and Scrapybara API keys.

```bash
export OPENAI_API_KEY=<your_api_key>
export SCRAPYBARA_API_KEY=<your_api_key>
```

Then, create the graph by importing the `create_cua` function from the `langgraph_cua` module.

```python
from langgraph_cua import create_cua

cua_graph = create_cua()
```

## How to customize

The `create_cua` function accepts a few configuration parameters. These are the same configuration parameters that the graph accepts, along with `recursion_limit`.

You can either pass these parameters when calling `create_cua`, or at runtime when invoking the graph by passing them to the `config` object.

### Configuration Parameters

- `scrapybara_api_key`: The API key to use for Scrapybara. If not provided, it defaults to reading the `SCRAPYBARA_API_KEY` environment variable.
- `timeout_hours`: The number of hours to keep the virtual machine running before it times out.
- `zdr_enabled`: Whether or not Zero Data Retention is enabled in the user's OpenAI account. If True, the agent will not pass the 'previous_response_id' to the model, and will always pass it the full message history for each request. If False, the agent will pass the 'previous_response_id' to the model, and only the latest message in the history will be passed. Default False.
- `recursion_limit`: The maximum number of recursive calls the agent can make. Default is 100. This is greater than the standard default of 25 in LangGraph, because computer use agents are expected to take more iterations.
- `auth_state_id`: The ID of the authentication state. If defined, it will be used to authenticate with Scrapybara. Only applies if 'environment' is set to 'web'.
- `environment`: The environment to use. Default is "web".

## Auth States

LangGraph CUA integrates with Scrapybara's [auth states API](https://docs.scrapybara.com/auth-states) to persist browser authentication sessions. This allows you to authenticate once (e.g., logging into Amazon) and reuse that session in future runs.

### Using Auth States

Pass an `auth_state_id` when creating your CUA graph:

```python
from langgraph_cua import create_cua

cua_graph = create_cua(auth_state_id="<your_auth_state_id>")
```

The graph stores this ID in the `authenticated_id` state field. If you change the `auth_state_id` in future runs, the graph will automatically reauthenticate.

### Managing Auth States with Scrapybara SDK

#### Save an Auth State

```python
from scrapybara import Scrapybara

client = Scrapybara(api_key="<api_key>")
instance = client.get("<instance_id>")
auth_state_id = instance.save_auth(name="example_site").auth_state_id
```

#### Modify an Auth State

```python
client = Scrapybara(api_key="<api_key>")
instance = client.get("<instance_id>")
instance.modify_auth(auth_state_id="your_existing_auth_state_id", name="renamed_auth_state")
```

> [!NOTE]
> To apply changes to an auth state in an existing run, set the `authenticated_id` state field to `None` to trigger re-authentication.


## Development

To get started with development, first clone the repository:

```bash
git clone https://github.com/langchain-ai/langgraph-cua.git
```

Create a virtual environment:

```bash
uv venv
```

Activate it:

```bash
source .venv/bin/activate
```

Then, install dependencies:

```bash
uv sync --all-groups
```

Next, set the required environment variables:

```bash
cp .env.example .env
```

Finally, you can then run the integration tests:

```bash
pytest -xvs tests/integration/test_cua.py
```
