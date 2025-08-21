"""Demo Agent - John Deere Sales Assistant

A modular AI agent system for John Deere equipment sales and support.
"""

from .john_deere.agent import JohnDeereAgentRunner, get_john_deere_agent
from .john_deere.tools import generate_john_deere_quote, search_john_deere_sales_manual
from .config import config
from .constants import (
    DEFAULT_AI_GATEWAY_MODEL,
    DEFAULT_OPENAI_MODEL,
    EQUIPMENT_PRICING,
    get_equipment_price,
    get_equipment_type,
)

__version__ = "0.1.0"
__all__ = [
    # Core agent classes
    "JohnDeereAgentRunner",
    "get_john_deere_agent",
    
    # Tools
    "generate_john_deere_quote",
    "search_john_deere_sales_manual",
    
    # Configuration
    "config",
    
    # Constants and utilities
    "DEFAULT_AI_GATEWAY_MODEL",
    "DEFAULT_OPENAI_MODEL",
    "EQUIPMENT_PRICING",
    "get_equipment_price",
    "get_equipment_type",
]
