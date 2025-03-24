from langchain_core.runnables.config import RunnableConfig

from ..types import CUAState
from ..utils import get_configuration_with_defaults, get_scrapybara_client


def authenticate(state: CUAState, config: RunnableConfig):
    instance_id = state.get("instance_id")
    environment = state.get("environment", "web")
    configuration = get_configuration_with_defaults(config)
    scrapybara_api_key = configuration.get("scrapybara_api_key")
    auth_state_id = configuration.get("auth_state_id")

    if instance_id is None or environment != "web" or auth_state_id is None:
        # If instance ID is not defined, environment is not "web", or auth state ID is not defined, do nothing.
        return {}

    if not scrapybara_api_key:
        raise ValueError(
            "Scrapybara API key not provided. Please provide one in the configurable fields, "
            "or set it as an environment variable (SCRAPYBARA_API_KEY)"
        )

    client = get_scrapybara_client(scrapybara_api_key)

    instance = client.get(instance_id)
    instance.authenticate(auth_state_id=auth_state_id)

    return {"authenticated_id": auth_state_id}
