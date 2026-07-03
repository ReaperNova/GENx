from flask import Blueprint, request, jsonify, session

cart_bp = Blueprint("cart", __name__)


@cart_bp.route("/count")
def cart_count():
    """Returns current cart item count (stored client-side, this is a stub)."""
    return jsonify({"count": 0})
