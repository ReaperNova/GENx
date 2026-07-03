"""
Shiprocket Delivery Gateway — SANDBOX/TEST MODE
================================================
Shiprocket acts as the single delivery gateway, aggregating 25+ couriers
(Delhivery, BlueDart, Ekart, Ecom Express, DTDC, etc.) and automatically
selecting the cheapest available courier per order.

Docs: https://apidocs.shiprocket.in/
"""

import os
from datetime import datetime, timedelta

import requests
from flask import current_app

SHIPROCKET_BASE = "https://apiv2.shiprocket.in/v1/external"

# Module-level token cache — persists for the lifetime of the process
_token_cache: dict = {
    "token": None,
    "expires_at": None,  # datetime when token expires
}


# ─── Auth ────────────────────────────────────────────────────────────────────

def get_token() -> str:
    """
    Authenticate with Shiprocket and return a cached JWT token.
    Token is valid for 24 hours — automatically refreshed when expired.
    Reads SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD from app config.
    """
    now = datetime.utcnow()

    # Return cached token if still valid (with 5-minute buffer)
    if (
        _token_cache["token"]
        and _token_cache["expires_at"]
        and now < _token_cache["expires_at"] - timedelta(minutes=5)
    ):
        return _token_cache["token"]

    email    = current_app.config.get("SHIPROCKET_EMAIL", "")
    password = current_app.config.get("SHIPROCKET_PASSWORD", "")

    if not email or not password:
        raise ValueError("SHIPROCKET_EMAIL and SHIPROCKET_PASSWORD must be set in .env")

    resp = requests.post(
        f"{SHIPROCKET_BASE}/auth/login",
        json={"email": email, "password": password},
        timeout=10,
    )
    resp.raise_for_status()
    data  = resp.json()
    token = data.get("token", "")

    if not token:
        raise ValueError(f"Shiprocket login failed: {data.get('message', 'No token returned')}")

    _token_cache["token"]      = token
    _token_cache["expires_at"] = now + timedelta(hours=24)
    return token


def _headers() -> dict:
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {get_token()}",
    }


def _pickup_config() -> dict:
    """Return warehouse/pickup location config from app settings."""
    return {
        "pincode": current_app.config.get("SHIPROCKET_PICKUP_PINCODE", "401303"),
        "name":    current_app.config.get("SHIPROCKET_PICKUP_NAME", "GenX Store"),
        "address": current_app.config.get("SHIPROCKET_PICKUP_ADDRESS", "Virar West"),
        "city":    current_app.config.get("SHIPROCKET_PICKUP_CITY", "Virar"),
        "state":   current_app.config.get("SHIPROCKET_PICKUP_STATE", "Maharashtra"),
    }


# ─── Serviceability ──────────────────────────────────────────────────────────

def get_serviceable_couriers(
    pickup_pincode: str,
    delivery_pincode: str,
    weight: float,
    cod: bool = False,
) -> dict:
    """
    Fetch available couriers for a route from Shiprocket serviceability API.
    Returns a dict:
        {
            "success": bool,
            "couriers": [  # sorted cheapest first
                {"courier_id": int, "courier_name": str, "rate": float, "etd": str},
                ...
            ],
            "message": str,
        }
    """
    try:
        params = {
            "pickup_postcode":   pickup_pincode,
            "delivery_postcode": delivery_pincode,
            "weight":            weight,
            "cod":               1 if cod else 0,
        }
        resp = requests.get(
            f"{SHIPROCKET_BASE}/courier/serviceability/",
            headers=_headers(),
            params=params,
            timeout=12,
        )
        data = resp.json()

        raw_couriers = (
            data.get("data", {})
                .get("available_courier_companies", [])
        )

        if not raw_couriers:
            return {
                "success": False,
                "couriers": [],
                "message": data.get("message", "No couriers available for this route"),
            }

        couriers = [
            {
                "courier_id":   c.get("courier_company_id"),
                "courier_name": c.get("courier_name", "Unknown"),
                "rate":         float(c.get("rate", 0)),
                "etd":          c.get("etd", ""),
            }
            for c in raw_couriers
        ]
        couriers.sort(key=lambda x: x["rate"])

        return {"success": True, "couriers": couriers, "message": "OK"}

    except Exception as e:
        return {"success": False, "couriers": [], "message": str(e)}


# ─── Order Creation ──────────────────────────────────────────────────────────

def create_order(order) -> dict:
    """
    Create an order on Shiprocket with customer and product details.

    Returns:
        {
            "success": bool,
            "shiprocket_order_id": str,
            "shiprocket_shipment_id": str,
            "message": str,
        }
    """
    try:
        pickup = _pickup_config()

        # Calculate total weight: sum of (product.weight * quantity) per item
        # Default to 0.5 kg per item if product has no weight
        total_weight = sum(
            (item.product.weight if item.product.weight else 0.5) * item.quantity
            for item in order.items
        )
        total_weight = max(total_weight, 0.1)  # Shiprocket minimum 0.1 kg

        payload = {
            "order_id":    f"GENX-{order.id}",
            "order_date":  order.ordered_at.strftime("%Y-%m-%d %H:%M"),
            "pickup_location": pickup["name"],

            # Billing / customer details
            "billing_customer_name": order.customer.name,
            "billing_address":       order.customer.address or "N/A",
            "billing_city":          order.customer.city    or pickup["city"],
            "billing_pincode":       order.customer.pincode or pickup["pincode"],
            "billing_state":         order.customer.state   or pickup["state"],
            "billing_country":       "India",
            "billing_email":         order.customer.email,
            "billing_phone":         order.customer.phone or "9999999999",

            "shipping_is_billing": True,

            "order_items": [
                {
                    "name":          item.product.name,
                    "sku":           f"PROD-{item.product_id}",
                    "units":         item.quantity,
                    "selling_price": item.price_at_purchase,
                }
                for item in order.items
            ],

            "payment_method": "Prepaid",
            "sub_total":      order.subtotal,

            # Package dimensions (standard clothing box)
            "length":  30,
            "breadth": 20,
            "height":  5,
            "weight":  total_weight,
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
                "success":                True,
                "shiprocket_order_id":    str(data.get("order_id", "")),
                "shiprocket_shipment_id": str(data.get("shipment_id", "")),
                "message":               "Shiprocket order created successfully.",
            }

        return {
            "success":                False,
            "shiprocket_order_id":    None,
            "shiprocket_shipment_id": None,
            "message":               data.get("message", f"Shiprocket error (HTTP {resp.status_code})"),
        }

    except Exception as e:
        return {
            "success": False,
            "shiprocket_order_id": None,
            "shiprocket_shipment_id": None,
            "message": str(e),
        }


# ─── Courier Assignment ──────────────────────────────────────────────────────

def assign_cheapest_courier(
    shiprocket_order_id: str,
    shiprocket_shipment_id: str,
    pickup_pincode: str,
    delivery_pincode: str,
    weight: float,
) -> dict:
    """
    Automatically find and assign the cheapest available courier for a shipment.

    Steps:
      1. Calls get_serviceable_couriers() to rank couriers cheapest-first
      2. Assigns the cheapest courier to the Shiprocket shipment
      3. Returns AWB number, courier name, rate, and tracking URL

    Returns:
        {
            "success": bool,
            "awb_number": str,
            "courier_name": str,
            "courier_rate": float,
            "tracking_url": str,
            "message": str,
        }
    """
    try:
        # Step 1: Find cheapest courier
        svc = get_serviceable_couriers(pickup_pincode, delivery_pincode, weight)
        if not svc["success"] or not svc["couriers"]:
            return {
                "success":      False,
                "awb_number":   None,
                "courier_name": None,
                "courier_rate": None,
                "tracking_url": None,
                "message":      f"No couriers available: {svc['message']}",
            }

        cheapest = svc["couriers"][0]
        courier_id = cheapest["courier_id"]

        # Step 2: Assign courier to Shiprocket shipment
        resp = requests.post(
            f"{SHIPROCKET_BASE}/courier/assign/awb",
            json={
                "shipment_id": shiprocket_shipment_id,
                "courier_id":  str(courier_id),
            },
            headers=_headers(),
            timeout=15,
        )
        data = resp.json()

        awb = (
            data.get("response", {}).get("data", {}).get("awb_code")
            or data.get("awb_code")
        )

        if not awb:
            return {
                "success":      False,
                "awb_number":   None,
                "courier_name": None,
                "courier_rate": None,
                "tracking_url": None,
                "message":      data.get("message", "AWB assignment failed — no AWB returned"),
            }

        tracking_url = f"https://shiprocket.co/tracking/{awb}"

        return {
            "success":      True,
            "awb_number":   str(awb),
            "courier_name": cheapest["courier_name"],
            "courier_rate": cheapest["rate"],
            "tracking_url": tracking_url,
            "message":      f"Courier assigned: {cheapest['courier_name']} @ ₹{cheapest['rate']:.0f}",
        }

    except Exception as e:
        return {
            "success":      False,
            "awb_number":   None,
            "courier_name": None,
            "courier_rate": None,
            "tracking_url": None,
            "message":      str(e),
        }


# ─── Pickup Scheduling ───────────────────────────────────────────────────────

def book_pickup(shiprocket_shipment_id: str) -> dict:
    """
    Schedule a pickup from the warehouse for a Shiprocket shipment.

    Returns:
        {
            "success": bool,
            "pickup_scheduled": bool,
            "message": str,
        }
    """
    try:
        resp = requests.post(
            f"{SHIPROCKET_BASE}/courier/generate/pickup",
            json={"shipment_id": [int(shiprocket_shipment_id)]},
            headers=_headers(),
            timeout=15,
        )
        data = resp.json()

        # Shiprocket returns pickup_scheduled_message on success
        if resp.status_code in (200, 201) and (
            data.get("pickup_scheduled_message")
            or data.get("response", {}).get("pickup_scheduled_message")
        ):
            msg = (
                data.get("pickup_scheduled_message")
                or data.get("response", {}).get("pickup_scheduled_message", "Pickup scheduled.")
            )
            return {"success": True, "pickup_scheduled": True, "message": msg}

        return {
            "success":          False,
            "pickup_scheduled": False,
            "message":          data.get("message", f"Pickup scheduling failed (HTTP {resp.status_code})"),
        }

    except Exception as e:
        return {"success": False, "pickup_scheduled": False, "message": str(e)}


# ─── Live Tracking ───────────────────────────────────────────────────────────

def get_tracking(awb_number: str) -> dict:
    """
    Fetch live tracking status for a shipment via its AWB number.

    Returns:
        {
            "success": bool,
            "status": str,
            "current_location": str,
            "etd": str,
            "raw": dict,
            "message": str,
        }
    """
    try:
        resp = requests.get(
            f"{SHIPROCKET_BASE}/courier/track/awb/{awb_number}",
            headers=_headers(),
            timeout=10,
        )
        data     = resp.json()
        tracking = data.get("tracking_data", {})
        shipment_track = tracking.get("shipment_track", [{}])
        latest   = shipment_track[0] if shipment_track else {}

        return {
            "success":          True,
            "status":           latest.get("current_status", "Unknown"),
            "current_location": latest.get("current_location", ""),
            "etd":              latest.get("etd", ""),
            "raw":              tracking,
            "message":          "OK",
        }

    except Exception as e:
        return {
            "success":          False,
            "status":           "Unknown",
            "current_location": "",
            "etd":              "",
            "raw":              {},
            "message":          str(e),
        }


# ─── Connection Health Check ─────────────────────────────────────────────────

def check_connection() -> dict:
    """
    Ping Shiprocket to verify credentials are valid.
    Used by the admin settings page to show connection status.

    Returns:
        {"connected": bool, "message": str}
    """
    try:
        token = get_token()
        return {"connected": bool(token), "message": "Shiprocket API connected."}
    except Exception as e:
        return {"connected": False, "message": str(e)}
