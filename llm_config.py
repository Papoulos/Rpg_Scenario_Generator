import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- API Key Management ---
# Load API keys from environment variables for security.
# Add your keys to the .env file in the root of the project.
api_keys = {
    "google": os.getenv("GOOGLE_API_KEY"),
    "openai": os.getenv("OPENAI_API_KEY"),
    "mistral": os.getenv("MISTRAL_API_KEY"),
    "custombot": os.getenv("CUSTOMBOT_API_KEY"), # Example for a custom bot
}

# --- LLM Provider Configuration ---
# This dictionary defines the available LLM providers.
# - 'service': The provider's service name (e.g., 'google', 'openai'). This helps in identifying the correct LangChain class.
# - 'model_name': The specific model to be used for the provider.
# - 'api_key_name': The key to look up the API key in the `api_keys` dictionary.
# - 'endpoint' (Optional): The API endpoint for custom or self-hosted models.
# - 'system_prompt' (Optional): A default system prompt to be used with the model.

llm_providers = {
    # --- Pre-configured Public LLMs ---
    "gemini-flash": {
        "service": "google",
        "model_name": "gemini-1.5-flash",
        "api_key_name": "google",
        "system_prompt": "You are a helpful assistant powered by Google Gemini.",
    },
    "gpt-4": {
        "service": "openai",
        "model_name": "gpt-4",
        "api_key_name": "openai",
        "system_prompt": "You are a helpful assistant powered by OpenAI GPT-4.",
    },
    "mistral-large": {
        "service": "mistral",
        "model_name": "mistral-large-latest",
        "api_key_name": "mistral",
        "system_prompt": "You are a helpful assistant powered by Mistral AI.",
    },

    # --- Template for a Custom OpenAI-Compatible Bot ---
    # To use this, uncomment the section below and fill in the details.
    # Ensure you have set the corresponding API key in your .env file.
    #
    # 'custom-model': {
    #     'service': 'openai_compatible',
    #     'model_name': 'name-of-your-local-model', // The model name your API expects
    #     'api_key_name': 'custombot', // The key for the API key in the `api_keys` dictionary
    #     'endpoint': 'http://your-custom-api-endpoint/v1', // The base URL of your custom API
    #     'system_prompt': 'You are a custom helpful assistant.' // The default system message
    # },
}

def get_provider_config(model_name: str):
    """
    Retrieves the configuration for a given model name.
    """
    return llm_providers.get(model_name)
