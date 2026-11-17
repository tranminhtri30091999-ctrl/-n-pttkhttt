from flask import Blueprint, render_template

from modules.admin.routes import role_required

report_bp = Blueprint("report", __name__)


@report_bp.route("/bills.html")
@role_required("staff", "admin")
def bills_page():
    return render_template("staff/bills.html")


@report_bp.route("/dashboard.html")
@role_required("staff", "admin")
def dashboard_page():
    return render_template("staff/dashboard.html")
