"""
DTDC delivery partner integration — SANDBOX/TEST MODE
"""
import requests
from flask import current_app

DTDC_BASE = "https://apigateway-sandbox.dtdc.com/v1"


def _headers() -> dict:
    token = current_app.config.get("DTDC_TOKEN", "")
    api_key = current_app.config.get("DTDC_API_KEY", "")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
        "X-Api-Key": api_key,
    }


def book_pickup(order) -> dict:
    """Book pickup via DTDC sandbox API."""
    try:
        payload = {
            "consignee": {
                "name": order.customer.name,
                "address1": order.customer.address,
                "city": "Virar",
                "state": "Maharashtra",
                "pincode": "401303",
                "phone": order.customer.phone or "9999999999",
            },
            "shipper": {
                "name": "GenX Clothing",
                "address1": "Virar West",
                "city": "Virar",
                "state": "Maharashtra",
                "pincode": "401303",
                "phone": "9999999999",
            },
            "order_number": str(order.id),
            "product_type": "PPD",
            "declared_value": order.total_amount,
            "weight": 500,
            "pieces": sum(i.quantity for i in order.items),
            "description": ", ".join(i.product.name for i in order.items),
        }

        resp = requests.post(
            f"{DTDC_BASE}/shipment/create",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        data = resp.json()

        if resp.status_code in (200, 201) and data.get("awb_number"):
            return {
                "success": True,
                "shipment_id": data["awb_number"],
                "tracking_id": data["awb_number"],
                "message": "DTDC shipment created.",
            }
        return {"success": False, "message": str(data), "shipment_id": None, "tracking_id": None}

    except Exception as e:
        return {"success": False, "message": str(e), "shipment_id": None, "tracking_id": None}


def get_tracking(tracking_id: str) -> dict:
    """Track shipment via DTDC."""
    try:
        resp = requests.get(
            f"{DTDC_BASE}/shipment/track/{tracking_id}",
            headers=_headers(),
            timeout=10,
        )
        data = resp.json()
        return {
            "success": True,
            "status": data.get("status", "Unknown"),
            "raw": data,
        }
    except Exception as e:
        return {"success": False, "status": "Unknown", "message": str(e)}
