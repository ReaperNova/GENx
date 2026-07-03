from flask import Blueprint, render_template, request, jsonify, session, current_app
from flask_login import login_required
from app.extensions import db
from app.models import Product, Customer, Order, OrderItem, Coupon

test_bp = Blueprint("test", __name__, url_prefix="/admin/test")


@test_bp.route("/")
@login_required
def test_panel():
    products = Product.query.filter_by(is_active=True).limit(6).all()
    coupons  = Coupon.query.filter_by(is_active=True).all()
    orders   = Order.query.order_by(Order.id.desc()).limit(10).all()
    return render_template("test_panel.html", products=products, coupons=coupons, orders=orders)


@test_bp.route("/simulate-order", methods=["POST"])
@login_required
def simulate_order():
    """Create a fully paid order without Razorpay — for demo only."""
    data       = request.get_json()
    product_id = data.get("product_id")
    quantity   = int(data.get("quantity", 1))
    size       = data.get("size", "M")

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"success": False, "error": "Product not found"}), 404

    customer = Customer.query.filter_by(email="test@genx.com").first()
    if not customer:
        customer = Customer(
            name="Test Customer",
            email="test@genx.com",
            phone="9999999999",
            address="123 Test Street, Virar West, Mumbai - 401303",
        )
        db.session.add(customer)
        db.session.flush()

    session["customer_id"] = customer.id

    subtotal = product.price * quantity
    order = Order(
        customer_id=customer.id,
        status="paid",
        subtotal=subtotal,
        discount_amount=0,
        total_amount=subtotal,
        payment_id="test_payment_sim",
        razorpay_order_id="test_rp_order_sim",
    )
    db.session.add(order)
    db.session.flush()

    db.session.add(OrderItem(
        order_id=order.id,
        product_id=product.id,
        quantity=quantity,
        price_at_purchase=product.price,
        size=size,
    ))

    product.stock = max(0, product.stock - quantity)
    db.session.commit()

    return jsonify({
        "success": True,
        "order_id": order.id,
        "redirect": f"/orders/confirmation/{order.id}",
    })


@test_bp.route("/advance-status", methods=["POST"])
@login_required
def advance_status():
    """Advance an order through the status pipeline — for demo."""
    pipeline = ["pending", "paid", "ready", "picked_up", "delivered"]
    data     = request.get_json()
    order    = Order.query.get(data.get("order_id"))

    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404

    try:
        idx = pipeline.index(order.status)
        if idx < len(pipeline) - 1:
            order.status = pipeline[idx + 1]
            
            # Simulated Shiprocket trigger
            if order.status == "ready" and not order.tracking_id:
                try:
                    from app.delivery import get_delivery_partner
                    partner_name = current_app.config.get("DEFAULT_DELIVERY_PARTNER", "shiprocket")
                    dp = get_delivery_partner(partner_name)
                    res = dp.book_pickup(order)
                    if res["success"]:
                        order.tracking_id = res["tracking_id"]
                        order.shipment_id = res["shipment_id"]
                        order.delivery_partner = partner_name
                except Exception:
                    pass
            
            db.session.commit()
            return jsonify({"success": True, "new_status": order.status})
        return jsonify({"success": False, "error": "Already at final status"})
    except ValueError:
        return jsonify({"success": False, "error": "Unknown status"}), 400
