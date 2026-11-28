from flask import Blueprint, jsonify, render_template, request

from modules.admin.routes import role_required
from modules.report import services

report_bp = Blueprint("report", __name__)


@report_bp.route("/bills.html")
@role_required("staff", "admin")
def bills_page():
    return render_template("staff/bills.html", active_nav="bills")


@report_bp.route("/dashboard.html")
@role_required("staff", "admin")
def dashboard_page():
    return render_template("staff/dashboard.html", active_nav="dashboard")


@report_bp.route("/api/orders/<int:order_id>/invoice", methods=["POST"])
@role_required("staff", "admin")
def create_invoice(order_id):
    return jsonify(services.create_invoice(order_id))
