"""John Deere agent tools for sales and quoting functionality."""

import datetime
from typing import List

from langchain_core.tools import tool

from ..constants import (
    DEFAULT_FINANCING_TERM,
    DEFAULT_INTEREST_RATE,
    EQUIPMENT_PRICING,
    TAX_AND_FEES_MULTIPLIER,
    get_equipment_price,
    get_equipment_type,
)
from ..rag_tool import get_rag_system
from ..knowledge_bases.john_deere import JOHN_DEERE_SALES_KNOWLEDGE
from ..config import config


@tool
def search_john_deere_sales_manual(query: str) -> str:
    """
    Search the John Deere sales manual using RAG.

    Args:
        query: The search query

    Returns:
        Relevant information from the John Deere sales manual and product database
    """
    # Get RAG system for sales manual search
    rag_system = get_rag_system(
        knowledge_content=JOHN_DEERE_SALES_KNOWLEDGE,
        collection_name=config.chromadb.collection_name,
        persist_directory=config.chromadb.persist_directory,
        description="John Deere Sales Manual",
    )
    return rag_system.search(query)


@tool
def generate_john_deere_quote(
    customer_name: str,
    model: str,
    optional_features: str = "",
    financing_term: int = DEFAULT_FINANCING_TERM,
) -> str:
    """
    Generate a simplified quote for John Deere equipment.

    Args:
        customer_name: Name of the customer requesting the quote
        model: Specific model number (e.g., 1025R, 5075E, S760)
        optional_features: Comma-separated list of optional features
        financing_term: Financing term in months (default: 60 months)

    Returns:
        Equipment quote with pricing and financing information
    """
    model_upper = model.upper()
    if model_upper not in EQUIPMENT_PRICING:
        available_models = ", ".join(EQUIPMENT_PRICING.keys())
        return f"Model {model} not found. Available models: {available_models}"

    base_price = get_equipment_price(model_upper)
    equipment_type = get_equipment_type(model_upper)

    # Calculate options cost
    features_list = _parse_optional_features(optional_features)
    options_cost = _calculate_options_cost(features_list, base_price)

    # Calculate totals
    subtotal = base_price + options_cost
    total_price = subtotal * TAX_AND_FEES_MULTIPLIER

    # Calculate financing
    monthly_payment = _calculate_monthly_payment(total_price, financing_term)

    # Generate quote
    return _format_quote(
        customer_name=customer_name,
        equipment_model=model_upper,
        base_price=base_price,
        options_cost=options_cost,
        subtotal=subtotal,
        tax_and_fees=total_price - subtotal,
        total=total_price,
        monthly_payment=monthly_payment,
        quote_number=_generate_quote_number(customer_name),
    )


def _parse_optional_features(optional_features: str) -> List[str]:
    """Parse optional features string into a list."""
    if not optional_features.strip():
        return []
    return [
        feature.strip() for feature in optional_features.split(",") if feature.strip()
    ]


def _calculate_options_cost(features_list: list[str], base_price: float) -> float:
    """Calculate the cost of optional features."""
    features_count = len(features_list)
    return base_price * 0.1 * features_count


def _calculate_monthly_payment(total_price: float, financing_term: int) -> float:
    """Calculate monthly payment for financing."""
    if financing_term <= 0:
        return 0.0

    monthly_rate = DEFAULT_INTEREST_RATE / 12
    if monthly_rate == 0:
        return total_price / financing_term

    # Standard loan payment formula
    numerator = total_price * monthly_rate * (1 + monthly_rate) ** financing_term
    denominator = (1 + monthly_rate) ** financing_term - 1

    return numerator / denominator


def _format_quote(
    customer_name: str,
    equipment_model: str,
    base_price: float,
    options_cost: float,
    subtotal: float,
    tax_and_fees: float,
    total: float,
    monthly_payment: float,
    quote_number: str,
) -> str:
    """Format the quote into a readable string."""
    quote_date = datetime.datetime.now().strftime("%B %d, %Y")
    
    # Get equipment type for display
    equipment_type = get_equipment_type(equipment_model)

    return f"""JOHN DEERE EQUIPMENT QUOTE
Quote #{quote_number} | Date: {quote_date}
Customer: {customer_name}

EQUIPMENT:
• Model: {equipment_model}
• Type: {equipment_type}
• Base Price: ${base_price:,.2f}

OPTIONAL FEATURES:
Options Cost: ${options_cost:,.2f}

PRICING BREAKDOWN:
• Base Price: ${base_price:,.2f}
• Options: ${options_cost:,.2f}
• Subtotal: ${subtotal:,.2f}
• Tax & Fees: ${tax_and_fees:,.2f}
• TOTAL: ${total:,.2f}

FINANCING:
Term: {DEFAULT_FINANCING_TERM} months @ {DEFAULT_INTEREST_RATE * 100:.1f}% APR
Monthly Payment: ${monthly_payment:,.2f}

Quote valid for 30 days. Contact your dealer for availability."""


def _generate_quote_number(customer_name: str) -> str:
    """Generate a unique quote number."""
    date_part = datetime.datetime.now().strftime("%Y%m%d")
    customer_hash = abs(hash(customer_name)) % 100
    return f"JD{date_part}{customer_hash:02d}"


__all__ = ["search_john_deere_sales_manual", "generate_john_deere_quote"]
