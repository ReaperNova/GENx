from flask import Blueprint, render_template, request, jsonify
from app.extensions import db
from app.models import Category, Product, Review, OrderItem, Order

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    categories = Category.query.all()
    new_arrivals = (
        Product.query
        .filter_by(is_active=True)
        .order_by(Product.id.desc())
        .limit(8)
        .all()
    )
    return render_template("index.html", categories=categories, new_arrivals=new_arrivals)


@main_bp.route("/shop")
def shop():
    categories = Category.query.all()
    active_category = request.args.get("category", "")

    query = Product.query.filter_by(is_active=True)
    if active_category:
        cat = Category.query.filter_by(slug=active_category).first()
        if cat:
            query = query.filter_by(category_id=cat.id)

    products = query.order_by(Product.id.desc()).all()
    total_products = Product.query.filter_by(is_active=True).count()

    return render_template(
        "shop.html",
        products=products,
        categories=categories,
        active_category=active_category,
        total_products=total_products,
    )


@main_bp.route("/shop/products")
def shop_products_ajax():
    """AJAX endpoint — returns product card HTML fragment."""
    active_category = request.args.get("category", "")
    query = Product.query.filter_by(is_active=True)

    if active_category:
        cat = Category.query.filter_by(slug=active_category).first()
        if cat:
            query = query.filter_by(category_id=cat.id)
        else:
            query = query.filter(False)  # empty result

    products = query.order_by(Product.id.desc()).all()
    return render_template("partials/product_cards.html", products=products)


@main_bp.route("/product/<int:product_id>")
def product_detail(product_id):
    from flask import session
    product = Product.query.get_or_404(product_id)
    reviews = Review.query.filter_by(product_id=product_id).order_by(Review.created_at.desc()).all()

    # Check if current session customer can review
    can_review = False
    customer_id = session.get("customer_id")
    if customer_id:
        # Has a delivered order containing this product and hasn't already reviewed
        delivered_item = (
            db.session.query(OrderItem)
            .join(Order)
            .filter(
                Order.customer_id == customer_id,
                Order.status == "delivered",
                OrderItem.product_id == product_id,
            )
            .first()
        )
        already_reviewed = Review.query.filter_by(
            product_id=product_id, customer_id=customer_id
        ).first()
        can_review = bool(delivered_item) and not already_reviewed

    return render_template(
        "product.html",
        product=product,
        reviews=reviews,
        can_review=can_review,
    )


@main_bp.route("/product/<int:product_id>/review", methods=["POST"])
def submit_review(product_id):
    from flask import session, redirect, url_for, flash, request
    import os
    from werkzeug.utils import secure_filename
    from app.models import ReviewImage, Customer
    from config import Config

    customer_id = session.get("customer_id")
    if not customer_id:
        flash("Please complete a purchase to leave a review.", "error")
        return redirect(url_for("main.product_detail", product_id=product_id))

    # Eligibility check
    delivered_item = (
        db.session.query(OrderItem)
        .join(Order)
        .filter(
            Order.customer_id == customer_id,
            Order.status == "delivered",
            OrderItem.product_id == product_id,
        )
        .first()
    )
    if not delivered_item:
        flash("Only verified purchasers can review.", "error")
        return redirect(url_for("main.product_detail", product_id=product_id))

    already = Review.query.filter_by(product_id=product_id, customer_id=customer_id).first()
    if already:
        flash("You have already reviewed this product.", "warning")
        return redirect(url_for("main.product_detail", product_id=product_id))

    star_rating = int(request.form.get("star_rating", 5))
    review_text = request.form.get("review_text", "").strip()

    review = Review(
        product_id=product_id,
        customer_id=customer_id,
        star_rating=max(1, min(5, star_rating)),
        review_text=review_text,
    )
    db.session.add(review)
    db.session.flush()  # get review.id

    # Handle uploaded images (up to 5)
    images = request.files.getlist("images")
    upload_folder = Config.UPLOAD_FOLDER
    os.makedirs(upload_folder, exist_ok=True)

    for i, img_file in enumerate(images[:5]):
        if img_file and img_file.filename:
            ext = img_file.filename.rsplit(".", 1)[-1].lower()
            if ext in Config.ALLOWED_EXTENSIONS:
                filename = secure_filename(f"review_{review.id}_{i}.{ext}")
                img_file.save(os.path.join(upload_folder, filename))
                ri = ReviewImage(
                    review_id=review.id,
                    image_url=f"/static/uploads/products/{filename}",
                )
                db.session.add(ri)

    db.session.commit()
    flash("Review submitted successfully!", "success")
    return redirect(url_for("main.product_detail", product_id=product_id) + "#reviews")
