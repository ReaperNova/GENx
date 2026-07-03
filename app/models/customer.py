from app.extensions import db
from datetime import datetime


class Customer(db.Model):
    __tablename__ = "customers"

    id         = db.Column(db.Integer, primary_key=True)
    name       = db.Column(db.String(150), nullable=False)
    email      = db.Column(db.String(200), unique=True, nullable=False)
    phone      = db.Column(db.String(20), nullable=True)
    address    = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    orders  = db.relationship("Order", backref="customer", lazy="dynamic")
    reviews = db.relationship("Review", backref="customer", lazy="dynamic")

    def __repr__(self):
        return f"<Customer {self.email}>"
