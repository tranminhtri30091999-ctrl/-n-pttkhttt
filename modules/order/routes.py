from flask import Blueprint, render_template

from modules.admin.routes import role_required

order_bp = Blueprint("order", __name__)


@order_bp.route("/orders.html")
@role_required("staff", "admin")
def orders_page():
    return render_template("staff/orders.html")
