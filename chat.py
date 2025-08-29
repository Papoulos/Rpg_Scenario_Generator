import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from langchain_core.messages import HumanMessage, SystemMessage
from llm_config import get_provider_config, api_keys

def get_llm_instance(model_name: str):
    """
    Initializes and returns an instance of the language model based on the model name.

    Args:
        model_name (str): The name of the model to initialize.

    Returns:
        An instance of a LangChain chat model.

    Raises:
        ValueError: If the model is not configured or if the required API key is not set.
    """
    provider_config = get_provider_config(model_name)
    if not provider_config:
        raise ValueError(f"No configuration found for model: {model_name}")

    service = provider_config["service"]
    config_model_name = provider_config["model_name"]
    api_key_name = provider_config.get("api_key_name")

    # Try to get the API key from the pre-defined dictionary,
    # otherwise, get it directly from the environment variables.
    api_key = api_keys.get(api_key_name)
    if not api_key and api_key_name:
        api_key = os.getenv(api_key_name)

    if not api_key and api_key_name:
        raise ValueError(f"API key for '{api_key_name}' not found. Please ensure the environment variable '{api_key_name}' is set in your .env file.")

    # --- Header Configuration ---
    # By default, langchain-openai uses the "Authorization: Bearer <api_key>" header.
    # If a custom `headers` dict is provided in the config, we process it.
    extra_headers = None
    custom_headers_config = provider_config.get("headers")
    if custom_headers_config:
        extra_headers = {}
        for key, value in custom_headers_config.items():
            # Find all placeholders like {VAR_NAME} in the header value
            placeholders = re.findall(r"\{(.+?)\}", str(value))
            processed_value = str(value)
            for placeholder in placeholders:
                # Get the value from environment and replace the placeholder
                env_value = os.getenv(placeholder, "") # Default to empty string if not found
                processed_value = processed_value.replace(f"{{{placeholder}}}", env_value)
            extra_headers[key] = processed_value

    # For services that use custom headers, we pass the api_key as None to prevent
    # the default "Authorization" header from being added automatically by the client.
    # The user is expected to handle the full auth in the custom `headers` field.
    final_api_key = None if custom_headers_config else api_key

    # --- Timeout Configuration ---
    timeout = provider_config.get("timeout", 60)


    if service == "google":
        return ChatGoogleGenerativeAI(model=config_model_name, google_api_key=api_key, client_options={"timeout": timeout})

    elif service == "openai":
        return ChatOpenAI(model=config_model_name, api_key=final_api_key, extra_headers=extra_headers, timeout=timeout)

    elif service == "mistral":
        return ChatMistralAI(model=config_model_name, api_key=api_key, timeout=timeout)

    elif service == "openai_compatible":
        endpoint = provider_config.get("endpoint")
        if not endpoint:
            raise ValueError(f"Endpoint not configured for custom OpenAI compatible model: {model_name}")
        return ChatOpenAI(
            model=config_model_name,
            api_key=final_api_key,
            base_url=endpoint,
            extra_headers=extra_headers,
            timeout=timeout
        )

    else:
        raise ValueError(f"Unsupported LLM service: {service}")

def run_chat_completion(model_name: str, messages: list):
    """
    Runs a chat completion with the specified model and messages.

    Args:
        model_name (str): The name of the model to use.
        messages (list): A list of message dictionaries, e.g., [{"role": "user", "content": "Hello"}].

    Returns:
        The content of the AI's response message.
    """
    llm = get_llm_instance(model_name)

    # Add the default system prompt if no system message is present
    provider_config = get_provider_config(model_name)
    has_system_message = any(msg["role"] == "system" for msg in messages)

    chat_messages = []
    if provider_config.get("system_prompt") and not has_system_message:
        chat_messages.append(SystemMessage(content=provider_config["system_prompt"]))

    for msg in messages:
        if msg["role"] == "user":
            chat_messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "system":
            chat_messages.append(SystemMessage(content=msg["content"]))
        # LangChain automatically handles assistant messages in the history

    response = llm.invoke(chat_messages)
    return response.content
