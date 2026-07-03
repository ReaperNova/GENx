# GENx — Gen Z Streetwear E-commerce Website

A full-stack e-commerce website built for a local Gen Z clothing brand based in Virar, Mumbai.

## Tech Stack
- **Backend:** Python Flask with Blueprints
- **Database:** SQLite via SQLAlchemy
- **Frontend:** Tailwind CSS, GSAP, Alpine.js
- **Payments:** Razorpay
- **Delivery:** Shiprocket, Delhivery, DTDC
- **Auth:** Flask-Login

## Features
- Product catalog with categories and multi-image upload
- Slide-in cart drawer
- Coupon engine (flat & percent discounts)
- Razorpay payment integration with webhook verification
- Order management (pending → paid → ready → picked up → delivered)
- Admin panel for products, orders, coupons, reviews
- Hidden test panel (auto-disables in production)

## Setup
1. Clone the repo
2. Create a `.env` file with your Razorpay and delivery API keys
3. Run `pip install -r requirements.txt`
4. Run `python seed_db.py`
5. Run `python run.py`
