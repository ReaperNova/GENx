from app.extensions import db


class ReviewImage(db.Model):
    __tablename__ = "review_images"

    id        = db.Column(db.Integer, primary_key=True)
    review_id = db.Column(db.Integer, db.ForeignKey("reviews.id"), nullable=False)
    image_url = db.Column(db.String(500), nullable=False)

    def __repr__(self):
        return f"<ReviewImage review={self.review_id}>"
