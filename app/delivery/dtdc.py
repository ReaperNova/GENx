"""
DEPRECATED — DTDC integration is no longer used directly.

Shiprocket now acts as the single delivery gateway for GenX.
It automatically selects the cheapest available courier per order
(which may include DTDC, Delhivery, BlueDart, Ekart, Ecom Express, etc.)
based on customer pincode, package weight, and COD preference.

All delivery logic is in: app/delivery/shiprocket.py
"""
