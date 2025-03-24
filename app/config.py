import os
from dotenv import load_dotenv
from typing import Optional

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4-turbo")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2023-05-15")

# GitHub Configuration
GITHUB_ACCESS_TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")

# Vector Database Configuration
CHROMA_PERSIST_DIRECTORY = os.getenv("CHROMA_PERSIST_DIRECTORY", "data/chroma")

# Repository Configuration
REPO_URL = os.getenv("REPO_URL", "https://github.com/vanna-ai/vanna")
REPO_BRANCH = os.getenv("REPO_BRANCH", "main")
REPO_OWNER = "vanna-ai"  # Extracted from REPO_URL
REPO_NAME = "vanna"  # Extracted from REPO_URL

# Application Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# Model Configuration
EMBEDDING_MODEL = "text-embedding-3-small"  # Azure OpenAI embedding model name
COMPLETION_MODEL = "gpt-4o"  # Azure OpenAI completion model name

# Define file extensions to index
INDEXABLE_EXTENSIONS = [
    ".py", ".md", ".txt", ".yaml", ".yml", ".json", 
    ".js", ".ts", ".html", ".css", ".ipynb"
]

# Define directories or files to exclude from indexing
EXCLUDE_PATTERNS = [
    "venv", "__pycache__", ".git", ".github", 
    "node_modules", "dist", "build"
]

def validate_config() -> tuple[bool, Optional[str]]:
    """
    Validate that all required environment variables are set.
    Returns a tuple of (valid, error_message)
    """
    required_vars = [
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
    ]
    
    missing_vars = [var for var in required_vars if not globals().get(var)]
    
    if missing_vars:
        return False, f"Missing required environment variables: {', '.join(missing_vars)}"
    
    return True, None
