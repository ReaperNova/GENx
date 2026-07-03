from app.extensions import db
from datetime import datetime


class Order(db.Model):
    __tablename__ = "orders"

    id              = db.Column(db.Integer, primary_key=True)
    customer_id     = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    coupon_id       = db.Column(db.Integer, db.ForeignKey("coupons.id"), nullable=True)
    payment_id      = db.Column(db.String(200), nullable=True)   # Razorpay payment_id
    razorpay_order_id = db.Column(db.String(200), nullable=True)  # Razorpay order_id
    status          = db.Column(db.String(20), default="pending")
    # status: pending | paid | ready | picked_up | delivered | cancelled
    subtotal        = db.Column(db.Float, nullable=False)
    discount_amount = db.Column(db.Float, default=0.0)
    total_amount    = db.Column(db.Float, nullable=False)
    ordered_at      = db.Column(db.DateTime, default=datetime.utcnow)
    delivery_partner = db.Column(db.String(50), nullable=True)
    tracking_id     = db.Column(db.String(200), nullable=True)
    shipment_id     = db.Column(db.String(200), nullable=True)

    # ── Shiprocket automated courier fields ───────────────────────────────────
    shiprocket_order_id    = db.Column(db.String(100), nullable=True)   # Shiprocket's order ID
    shiprocket_shipment_id = db.Column(db.String(100), nullable=True)   # Shiprocket's shipment ID
    awb_number             = db.Column(db.String(100), nullable=True)   # Courier AWB / tracking number
    courier_name           = db.Column(db.String(100), nullable=True)   # Courier Shiprocket assigned (e.g. "Delhivery")
    courier_rate           = db.Column(db.Float,       nullable=True)   # Shipment rate Shiprocket charged
    tracking_url           = db.Column(db.String(500), nullable=True)   # Full tracking URL for customer

    items = db.relationship("OrderItem", backref="order",
                            cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Order #{self.id} {self.status}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id                = db.Column(db.Integer, primary_key=True)
    order_id          = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id        = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    quantity          = db.Column(db.Integer, nullable=False)
    price_at_purchase = db.Column(db.Float, nullable=False)
    size              = db.Column(db.String(10), nullable=True)  # S/M/L/XL/XXL

    def __repr__(self):
        return f"<OrderItem order={self.order_id} product={self.product_id}>"
