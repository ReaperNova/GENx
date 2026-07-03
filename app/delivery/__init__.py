"""
Delivery partner factory.
Usage:
    from app.delivery import get_delivery_partner
    partner = get_delivery_partner("shiprocket")
    result = partner.book_pickup(order)
"""

import importlib


def get_delivery_partner(name: str):
    """Return the delivery module for the given partner name."""
    name = (name or "shiprocket").lower().strip()
    try:
        module = importlib.import_module(f"app.delivery.{name}")
        return module
    except ModuleNotFoundError:
        raise ValueError(f"Unknown delivery partner: {name}")
