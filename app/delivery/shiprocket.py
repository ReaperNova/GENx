"""
Shiprocket delivery partner integration — SANDBOX/TEST MODE
Docs: https://apidocs.shiprocket.in/
"""
import os
import requests
from flask import current_app

SHIPROCKET_BASE = "https://apiv2.shiprocket.in/v1/external"
_token_cache = {"token": None}


def _get_token() -> str:
    """Authenticate with Shiprocket and cache the JWT token."""
    if _token_cache["token"]:
        return _token_cache["token"]

    email = current_app.config.get("SHIPROCKET_EMAIL", "")
    password = current_app.config.get("SHIPROCKET_PASSWORD", "")

    resp = requests.post(
        f"{SHIPROCKET_BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    token = resp.json().get("token", "")
    _token_cache["token"] = token
    return token


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {_get_token()}",
    }


def book_pickup(order) -> dict:
    """
    Create a shipment on Shiprocket and request pickup.
    Returns: { success: bool, shipment_id, tracking_id, message }
    """
    try:
        payload = {
            "order_id": str(order.id),
            "order_date": order.ordered_at.strftime("%Y-%m-%d %H:%M"),
            "pickup_location": "Primary",
            "billing_customer_name": order.customer.name,
            "billing_address": order.customer.address,
            "billing_city": "Virar",
            "billing_pincode": "401303",
            "billing_state": "Maharashtra",
            "billing_country": "India",
            "billing_email": order.customer.email,
            "billing_phone": order.customer.phone or "9999999999",
            "shipping_is_billing": True,
            "order_items": [
                {
                    "name": item.product.name,
                    "sku": f"PROD-{item.product_id}",
                    "units": item.quantity,
                    "selling_price": item.price_at_purchase,
                }
                for item in order.items
            ],
            "payment_method": "Prepaid",
            "sub_total": order.subtotal,
            "length": 30,
            "breadth": 20,
            "height": 5,
            "weight": 0.5,
        }

        resp = requests.post(
            f"{SHIPROCKET_BASE}/orders/create/adhoc",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        data = resp.json()

        if resp.status_code in (200, 201) and data.get("shipment_id"):
            return {
                "success": True,
                "shipment_id": str(data.get("shipment_id", "")),
                "tracking_id": str(data.get("awb_code", "")),
                "message": "Shiprocket shipment created successfully.",
            }
        return {"success": False, "message": data.get("message", "Unknown error"), "shipment_id": None, "tracking_id": None}

    except Exception as e:
        return {"success": False, "message": str(e), "shipment_id": None, "tracking_id": None}


def get_tracking(tracking_id: str) -> dict:
    """Fetch live tracking status for a shipment."""
    try:
        resp = requests.get(
            f"{SHIPROCKET_BASE}/courier/track/awb/{tracking_id}",
            headers=_headers(),
            timeout=10,
        )
        data = resp.json()
        tracking = data.get("tracking_data", {})
        return {
            "success": True,
            "status": tracking.get("shipment_track", [{}])[0].get("current_status", "Unknown"),
            "raw": tracking,
        }
    except Exception as e:
        return {"success": False, "status": "Unknown", "message": str(e)}
