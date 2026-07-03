from app.extensions import db
from datetime import datetime


class Review(db.Model):
    __tablename__ = "reviews"

    id          = db.Column(db.Integer, primary_key=True)
    product_id  = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey("customers.id"), nullable=False)
    star_rating = db.Column(db.Integer, nullable=False)   # 1–5
    review_text = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    images = db.relationship("ReviewImage", backref="review",
                             cascade="all, delete-orphan", lazy="select")

    def __repr__(self):
        return f"<Review product={self.product_id} stars={self.star_rating}>"
