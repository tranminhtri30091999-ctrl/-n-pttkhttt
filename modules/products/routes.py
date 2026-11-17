from flask import Blueprint, render_template

from modules.admin.routes import role_required

products_bp = Blueprint("products", __name__)


@products_bp.route("/products.html")
@role_required("staff", "admin")
def products_page():
    return render_template("staff/products.html")
