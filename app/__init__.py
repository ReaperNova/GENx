import os
from flask import Flask, render_template
from config import config, BRAND_NAME, BRAND_TAGLINE, BRAND_CITY
from app.extensions import db, login_manager


def create_app(config_name: str = None):
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    app = Flask(__name__)
    app.config.from_object(config.get(config_name, config["default"]))

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # ──────────────────────────────────────
    #  Context processor — injects brand info
    #  into EVERY template automatically
    # ──────────────────────────────────────
    @app.context_processor
    def inject_brand():
        return {
            "BRAND_NAME": BRAND_NAME,
            "BRAND_TAGLINE": BRAND_TAGLINE,
            "BRAND_CITY": BRAND_CITY,
            "RAZORPAY_KEY_ID": app.config.get("RAZORPAY_KEY_ID", ""),
        }

    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.cart import cart_bp
    from app.routes.checkout import checkout_bp
    from app.routes.orders import orders_bp
    from app.routes.admin import admin_bp
    from app.routes.test_panel import test_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(cart_bp, url_prefix="/cart")
    app.register_blueprint(checkout_bp, url_prefix="/checkout")
    app.register_blueprint(orders_bp, url_prefix="/orders")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(test_bp)

    # Create tables
    with app.app_context():
        db.create_all()

    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("500.html"), 500

    return app
