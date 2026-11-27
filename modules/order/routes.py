from flask import Blueprint, jsonify, render_template, request

from modules.admin.routes import role_required
from modules.order import services

order_bp = Blueprint("order", __name__)


@order_bp.route("/orders.html")
@role_required("staff", "admin")
def orders_page():
    return render_template("staff/orders.html", active_nav="orders")


@order_bp.route("/api/orders", methods=["GET"])
@role_required("staff", "admin")
def list_orders():
    result = services.list_orders(
        search=request.args.get("search", ""),
        date_from=request.args.get("from", ""),
        date_to=request.args.get("to", ""),
    )
    return jsonify(result)


@order_bp.route("/api/orders/<int:order_id>/approve", methods=["POST"])
@role_required("staff", "admin")
def approve_order(order_id):
    return jsonify(services.approve_order(order_id))


@order_bp.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
@role_required("staff", "admin")
def cancel_order(order_id):
    return jsonify(services.cancel_order(order_id))
