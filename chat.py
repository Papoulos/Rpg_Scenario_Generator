import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from openai import OpenAI
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
    extra_headers = None
    custom_headers_config = provider_config.get("headers")
    if custom_headers_config:
        extra_headers = {}
        for key, value in custom_headers_config.items():
            placeholders = re.findall(r"\{(.+?)\}", str(value))
            processed_value = str(value)
            for placeholder in placeholders:
                env_value = os.getenv(placeholder, "")
                processed_value = processed_value.replace(f"{{{placeholder}}}", env_value)
            extra_headers[key] = processed_value

    final_api_key = None if custom_headers_config else api_key

    # --- Timeout Configuration ---
    timeout_value = provider_config.get("timeout", 60)
    try:
        timeout = float(timeout_value)
    except (ValueError, TypeError):
        timeout = 60

    if service == "google":
        return ChatGoogleGenerativeAI(model=config_model_name, google_api_key=api_key, client_options={"timeout": timeout})

    elif service in ["openai", "openai_compatible"]:
        endpoint = provider_config.get("endpoint")

        http_client = OpenAI(
            base_url=endpoint,
            api_key=final_api_key,
            default_headers=extra_headers,
            timeout=timeout,
        ).chat.completions

        return ChatOpenAI(
            model=config_model_name,
            client=http_client
        )

    elif service == "mistral":
        return ChatMistralAI(model=config_model_name, api_key=api_key, timeout=timeout)

    else:
        raise ValueError(f"Unsupported LLM service: {service}")

def run_chat_completion(model_name: str, messages: list, stream: bool = False):
    """
    Runs a chat completion with the specified model and messages.

    Args:
        model_name (str): The name of the model to use.
        messages (list): A list of message dictionaries, e.g., [{"role": "user", "content": "Hello"}].
        stream (bool): If True, streams the response.

    Returns:
        If stream is False, a string with the full response.
        If stream is True, a generator that yields response chunks.
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

    if stream:
        return (chunk.content for chunk in llm.stream(chat_messages))
    else:
        response = llm.invoke(chat_messages)
        return response.content
