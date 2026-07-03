from app.extensions import db
from datetime import datetime


class Coupon(db.Model):
    __tablename__ = "coupons"

    id               = db.Column(db.Integer, primary_key=True)
    code             = db.Column(db.String(50), unique=True, nullable=False)
    discount_type    = db.Column(db.String(10), nullable=False)   # "flat" | "percent"
    discount_value   = db.Column(db.Float, nullable=False)
    min_order_amount = db.Column(db.Float, default=0.0)
    max_uses         = db.Column(db.Integer, default=1)
    used_count       = db.Column(db.Integer, default=0)
    expires_at       = db.Column(db.DateTime, nullable=True)
    is_active        = db.Column(db.Boolean, default=True)

    orders = db.relationship("Order", backref="coupon", lazy="dynamic")

    def is_valid(self, cart_total: float) -> tuple[bool, str]:
        """Returns (is_valid, message)"""
        if not self.is_active:
            return False, "This coupon is inactive."
        if self.expires_at and datetime.utcnow() > self.expires_at:
            return False, "This coupon has expired."
        if self.used_count >= self.max_uses:
            return False, "This coupon has reached its usage limit."
        if cart_total < self.min_order_amount:
            return False, f"Minimum order amount ₹{self.min_order_amount:.0f} required."
        return True, "Valid"

    def calculate_discount(self, cart_total: float) -> float:
        if self.discount_type == "flat":
            return min(self.discount_value, cart_total)
        elif self.discount_type == "percent":
            return round(cart_total * (self.discount_value / 100), 2)
        return 0.0

    def __repr__(self):
        return f"<Coupon {self.code}>"
