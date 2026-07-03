from flask import Blueprint, render_template, abort
from app.models import Order

orders_bp = Blueprint("orders", __name__)


@orders_bp.route("/confirmation/<int:order_id>")
def confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    if order.status not in ("paid", "ready", "picked_up", "delivered"):
        abort(403)
    return render_template("order_confirmation.html", order=order)
