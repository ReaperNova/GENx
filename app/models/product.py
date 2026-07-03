from app.extensions import db
from datetime import datetime


class Product(db.Model):
    __tablename__ = "products"

    id          = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    name        = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price       = db.Column(db.Float, nullable=False)
    stock       = db.Column(db.Integer, default=0)
    is_active   = db.Column(db.Boolean, default=True)

    images      = db.relationship("ProductImage", backref="product",
                                  cascade="all, delete-orphan", lazy="select")
    order_items = db.relationship("OrderItem", backref="product", lazy="dynamic")
    reviews     = db.relationship("Review", backref="product",
                                  cascade="all, delete-orphan", lazy="dynamic")

    @property
    def primary_image(self):
        img = ProductImage.query.filter_by(product_id=self.id, is_primary=True).first()
        if img:
            return img.image_url
        img = ProductImage.query.filter_by(product_id=self.id).first()
        return img.image_url if img else "/static/images/placeholder.jpg"

    @property
    def avg_rating(self):
        from sqlalchemy import func
        from app.extensions import db
        result = db.session.query(func.avg(Review.star_rating)).filter(
            Review.product_id == self.id).scalar()
        return round(float(result), 1) if result else 0.0

    @property
    def review_count(self):
        return self.reviews.count()

    def __repr__(self):
        return f"<Product {self.name}>"


from app.models.product_image import ProductImage  # noqa: E402
from app.models.review import Review               # noqa: E402
