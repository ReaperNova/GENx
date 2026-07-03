# GENx — Gen Z Streetwear E-commerce Website

A full-stack e-commerce website built for a local Gen Z clothing brand based in Virar, Mumbai.

## Tech Stack
- **Backend:** Python Flask with Blueprints
- **Database:** SQLite via SQLAlchemy + Flask-Migrate
- **Frontend:** Tailwind CSS, GSAP, Alpine.js
- **Payments:** Razorpay (webhook verified)
- **Delivery:** Shiprocket (automated courier selection)
- **Auth:** Flask-Login

## Features
- Premium dark-mode Gen Z design with GSAP animations
- Product catalog with categories and multi-image upload
- Slide-in cart drawer with live quantity updates
- Coupon engine (flat & percent discounts, expiry, usage limits)
- Razorpay payment integration with webhook signature verification
- Smart delivery — Shiprocket auto-selects cheapest courier per order
- Order management (pending → paid → ready → picked up → delivered)
- Admin panel for products, orders, coupons, categories, reviews
- Reviews system with star ratings and photo uploads
- Hidden test panel (auto-disables in production via FLASK_ENV)
- All credentials in .env — owner swaps test/live keys without touching code

## Setup
1. Clone the repo
2. Create `.env` file with Razorpay and Shiprocket credentials
3. Run `pip install -r requirements.txt`
4. Run `python seed_db.py`
5. Run `python run.py`
6. Visit `http://localhost:5002`
