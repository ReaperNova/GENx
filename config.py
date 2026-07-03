import os
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  BRAND — change BRAND_NAME in .env to update
#  the name everywhere on the site.
# ─────────────────────────────────────────────
BRAND_NAME = os.getenv("BRAND_NAME", "GenX")
BRAND_TAGLINE = "Drop The Ordinary."
BRAND_CITY = "Virar, Mumbai"

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///genx.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Razorpay (TEST MODE)
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")

    # Shiprocket — single delivery gateway (aggregates 25+ couriers automatically)
    SHIPROCKET_EMAIL    = os.getenv("SHIPROCKET_EMAIL", "")
    SHIPROCKET_PASSWORD = os.getenv("SHIPROCKET_PASSWORD", "")

    # Shiprocket pickup / warehouse location
    SHIPROCKET_PICKUP_PINCODE = os.getenv("SHIPROCKET_PICKUP_PINCODE", "401303")
    SHIPROCKET_PICKUP_NAME    = os.getenv("SHIPROCKET_PICKUP_NAME",    "GenX Store")
    SHIPROCKET_PICKUP_ADDRESS = os.getenv("SHIPROCKET_PICKUP_ADDRESS", "Virar West")
    SHIPROCKET_PICKUP_CITY    = os.getenv("SHIPROCKET_PICKUP_CITY",    "Virar")
    SHIPROCKET_PICKUP_STATE   = os.getenv("SHIPROCKET_PICKUP_STATE",   "Maharashtra")

    # SMS Notifications
    FAST2SMS_API_KEY = os.getenv("FAST2SMS_API_KEY", "")

    # Admin
    ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@genx.com")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")

    # File uploads
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "app", "static", "uploads", "products")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

    # Delivery is fully automated via Shiprocket — no manual partner selection needed

    # Brand info passed to all templates
    BRAND_NAME = BRAND_NAME
    BRAND_TAGLINE = BRAND_TAGLINE
    BRAND_CITY = BRAND_CITY


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
