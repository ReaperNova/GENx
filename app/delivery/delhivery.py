"""
Delhivery delivery partner integration — SANDBOX/TEST MODE
Docs: https://developers.delhivery.com/
"""
import requests
from flask import current_app

DELHIVERY_BASE = "https://staging-express.delhivery.com"  # sandbox URL


def _headers() -> dict:
    token = current_app.config.get("DELHIVERY_TOKEN", "")
    return {
        "Content-Type": "application/json",
        "Authorization": f"Token {token}",
    }


def book_pickup(order) -> dict:
    """Create a waybill and request pickup via Delhivery."""
    try:
        payload = {
            "format": "json",
            "data": {
                "shipments": [
                    {
                        "name": order.customer.name,
                        "add": order.customer.address,
                        "city": "Virar",
                        "state": "Maharashtra",
                        "country": "India",
                        "pin": "401303",
                        "phone": order.customer.phone or "9999999999",
                        "order": str(order.id),
                        "payment_mode": "Prepaid",
                        "return_pin": "401303",
                        "return_city": "Virar",
                        "return_phone": "9999999999",
                        "return_add": "GenX HQ, Virar West, Mumbai",
                        "return_state": "Maharashtra",
                        "return_country": "India",
                        "products_desc": ", ".join(i.product.name for i in order.items),
                        "hsn_code": "",
                        "cod_amount": "0",
                        "order_date": order.ordered_at.strftime("%Y-%m-%d %H:%M:%S"),
                        "total_amount": str(order.total_amount),
                        "seller_add": "Virar West, Mumbai",
                        "seller_name": "GenX",
                        "seller_inv": str(order.id),
                        "quantity": str(sum(i.quantity for i in order.items)),
                        "shipment_width": "20",
                        "shipment_height": "10",
                        "weight": "500",
                        "seller_gst_tin": "",
                        "shipping_mode": "Surface",
                        "address_type": "home",
                    }
                ],
                "pickup_location": {
                    "name": "GenX Primary",
                    "add": "Virar West",
                    "city": "Virar",
                    "state": "Maharashtra",
                    "country": "India",
                    "pin_code": "401303",
                    "phone": "9999999999",
                },
            },
        }

        resp = requests.post(
            f"{DELHIVERY_BASE}/api/cmu/create.json",
            json=payload,
            headers=_headers(),
            timeout=15,
        )
        data = resp.json()
        packages = data.get("packages", [])

        if packages and packages[0].get("waybill"):
            return {
                "success": True,
                "shipment_id": packages[0]["waybill"],
                "tracking_id": packages[0]["waybill"],
                "message": "Delhivery shipment created.",
            }
        return {"success": False, "message": str(data), "shipment_id": None, "tracking_id": None}

    except Exception as e:
        return {"success": False, "message": str(e), "shipment_id": None, "tracking_id": None}


def get_tracking(tracking_id: str) -> dict:
    """Track shipment via Delhivery."""
    try:
        resp = requests.get(
            f"{DELHIVERY_BASE}/api/v1/packages/json/?waybill={tracking_id}",
            headers=_headers(),
            timeout=10,
        )
        data = resp.json()
        shipments = data.get("ShipmentData", [])
        status = shipments[0]["Shipment"]["Status"]["Status"] if shipments else "Unknown"
        return {"success": True, "status": status, "raw": data}
    except Exception as e:
        return {"success": False, "status": "Unknown", "message": str(e)}
