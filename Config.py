"""
Configuration for API providers.

This file loads configuration from a .env file in the same directory.
Create a .env file based on .env.example for local development.
"""
import os

def load_env_file():
    """Load .env file if it exists."""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

# Load .env file
load_env_file()

# Bocha (博查) - default host is the production API
BOCHA_API_URL = os.getenv("BOCHA_API_URL", "https://api.bochaai.com")
BOCHA_API_KEY = os.getenv("BOCHA_API_KEY")  # required for authenticated calls

# Tavily - default host
TAVILY_API_URL = os.getenv("TAVILY_API_URL", "https://api.tavily.com")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

# Small LLM for keyword generation
SMALL_LLM_URL = os.getenv("SMALL_LLM_URL")
SMALL_LLM_MODEL = os.getenv("SMALL_LLM_MODEL", "llama2")
SMALL_LLM_API_KEY = os.getenv("SMALL_LLM_API_KEY") 


def require_env_keys():
    missing = []
    if not BOCHA_API_KEY:
        missing.append("BOCHA_API_KEY")
    if not TAVILY_API_KEY:
        missing.append("TAVILY_API_KEY")
    return missing