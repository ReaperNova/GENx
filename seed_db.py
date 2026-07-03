"""
seed_db.py — Seeds the database with:
  - 4 categories
  - 8 sample products with placeholder images
  - Admin user (credentials from .env)
  - 3 test coupons

Run once: python seed_db.py
"""
import os
from datetime import datetime, timedelta
from app import create_app
from app.extensions import db
from app.models import Category, Product, ProductImage, Coupon, AdminUser

app = create_app()

PLACEHOLDER = "https://images.unsplash.com/photo-1620799140408-edc6dcb6d633?w=600&auto=format"

CATEGORIES = [
    ("Hoodies", "hoodies"),
    ("Tees",    "tees"),
    ("Pants",   "pants"),
    ("Accessories", "accessories"),
]

PRODUCTS = [
    # (name, desc, price, stock, category_slug, image_url, weight_kg)
    ("Drop Shoulder Hoodie",
     "Heavyweight 380gsm fleece. Oversized silhouette, kangaroo pocket. Built for the streets.",
     1499, 40, "hoodies",
     "/static/images/hoodie1.jpg", 0.6),

    ("Acid Wash Hoodie",
     "Vintage acid wash treatment, unique every piece. French terry lining.",
     1799, 25, "hoodies",
     "/static/images/hoodie2.jpg", 0.6),

    ("Graphic Tee — Logo Drop",
     "100% organic cotton. Screen-printed logo. Oversized fit.",
     699,  80, "tees",
     "/static/images/tee1.jpg", 0.3),

    ("Blank Tee — Urban Fit",
     "Boxy cut, 220gsm combed cotton. The perfect blank canvas.",
     599,  100, "tees",
     "/static/images/tee2.jpg", 0.3),

    ("Cargo Pants — Slate",
     "6-pocket cargo silhouette. Relaxed taper. Ripstop fabric.",
     1999, 30, "pants",
     "/static/images/pants1.jpg", 0.7),

    ("Track Pants — OG",
     "Tricot track pants with side stripe. Elastic waist + drawcord.",
     1299, 45, "pants",
     "/static/images/pants2.jpg", 0.5),

    ("5-Panel Cap — Black",
     "Structured 5-panel with embroidered logo. One size fits all.",
     499,  60, "accessories",
     "/static/images/cap.jpg", 0.2),

    ("Tote Bag — Street Edition",
     "Heavy canvas tote. Screen-printed. Holds your whole fit.",
     349,  75, "accessories",
     "/static/images/tote.jpg", 0.4),
]

COUPONS = [
    # (code, type, value, min_order, max_uses)
    ("GENX10",   "percent", 10,  0,   999),
    ("FIRST100", "flat",    100, 499, 100),
    ("VIRAR20",  "percent", 20,  999, 50),
]

with app.app_context():
    db.create_all()

    # Categories
    cat_map = {}
    for name, slug in CATEGORIES:
        existing = Category.query.filter_by(slug=slug).first()
        if not existing:
            cat = Category(name=name, slug=slug)
            db.session.add(cat)
            db.session.flush()
            cat_map[slug] = cat.id
            print(f"  ✓ Category: {name}")
        else:
            cat_map[slug] = existing.id

    # Products
    for name, desc, price, stock, cat_slug, img_url, weight_kg in PRODUCTS:
        if not Product.query.filter_by(name=name).first():
            p = Product(
                name=name,
                description=desc,
                price=price,
                stock=stock,
                category_id=cat_map[cat_slug],
                is_active=True,
                weight=weight_kg,
            )
            db.session.add(p)
            db.session.flush()
            db.session.add(ProductImage(product_id=p.id, image_url=img_url, is_primary=True))
            print(f"  ✓ Product: {name} ({weight_kg}kg)")

    # Coupons
    for code, dtype, value, min_order, max_uses in COUPONS:
        if not Coupon.query.filter_by(code=code).first():
            db.session.add(Coupon(
                code=code,
                discount_type=dtype,
                discount_value=value,
                min_order_amount=min_order,
                max_uses=max_uses,
                expires_at=datetime.utcnow() + timedelta(days=365),
                is_active=True,
            ))
            print(f"  ✓ Coupon: {code}")

    # Admin user
    admin_email = os.getenv("ADMIN_EMAIL", "admin@genx.com")
    admin_pass  = os.getenv("ADMIN_PASSWORD", "admin123")
    if not AdminUser.query.filter_by(email=admin_email).first():
        admin = AdminUser(email=admin_email, name="Admin")
        admin.set_password(admin_pass)
        db.session.add(admin)
        print(f"  ✓ Admin user: {admin_email}")

    db.session.commit()
    print("\n✅  Database seeded successfully!")
    print(f"   Admin login: {admin_email} / {admin_pass}")
    print("   Test coupons: GENX10, FIRST100, VIRAR20")
