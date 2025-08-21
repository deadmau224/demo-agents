"""John Deere agent tools for sales and quoting functionality.

Includes:
- `search_john_deere_sales_manual`: Retrieval-Augmented Generation (RAG)
  search over an embedded sales manual using ChromaDB for local vector
  storage.
- `generate_john_deere_quote`: A simplified quote generator that applies
  base prices, a flat per-feature uplift, tax/fees, and basic financing.
"""

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
from ..utils.logging import logger


@tool
def search_john_deere_sales_manual(query: str) -> str:
    """Search the John Deere sales manual using RAG backed by ChromaDB.

    Args:
        query: Natural-language question to search the knowledge base.

    Returns:
        A synthesized answer using retrieved context from the embedded
        sales manual content.
    """
    logger.info("[TOOLS] search_john_deere_sales_manual: start")
    logger.info("[TOOLS] RAG query: %s", query)
    logger.info(
        "[TOOLS] Using ChromaDB collection '%s' at '%s'",
        config.chromadb.collection_name,
        config.chromadb.persist_directory,
    )
    # Get RAG system for sales manual search
    rag_system = get_rag_system(
        knowledge_content=JOHN_DEERE_SALES_KNOWLEDGE,
        collection_name=config.chromadb.collection_name,
        persist_directory=config.chromadb.persist_directory,
        description="John Deere Sales Manual",
    )
    response = rag_system.search(query)
    preview = (response[:200] + "...") if len(response) > 200 else response
    logger.info("[TOOLS] search_john_deere_sales_manual: completed")
    logger.info("[TOOLS] RAG response (preview): %s", preview)
    return response


@tool
def generate_john_deere_quote(
    customer_name: str,
    model: str,
    optional_features: str = "",
    financing_term: int = DEFAULT_FINANCING_TERM,
) -> str:
    """Generate a simplified quote for John Deere equipment.

    Pricing model:
    - Base price from `EQUIPMENT_PRICING`.
    - Each optional feature adds 10% of the base price (simple uplift).
    - Subtotal is multiplied by `TAX_AND_FEES_MULTIPLIER`.
    - Financing uses a standard amortization formula with
      `DEFAULT_INTEREST_RATE` and provided `financing_term`.

    Args:
        customer_name: Customer name.
        model: Model number (e.g., 6155R, 6120M, 5075E).
        optional_features: Comma-separated list of features.
        financing_term: Financing term in months.

    Returns:
        A formatted quote string including pricing and financing details.
    """
    logger.info("[TOOLS] generate_john_deere_quote: start")
    logger.info(
        "[TOOLS] Inputs -> customer_name='%s', model='%s', optional_features='%s', financing_term=%s",
        customer_name,
        model,
        optional_features,
        financing_term,
    )
    model_upper = model.upper()
    if model_upper not in EQUIPMENT_PRICING:
        available_models = ", ".join(EQUIPMENT_PRICING.keys())
        logger.info("[TOOLS] Unknown model '%s'. Available: %s", model_upper, available_models)
        return f"Model {model} not found. Available models: {available_models}"

    base_price = get_equipment_price(model_upper)
    logger.info("[TOOLS] Base price for %s: %.2f", model_upper, base_price)

    # Calculate options cost
    features_list = _parse_optional_features(optional_features)
    logger.info("[TOOLS] Parsed features: %s", features_list)
    options_cost = _calculate_options_cost(features_list, base_price)
    logger.info("[TOOLS] Options cost: %.2f", options_cost)

    # Calculate totals
    subtotal = base_price + options_cost
    total_price = subtotal * TAX_AND_FEES_MULTIPLIER
    logger.info("[TOOLS] Subtotal: %.2f, Tax/Fees multiplier: %.2f, Total: %.2f", subtotal, TAX_AND_FEES_MULTIPLIER, total_price)

    # Calculate financing
    monthly_payment = _calculate_monthly_payment(total_price, financing_term)
    logger.info("[TOOLS] Financing -> term: %s months, monthly payment: %.2f", financing_term, monthly_payment)

    # Generate quote
    quote_number = _generate_quote_number(customer_name)
    logger.info("[TOOLS] Generated quote number: %s", quote_number)
    result = _format_quote(
        customer_name=customer_name,
        equipment_model=model_upper,
        base_price=base_price,
        options_cost=options_cost,
        subtotal=subtotal,
        tax_and_fees=total_price - subtotal,
        total=total_price,
        monthly_payment=monthly_payment,
        quote_number=quote_number,
    )
    logger.info("[TOOLS] generate_john_deere_quote: completed")
    return result


def _parse_optional_features(optional_features: str) -> List[str]:
    """Parse optional features string into a list."""
    if not optional_features.strip():
        return []
    return [
        feature.strip() for feature in optional_features.split(",") if feature.strip()
    ]


def _calculate_options_cost(features_list: list[str], base_price: float) -> float:
    """Calculate the cost of optional features.

    Applies a flat 10% of base price per feature.
    """
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
    """Format the quote into a readable string.

    Uses `DEFAULT_FINANCING_TERM` and `DEFAULT_INTEREST_RATE` for the
    financing display line.
    """
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
