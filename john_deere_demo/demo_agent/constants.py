"""Constants used throughout the Demo Agent application."""

from typing import Final, TypedDict

# AI Gateway Configuration
DEFAULT_AI_GATEWAY_MODEL: Final[str] = "gpt-4o-mini-2024-07-18"
DEFAULT_OPENAI_MODEL: Final[str] = "gpt-4.1"
DEFAULT_EMBEDDING_MODEL: Final[str] = "text-embedding-3-large"
DEFAULT_EMBEDDING_DIMENSION: Final[int] = 3072

# Pinecone Configuration
DEFAULT_PINECONE_CLOUD: Final[str] = "aws"
DEFAULT_PINECONE_REGION: Final[str] = "us-east-1"

class EquipmentInfo(TypedDict):
    """Type definition for equipment information."""
    price: int
    type: str

# John Deere Equipment Pricing
EQUIPMENT_PRICING: Final[dict[str, EquipmentInfo]] = {
    "1025R": {"price": 17500, "type": "Compact Utility Tractor"},
    "3038E": {"price": 24000, "type": "Utility Tractor"},
    "5075E": {"price": 48500, "type": "Agricultural Tractor"},
    "6155R": {"price": 135000, "type": "Row Crop Tractor"},
    "S760": {"price": 502000, "type": "Combine Harvester"},
    "S780": {"price": 545000, "type": "Combine Harvester"},
    "DB60": {"price": 85000, "type": "Planter"},
}

# Type-safe equipment pricing access
def get_equipment_price(model: str) -> int:
    """Get the base price for a specific equipment model."""
    if model not in EQUIPMENT_PRICING:
        raise ValueError(f"Model {model} not found in equipment pricing")
    return EQUIPMENT_PRICING[model]["price"]

def get_equipment_type(model: str) -> str:
    """Get the equipment type for a specific model."""
    if model not in EQUIPMENT_PRICING:
        raise ValueError(f"Model {model} not found in equipment pricing")
    return EQUIPMENT_PRICING[model]["type"]

# Financial Constants
DEFAULT_FINANCING_TERM: Final[int] = 60
DEFAULT_ANNUAL_INTEREST_RATE: Final[float] = 0.05
TAX_AND_FEES_MULTIPLIER: Final[float] = 1.08
OPTIONS_COST_PERCENTAGE: Final[float] = 0.1

# RAG System Constants
DEFAULT_RAG_INDEX_NAME: Final[str] = "john-deere-sales-rag"
DEFAULT_RAG_NAMESPACE: Final[str] = "john-deere-sales"
DEFAULT_RAG_DESCRIPTION: Final[str] = "John Deere Sales"

# Streamlit Constants
DEFAULT_SESSION_ID_LENGTH: Final[int] = 10
PROGRESS_STEP_DELAY: Final[float] = 0.6

# Galileo Constants
DEFAULT_GALILEO_PROJECT: Final[str] = "john-deere-agent-evaluation"
DEFAULT_EXPERIMENT_NAME: Final[str] = "john-deere-agent-test-no-legal-advice"

# Message Types
MESSAGE_TYPE_USER: Final[str] = "user"
MESSAGE_TYPE_ASSISTANT: Final[str] = "assistant"
MESSAGE_TYPE_SYSTEM: Final[str] = "system"

# Error Messages
ERROR_AI_GATEWAY_TOKEN: Final[str] = "Failed to obtain access token. The John Deere agent will not be able to authenticate."
ERROR_AI_GATEWAY_CONFIG: Final[str] = "Please check your .env file and ensure the OAuth credentials are correct."
ERROR_AGENT_INITIALIZATION: Final[str] = "Failed to initialize John Deere agent: {}"
ERROR_QUERY_PROCESSING: Final[str] = "Error processing query: {}"
ERROR_GALILEO_SESSION: Final[str] = "Failed to start Galileo session: {}"

# Success Messages
SUCCESS_WELCOME: Final[str] = "Welcome!"
SUCCESS_QUOTE_VALID: Final[str] = "Quote valid for 30 days. Contact your dealer for availability."

# UI Elements
UI_TITLE: Final[str] = "John Deere Agent"
UI_CHAT_INPUT_PLACEHOLDER: Final[str] = "How can I help you?..."
UI_PROCESSING_MESSAGE: Final[str] = "Processing..."
UI_EXAMPLE_QUERIES_HEADER: Final[str] = "Example queries"

# Example Queries
EXAMPLE_QUERY_1: Final[str] = "What are the specifications for the 6155R tractor?"
EXAMPLE_QUERY_2: Final[str] = "Generate a quote for John Smith for a S780 combine with AutoTrac GPS"

# Progress Steps
PROGRESS_STEPS: Final[list[str]] = [
    "Intent Classification",
    "Supply Chain Analysis",
    "Financial Analysis",
    "Synthesis",
    "Spanish Translation",
    "Hindi Translation",
    "Multilingual Combination",
]

# Progress Step Emojis
PROGRESS_EMOJI_MULTILINGUAL: Final[str] = "🌍"
PROGRESS_EMOJI_DEFAULT: Final[str] = "🧩"
