"""
Delivery gateway — Shiprocket only.

Shiprocket aggregates 25+ courier partners and automatically selects
the cheapest available courier per order. delhivery.py and dtdc.py
have been deprecated (kept as stubs with explanatory comments).

Usage:
    from app.delivery import shiprocket
    result = shiprocket.create_order(order)
"""

from app.delivery import shiprocket  # noqa: F401 — re-export for convenience

__all__ = ["shiprocket"]
