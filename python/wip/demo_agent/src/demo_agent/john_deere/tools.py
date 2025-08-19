import datetime

from knowledge_bases.john_deere import JOHN_DEERE_SALES_KNOWLEDGE
from langchain_core.tools import tool
from rag_tool import get_rag_system


@tool
def search_john_deere_sales_manual(query: str) -> str:
    """
    Search the John Deere sales manual and product knowledge base for information about
    equipment specifications, pricing, features, warranty, service programs, and sales processes.

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
    print(f"Searching for {query} in tool")
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
    financing_term: int = 60,
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
    # Simplified pricing database
    equipment_pricing = {
        "1025R": {"price": 17500, "type": "Compact Utility Tractor"},
        "3038E": {"price": 24000, "type": "Utility Tractor"},
        "5075E": {"price": 48500, "type": "Agricultural Tractor"},
        "6155R": {"price": 135000, "type": "Row Crop Tractor"},
        "S760": {"price": 502000, "type": "Combine Harvester"},
        "S780": {"price": 545000, "type": "Combine Harvester"},
        "DB60": {"price": 85000, "type": "Planter"},
    }

    model_upper = model.upper()
    if model_upper not in equipment_pricing:
        return f"Model {model} not found. Available models: {', '.join(equipment_pricing.keys())}"

    equipment = equipment_pricing[model_upper]
    base_price = equipment["price"]
    equipment_type = equipment["type"]

    # Simple options calculation (10% of base price per feature)
    features_list = [f.strip() for f in optional_features.split(",") if f.strip()]
    options_cost = len(features_list) * (base_price * 0.1)

    # Calculate totals
    subtotal = base_price + options_cost
    total_price = subtotal * 1.08  # Include taxes and fees

    # Simple financing calculation
    if financing_term > 0:
        monthly_payment = (
            total_price
            * (0.05 / 12)
            * (1 + 0.05 / 12) ** financing_term
            / ((1 + 0.05 / 12) ** financing_term - 1)
        )
    else:
        monthly_payment = 0

    # Generate simplified quote
    quote_date = datetime.datetime.now().strftime("%B %d, %Y")
    quote_number = (
        f"JD{datetime.datetime.now().strftime('%Y%m%d')}{hash(customer_name) % 100:02d}"
    )

    quote = f"""JOHN DEERE EQUIPMENT QUOTE
Quote #{quote_number} | Date: {quote_date}
Customer: {customer_name}

EQUIPMENT:
• Model: {model_upper}
• Type: {equipment_type}
• Base Price: ${base_price:,.2f}

OPTIONAL FEATURES:
{chr(10).join([f'• {feature}' for feature in features_list]) if features_list else '• None selected'}
Options Cost: ${options_cost:,.2f}

TOTAL PRICE: ${total_price:,.2f}
(Includes taxes, delivery, and setup)

FINANCING:
Term: {financing_term} months @ 5% APR
Monthly Payment: ${monthly_payment:,.2f}

Quote valid for 30 days. Contact your dealer for availability.
"""

    return quote


__all__ = ["search_john_deere_sales_manual", "generate_john_deere_quote"]
