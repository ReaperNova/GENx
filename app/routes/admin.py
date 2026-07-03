import os
from datetime import datetime

from flask import (
    Blueprint, render_template, request, redirect,
    url_for, flash, current_app,
)
from flask_login import login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename

from app.extensions import db
from app.models import (
    AdminUser, Category, Product, ProductImage,
    Order, Coupon, Review,
)

admin_bp = Blueprint("admin", __name__)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_image(file):
    """Save uploaded file to UPLOAD_FOLDER and return the URL path."""
    upload_folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_folder, exist_ok=True)
    ext = file.filename.rsplit(".", 1)[-1].lower()
    filename = secure_filename(f"product_{datetime.utcnow().timestamp():.0f}_{file.filename}")
    file.save(os.path.join(upload_folder, filename))
    return f"/static/uploads/products/{filename}"


# ─── Settings helper ─────────────────────────────────────────────────────────

class _Settings:
    """Simple in-memory settings store (replace with DB row if needed)."""
    delivery_partner = os.getenv("DEFAULT_DELIVERY_PARTNER", "shiprocket")

_settings = _Settings()


# ─── Auth ────────────────────────────────────────────────────────────────────

@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        user = AdminUser.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid email or password.", "error")

    return render_template("admin/login.html")


@admin_bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


# ─── Dashboard ───────────────────────────────────────────────────────────────

@admin_bp.route("/")
@login_required
def dashboard():
    from sqlalchemy import func

    total_orders   = Order.query.count()
    total_revenue  = db.session.query(func.sum(Order.total_amount)).filter(Order.status != "cancelled").scalar() or 0
    pending_orders = Order.query.filter_by(status="pending").count()
    total_products = Product.query.filter_by(is_active=True).count()

    recent_orders = Order.query.order_by(Order.ordered_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        stats=type("s", (), {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "pending_orders": pending_orders,
            "total_products": total_products,
        })(),
        recent_orders=recent_orders,
        now=datetime.utcnow(),
    )


# ─── Categories ──────────────────────────────────────────────────────────────

@admin_bp.route("/categories")
@login_required
def categories():
    return render_template("admin/categories.html", categories=Category.query.all())


@admin_bp.route("/categories/add", methods=["POST"])
@login_required
def add_category():
    name = request.form.get("name", "").strip()
    slug = request.form.get("slug", "").strip().lower()
    if not name or not slug:
        flash("Name and slug are required.", "error")
        return redirect(url_for("admin.categories"))
    if Category.query.filter_by(slug=slug).first():
        flash("A category with that slug already exists.", "error")
        return redirect(url_for("admin.categories"))
    db.session.add(Category(name=name, slug=slug))
    db.session.commit()
    flash(f"Category '{name}' created.", "success")
    return redirect(url_for("admin.categories"))


@admin_bp.route("/categories/<int:cat_id>/delete", methods=["POST"])
@login_required
def delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    db.session.delete(cat)
    db.session.commit()
    flash(f"Category '{cat.name}' deleted.", "success")
    return redirect(url_for("admin.categories"))


# ─── Products ────────────────────────────────────────────────────────────────

@admin_bp.route("/products")
@login_required
def products():
    return render_template(
        "admin/products.html",
        products=Product.query.order_by(Product.id.desc()).all(),
    )


@admin_bp.route("/products/add", methods=["GET", "POST"])
@login_required
def add_product():
    categories = Category.query.all()
    if request.method == "POST":
        p = Product(
            name=request.form["name"].strip(),
            description=request.form.get("description", "").strip(),
            price=float(request.form["price"]),
            stock=int(request.form["stock"]),
            category_id=int(request.form["category_id"]),
            is_active=True,
        )
        db.session.add(p)
        db.session.flush()

        files = request.files.getlist("images")
        for i, f in enumerate(files):
            if f and f.filename and allowed_file(f.filename):
                url = save_image(f)
                db.session.add(ProductImage(
                    product_id=p.id,
                    image_url=url,
                    is_primary=(i == 0),
                ))

        db.session.commit()
        flash(f"Product '{p.name}' created.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", product=None, categories=categories)


@admin_bp.route("/products/<int:product_id>/edit", methods=["GET", "POST"])
@login_required
def edit_product(product_id):
    product    = Product.query.get_or_404(product_id)
    categories = Category.query.all()

    if request.method == "POST":
        product.name        = request.form["name"].strip()
        product.description = request.form.get("description", "").strip()
        product.price       = float(request.form["price"])
        product.stock       = int(request.form["stock"])
        product.category_id = int(request.form["category_id"])

        files = request.files.getlist("images")
        has_primary = any(img.is_primary for img in product.images)
        for i, f in enumerate(files):
            if f and f.filename and allowed_file(f.filename):
                url = save_image(f)
                db.session.add(ProductImage(
                    product_id=product.id,
                    image_url=url,
                    is_primary=(not has_primary and i == 0),
                ))
                has_primary = True

        db.session.commit()
        flash(f"Product '{product.name}' updated.", "success")
        return redirect(url_for("admin.products"))

    return render_template("admin/product_form.html", product=product, categories=categories)


@admin_bp.route("/products/<int:product_id>/toggle", methods=["POST"])
@login_required
def toggle_product(product_id):
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    flash(f"Product {'activated' if product.is_active else 'hidden'}.", "success")
    return redirect(request.referrer or url_for("admin.products"))


@admin_bp.route("/products/<int:product_id>/delete", methods=["POST"])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash(f"Product deleted.", "success")
    return redirect(url_for("admin.products"))


@admin_bp.route("/images/<int:image_id>/set-primary", methods=["POST"])
@login_required
def set_primary_image(image_id):
    img = ProductImage.query.get_or_404(image_id)
    # Clear existing primary
    ProductImage.query.filter_by(product_id=img.product_id).update({"is_primary": False})
    img.is_primary = True
    db.session.commit()
    flash("Primary image updated.", "success")
    return redirect(url_for("admin.edit_product", product_id=img.product_id))


@admin_bp.route("/images/<int:image_id>/delete", methods=["POST"])
@login_required
def delete_image(image_id):
    img = ProductImage.query.get_or_404(image_id)
    product_id = img.product_id
    db.session.delete(img)
    db.session.commit()
    flash("Image deleted.", "success")
    return redirect(url_for("admin.edit_product", product_id=product_id))


# ─── Orders ──────────────────────────────────────────────────────────────────

@admin_bp.route("/orders")
@login_required
def orders():
    status_filter = request.args.get("status", "all")
    query = Order.query.order_by(Order.ordered_at.desc())
    if status_filter != "all":
        query = query.filter_by(status=status_filter)
    return render_template(
        "admin/orders.html",
        orders=query.all(),
        status_filter=status_filter,
    )


@admin_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template(
        "admin/order_detail.html",
        order=order,
        available_partners=["shiprocket", "delhivery", "dtdc"],
    )


@admin_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
def update_order_status(order_id):
    order     = Order.query.get_or_404(order_id)
    new_status = request.form.get("status")
    partner    = request.form.get("delivery_partner", _settings.delivery_partner)

    if new_status == "picked_up" and order.status != "picked_up":
        try:
            api_key = current_app.config.get("FAST2SMS_API_KEY")
            if api_key and api_key != "your_fast2sms_api_key_here":
                import requests
                customer_phone = order.customer.phone
                msg = f"Good news! Your GenX order #{order.id} has been picked up! Track it here: {order.tracking_id or 'Soon'}"
                
                resp = requests.get("https://www.fast2sms.com/dev/bulkV2", params={
                    "authorization": api_key,
                    "message": msg,
                    "language": "english",
                    "route": "q",
                    "numbers": customer_phone
                })
                if resp.status_code == 200:
                    flash("SMS update pinged to customer successfully.", "success")
                else:
                    flash("SMS failed to send.", "warning")
        except Exception as e:
            flash(f"SMS error: {str(e)}", "warning")

    order.status = new_status

    # Auto-book pickup when status → "ready"
    if new_status == "ready" and not order.tracking_id:
        try:
            from app.delivery import get_delivery_partner
            dp = get_delivery_partner(partner)
            result = dp.book_pickup(order)
            if result["success"]:
                order.tracking_id    = result["tracking_id"]
                order.shipment_id    = result["shipment_id"]
                order.delivery_partner = partner
                flash(f"Pickup booked via {partner.title()}. Tracking: {result['tracking_id']}", "success")
            else:
                flash(f"Delivery booking failed: {result['message']}", "warning")
        except Exception as e:
            flash(f"Delivery error: {str(e)}", "warning")

    db.session.commit()
    flash(f"Order #{order_id} status updated to '{new_status}'.", "success")
    return redirect(url_for("admin.order_detail", order_id=order_id))


# ─── Coupons ─────────────────────────────────────────────────────────────────

@admin_bp.route("/coupons")
@login_required
def coupons():
    return render_template("admin/coupons.html", coupons=Coupon.query.order_by(Coupon.id.desc()).all())


@admin_bp.route("/coupons/add", methods=["POST"])
@login_required
def add_coupon():
    code           = request.form.get("code", "").upper().strip()
    discount_type  = request.form.get("discount_type")
    discount_value = float(request.form.get("discount_value", 0))
    min_order      = float(request.form.get("min_order_amount", 0))
    max_uses       = int(request.form.get("max_uses", 100))
    expires_raw    = request.form.get("expires_at", "")

    expires_at = None
    if expires_raw:
        try:
            expires_at = datetime.fromisoformat(expires_raw)
        except ValueError:
            pass

    if Coupon.query.filter_by(code=code).first():
        flash(f"Coupon '{code}' already exists.", "error")
        return redirect(url_for("admin.coupons"))

    c = Coupon(
        code=code,
        discount_type=discount_type,
        discount_value=discount_value,
        min_order_amount=min_order,
        max_uses=max_uses,
        expires_at=expires_at,
        is_active=True,
    )
    db.session.add(c)
    db.session.commit()
    flash(f"Coupon '{code}' created.", "success")
    return redirect(url_for("admin.coupons"))


@admin_bp.route("/coupons/<int:coupon_id>/toggle", methods=["POST"])
@login_required
def toggle_coupon(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    c.is_active = not c.is_active
    db.session.commit()
    flash(f"Coupon '{c.code}' {'enabled' if c.is_active else 'disabled'}.", "success")
    return redirect(url_for("admin.coupons"))


@admin_bp.route("/coupons/<int:coupon_id>/delete", methods=["POST"])
@login_required
def delete_coupon(coupon_id):
    c = Coupon.query.get_or_404(coupon_id)
    db.session.delete(c)
    db.session.commit()
    flash(f"Coupon '{c.code}' deleted.", "success")
    return redirect(url_for("admin.coupons"))


# ─── Reviews ─────────────────────────────────────────────────────────────────

@admin_bp.route("/reviews")
@login_required
def reviews_list():
    reviews = Review.query.order_by(Review.created_at.desc()).all()
    return render_template("admin/reviews.html", reviews=reviews)


@admin_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    r = Review.query.get_or_404(review_id)
    db.session.delete(r)
    db.session.commit()
    flash("Review deleted.", "success")
    return redirect(url_for("admin.reviews_list"))


# ─── Settings ────────────────────────────────────────────────────────────────

@admin_bp.route("/settings")
@login_required
def settings():
    return render_template("admin/settings.html", settings=_settings)


@admin_bp.route("/settings/save", methods=["POST"])
@login_required
def save_settings():
    _settings.delivery_partner = request.form.get("delivery_partner", "shiprocket")
    flash(f"Delivery partner set to {_settings.delivery_partner.title()}.", "success")
    return redirect(url_for("admin.settings"))
