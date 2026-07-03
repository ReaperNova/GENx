import json
import hmac
import hashlib
from datetime import datetime

import razorpay
from flask import (
    Blueprint, render_template, request, jsonify,
    session, current_app, redirect, url_for, flash,
)

from app.extensions import db
from app.models import (
    Customer, Order, OrderItem, Coupon, Product,
)

checkout_bp = Blueprint("checkout", __name__)


def _razorpay_client():
    return razorpay.Client(
        auth=(
            current_app.config["RAZORPAY_KEY_ID"],
            current_app.config["RAZORPAY_KEY_SECRET"],
        )
    )


@checkout_bp.route("/")
def checkout():
    return render_template("checkout.html")


@checkout_bp.route("/apply-coupon", methods=["POST"])
def apply_coupon():
    """AJAX: validate coupon code against cart subtotal."""
    data = request.get_json()
    code = (data.get("code") or "").strip().upper()
    subtotal = float(data.get("subtotal", 0))

    coupon = Coupon.query.filter_by(code=code).first()
    if not coupon:
        return jsonify({"valid": False, "message": "Invalid coupon code."})

    valid, msg = coupon.is_valid(subtotal)
    if not valid:
        return jsonify({"valid": False, "message": msg})

    discount = coupon.calculate_discount(subtotal)
    new_total = round(subtotal - discount, 2)

    return jsonify({
        "valid": True,
        "message": f"🎉 Coupon applied! You save ₹{discount:,.0f}",
        "discount": discount,
        "new_total": new_total,
    })


@checkout_bp.route("/create-order", methods=["POST"])
def create_order():
    """Create a Razorpay order and save a pending Order in DB."""
    name      = request.form.get("name", "").strip()
    email     = request.form.get("email", "").strip()
    phone     = request.form.get("phone", "").strip()
    address   = request.form.get("address", "").strip()
    city      = request.form.get("city", "").strip()
    state     = request.form.get("state", "").strip()
    pincode   = request.form.get("pincode", "").strip()
    coupon_code = request.form.get("coupon_code", "").strip().upper()

    full_address = f"{address}, {city}, {state} - {pincode}"

    cart_items_raw = request.form.get("cart_items", "[]")
    try:
        cart_items = json.loads(cart_items_raw)
    except Exception:
        return jsonify({"error": "Invalid cart data."}), 400

    if not cart_items:
        return jsonify({"error": "Cart is empty."}), 400

    # Upsert customer
    customer = Customer.query.filter_by(email=email).first()
    if customer:
        customer.name = name
        customer.phone = phone
        customer.address = full_address
    else:
        customer = Customer(
            name=name, email=email, phone=phone, address=full_address
        )
        db.session.add(customer)
    db.session.flush()

    # Calculate subtotal from DB prices (always trust server, not client)
    subtotal = 0.0
    line_items = []
    for ci in cart_items:
        product = Product.query.get(ci.get("id"))
        if not product or not product.is_active:
            return jsonify({"error": f"Product #{ci.get('id')} is no longer available."}), 400
        qty = max(1, int(ci.get("quantity", 1)))
        line_items.append((product, qty, ci.get("size")))
        subtotal += product.price * qty

    # Apply coupon if any
    coupon = None
    discount_amount = 0.0
    if coupon_code:
        coupon = Coupon.query.filter_by(code=coupon_code).first()
        if coupon:
            valid, _ = coupon.is_valid(subtotal)
            if valid:
                discount_amount = coupon.calculate_discount(subtotal)

    total_amount = round(subtotal - discount_amount, 2)

    # Create Razorpay order
    try:
        client = _razorpay_client()
        rp_order = client.order.create({
            "amount": int(total_amount * 100),  # paise
            "currency": "INR",
            "receipt": f"genx_{datetime.utcnow().timestamp():.0f}",
        })
    except Exception as e:
        return jsonify({"error": f"Payment gateway error: {str(e)}"}), 500

    # Save pending order to DB
    order = Order(
        customer_id=customer.id,
        coupon_id=coupon.id if coupon else None,
        razorpay_order_id=rp_order["id"],
        status="pending",
        subtotal=subtotal,
        discount_amount=discount_amount,
        total_amount=total_amount,
    )
    db.session.add(order)
    db.session.flush()

    for product, qty, size in line_items:
        oi = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantity=qty,
            price_at_purchase=product.price,
            size=size,
        )
        db.session.add(oi)
        # Decrement stock
        product.stock = max(0, product.stock - qty)

    db.session.commit()
    session["customer_id"] = customer.id

    return jsonify({
        "razorpay_order_id": rp_order["id"],
        "razorpay_key": current_app.config["RAZORPAY_KEY_ID"],
        "amount": rp_order["amount"],
        "order_id": order.id,
        "brand_name": current_app.config.get("BRAND_NAME", "GenX"),
    })


@checkout_bp.route("/verify", methods=["POST"])
def verify_payment():
    """Verify Razorpay HMAC signature and mark order as paid."""
    data = request.get_json()

    payment_id   = data.get("razorpay_payment_id", "")
    rp_order_id  = data.get("razorpay_order_id", "")
    signature    = data.get("razorpay_signature", "")
    order_id     = data.get("internal_order_id")

    # HMAC verification
    body = f"{rp_order_id}|{payment_id}"
    secret = current_app.config["RAZORPAY_KEY_SECRET"].encode()
    expected = hmac.new(secret, body.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(expected, signature):
        return jsonify({"success": False, "error": "Signature mismatch"}), 400

    order = Order.query.get(order_id)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404

    order.payment_id = payment_id
    order.status = "paid"

    # Increment coupon usage
    if order.coupon_id:
        coupon = Coupon.query.get(order.coupon_id)
        if coupon:
            coupon.used_count += 1

    db.session.commit()

    return jsonify({"success": True, "order_id": order.id})


@checkout_bp.route("/webhook", methods=["POST"])
def razorpay_webhook():
    """Razorpay webhook endpoint for payment.captured events."""
    payload   = request.data
    signature = request.headers.get("X-Razorpay-Signature", "")
    secret    = current_app.config["RAZORPAY_KEY_SECRET"].encode()

    expected = hmac.new(secret, payload, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        return "Invalid signature", 400

    event = request.get_json(force=True)
    if event.get("event") == "payment.captured":
        rp_order_id = event["payload"]["payment"]["entity"]["order_id"]
        payment_id  = event["payload"]["payment"]["entity"]["id"]

        order = Order.query.filter_by(razorpay_order_id=rp_order_id).first()
        if order and order.status == "pending":
            order.status = "paid"
            order.payment_id = payment_id
            if order.coupon_id:
                coupon = Coupon.query.get(order.coupon_id)
                if coupon:
                    coupon.used_count += 1
            db.session.commit()

    return "OK", 200
