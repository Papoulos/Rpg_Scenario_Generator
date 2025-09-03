import os
import json
import logging
from dotenv import load_dotenv

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# --- Environment and API Key Loading ---
load_dotenv()

# Load all API keys from environment variables for security.
# Users should add their keys to the .env file.
api_keys = {
    "google": os.getenv("GOOGLE_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "mistral": os.getenv("MISTRAL_API_KEY"),
    "custombot": os.getenv("CUSTOMBOT_API_KEY"),
}


# --- LLM Provider Configuration ---
# This dictionary defines the default, pre-configured LLM providers.
# It can be extended by an external JSON configuration file.
llm_providers = {
    # --- Pre-configured Public LLMs ---
    "gemini-flash": {
        "service": "google",
        "model_name": "gemini-1.5-flash",
        "api_key_name": "google",
        "system_prompt": "You are a helpful assistant powered by Google Gemini.",
        "timeout": 600,
    },
    "gpt-4": {
        "service": "openai",
        "model_name": "gpt-4",
        "api_key_name": "openai",
        "system_prompt": "You are a helpful assistant powered by OpenAI GPT-4.",
        "timeout": 600,
    },
    "mistral-large": {
        "service": "mistral",
        "model_name": "mistral-large-latest",
        "api_key_name": "mistral",
        "system_prompt": "You are a helpful assistant powered by Mistral AI.",
        "timeout": 600,
    },
}

def load_custom_llm_config():
    """
    Loads custom LLM configurations from an external JSON file if specified.
    The path to the file is retrieved from the CUSTOM_LLM_CONFIG_PATH environment variable.
    """
    config_path = os.getenv("CUSTOM_LLM_CONFIG_PATH")
    if not config_path:
        logging.info("CUSTOM_LLM_CONFIG_PATH not set. Skipping loading of custom LLM config.")
        return

    if not os.path.exists(config_path):
        logging.warning(f"Custom LLM config file not found at: {config_path}")
        return

    try:
        with open(config_path, 'r') as f:
            custom_configs = json.load(f)

        # Merge the custom configurations into the main providers dictionary
        llm_providers.update(custom_configs)
        logging.info(f"Successfully loaded and merged {len(custom_configs)} custom LLM provider(s) from {config_path}.")

    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from the custom LLM config file: {config_path}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while loading custom LLM config: {e}")

# --- Initialize Configurations ---
# Load custom configurations when the module is imported.
load_custom_llm_config()

def get_provider_config(model_name: str):
    """
    Retrieves the configuration for a given model name from the merged providers list.
    """
    return llm_providers.get(model_name)
