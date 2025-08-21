"""John Deere agent tools for sales and quoting functionality."""

import datetime
from typing import List

from langchain_core.tools import tool

from ..constants import (
    DEFAULT_FINANCING_TERM,
    DEFAULT_ANNUAL_INTEREST_RATE,
    EQUIPMENT_PRICING,
    OPTIONS_COST_PERCENTAGE,
    TAX_AND_FEES_MULTIPLIER,
    SUCCESS_QUOTE_VALID,
    get_equipment_price,
    get_equipment_type,
)
from ..knowledge_bases.john_deere import JOHN_DEERE_SALES_KNOWLEDGE
from ..rag_tool import get_rag_system


@tool
def search_john_deere_sales_manual(query: str) -> str:
    """
    Search the John Deere sales manual and product knowledge base.
    
    This tool provides access to comprehensive information about:
    - Tractor models and specifications (1 Series through 9R Series)
    - Combine harvesters (S700, X9, T-Series)
    - Planters and seeding equipment
    - Precision agriculture technology
    - Pricing and configuration options
    - Financing and warranty programs
    - Training and support services

    Args:
        query: The question or topic to search for in the John Deere sales knowledge base

    Returns:
        Relevant information from the John Deere sales manual and product database
    """
    rag_instance = get_rag_system(
        knowledge_content=JOHN_DEERE_SALES_KNOWLEDGE,
        index_name="john-deere-sales-rag",
        namespace="john-deere-sales",
        description="John Deere Sales",
    )
    return rag_instance.search(query)


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
        model_upper=model_upper,
        equipment_type=equipment_type,
        base_price=base_price,
        features_list=features_list,
        options_cost=options_cost,
        total_price=total_price,
        financing_term=financing_term,
        monthly_payment=monthly_payment,
    )


def _parse_optional_features(optional_features: str) -> List[str]:
    """Parse optional features string into a list."""
    if not optional_features.strip():
        return []
    return [feature.strip() for feature in optional_features.split(",") if feature.strip()]


def _calculate_options_cost(features_list: List[str], base_price: int) -> float:
    """Calculate the cost of optional features."""
    features_count = len(features_list)
    return features_count * (base_price * OPTIONS_COST_PERCENTAGE)


def _calculate_monthly_payment(total_price: float, financing_term: int) -> float:
    """Calculate monthly payment for financing."""
    if financing_term <= 0:
        return 0.0
    
    monthly_rate = DEFAULT_ANNUAL_INTEREST_RATE / 12
    if monthly_rate == 0:
        return total_price / financing_term
    
    # Standard loan payment formula
    numerator = total_price * monthly_rate * (1 + monthly_rate) ** financing_term
    denominator = (1 + monthly_rate) ** financing_term - 1
    
    return numerator / denominator


def _format_quote(
    customer_name: str,
    model_upper: str,
    equipment_type: str,
    base_price: int,
    features_list: List[str],
    options_cost: float,
    total_price: float,
    financing_term: int,
    monthly_payment: float,
) -> str:
    """Format the quote into a readable string."""
    quote_date = datetime.datetime.now().strftime("%B %d, %Y")
    quote_number = _generate_quote_number(customer_name)
    
    features_display = (
        "\n".join([f"• {feature}" for feature in features_list])
        if features_list
        else "• None selected"
    )
    
    return f"""JOHN DEERE EQUIPMENT QUOTE
Quote #{quote_number} | Date: {quote_date}
Customer: {customer_name}

EQUIPMENT:
• Model: {model_upper}
• Type: {equipment_type}
• Base Price: ${base_price:,.2f}

OPTIONAL FEATURES:
{features_display}
Options Cost: ${options_cost:,.2f}

TOTAL PRICE: ${total_price:,.2f}
(Includes taxes, delivery, and setup)

FINANCING:
Term: {financing_term} months @ {DEFAULT_ANNUAL_INTEREST_RATE * 100:.0f}% APR
Monthly Payment: ${monthly_payment:,.2f}

{SUCCESS_QUOTE_VALID}"""


def _generate_quote_number(customer_name: str) -> str:
    """Generate a unique quote number."""
    date_part = datetime.datetime.now().strftime("%Y%m%d")
    customer_hash = abs(hash(customer_name)) % 100
    return f"JD{date_part}{customer_hash:02d}"


__all__ = ["search_john_deere_sales_manual", "generate_john_deere_quote"]
