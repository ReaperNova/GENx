from app.extensions import db


class ProductImage(db.Model):
    __tablename__ = "product_images"

    id         = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    image_url  = db.Column(db.String(500), nullable=False)
    is_primary = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<ProductImage product={self.product_id} primary={self.is_primary}>"
