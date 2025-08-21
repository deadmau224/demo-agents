"""Constants and configuration values for the Demo Agent."""

from typing import Final, TypedDict

# AI Models
DEFAULT_OPENAI_MODEL: Final[str] = "gpt-4o-mini"
DEFAULT_AI_GATEWAY_MODEL: Final[str] = "gpt-4o-mini"
DEFAULT_EMBEDDING_MODEL: Final[str] = "text-embedding-3-small"

# ChromaDB Configuration
DEFAULT_CHROMADB_PERSIST_DIR: Final[str] = "./chroma_db"
DEFAULT_CHROMADB_COLLECTION: Final[str] = "john_deere_sales"

# Galileo Configuration
DEFAULT_GALILEO_PROJECT: Final[str] = "john-deere-agent-evaluation"
DEFAULT_EXPERIMENT_NAME: Final[str] = "john-deere-agent-test"

# Session Configuration
DEFAULT_SESSION_ID_LENGTH: Final[int] = 8

# UI Constants
UI_TITLE: Final[str] = "🚜 John Deere Sales Assistant"
UI_CHAT_INPUT_PLACEHOLDER: Final[str] = "Ask about John Deere equipment, pricing, or get a quote..."
UI_EXAMPLE_QUERIES_HEADER: Final[str] = "Example Queries"
UI_PROCESSING_MESSAGE: Final[str] = "Processing your request..."
SUCCESS_WELCOME: Final[str] = "👋 Welcome! I'm your John Deere sales assistant. I can help you with equipment information, pricing, and generate quotes. What would you like to know?"

# Example Queries
EXAMPLE_QUERY_1: Final[str] = "Tell me about the 6155R tractor specifications"
EXAMPLE_QUERY_2: Final[str] = "Generate a quote for a 6155R tractor with front loader"

# Progress Indicators
PROGRESS_EMOJI_DEFAULT: Final[str] = "⚙️"
PROGRESS_EMOJI_MULTILINGUAL: Final[str] = "🌐"

# Error Messages
ERROR_GALILEO_SESSION: Final[str] = "Failed to start Galileo session: {}"
ERROR_AGENT_INITIALIZATION: Final[str] = "Failed to initialize agent: {}"
ERROR_AI_GATEWAY_CONFIG: Final[str] = "AI Gateway configuration error: {}"
ERROR_AI_GATEWAY_TOKEN: Final[str] = "Failed to obtain AI Gateway access token: {}"
ERROR_QUERY_PROCESSING: Final[str] = "Error processing query: {}"

# Equipment Pricing
EQUIPMENT_PRICING: Final[dict[str, dict[str, float]]] = {
    "6155R": {
        "base_price": 125000.0,
        "front_loader": 15000.0,
        "cab": 8000.0,
        "4wd": 12000.0,
        "premium_seat": 2500.0,
        "climate_control": 3000.0,
    },
    "6120M": {
        "base_price": 85000.0,
        "front_loader": 12000.0,
        "cab": 6000.0,
        "4wd": 10000.0,
        "premium_seat": 2000.0,
        "climate_control": 2500.0,
    },
    "5075E": {
        "base_price": 45000.0,
        "front_loader": 8000.0,
        "cab": 5000.0,
        "4wd": 8000.0,
        "premium_seat": 1500.0,
        "climate_control": 2000.0,
    },
}

# Financing and Fees
DEFAULT_FINANCING_TERM: Final[int] = 60  # months
DEFAULT_INTEREST_RATE: Final[float] = 0.049  # 4.9%
TAX_AND_FEES_MULTIPLIER: Final[float] = 1.08  # 8% tax and fees

# Quote Generation
QUOTE_NUMBER_PREFIX: Final[str] = "JD"
QUOTE_NUMBER_LENGTH: Final[int] = 6

# RAG System
RAG_CHUNK_SIZE: Final[int] = 1000
RAG_CHUNK_OVERLAP: Final[int] = 200


# Type-safe equipment pricing access
def get_equipment_price(model: str) -> float:
    """Get the base price for a specific equipment model."""
    if model not in EQUIPMENT_PRICING:
        raise ValueError(f"Model {model} not found in equipment pricing")
    return EQUIPMENT_PRICING[model]["base_price"]


def get_equipment_type(model: str) -> str:
    """Get the equipment type for a specific model."""
    # Map models to types based on their characteristics
    if model in ["6155R", "6120M"]:
        return "Row Crop Tractor"
    elif model in ["5075E"]:
        return "Agricultural Tractor"
    else:
        return "Tractor"
