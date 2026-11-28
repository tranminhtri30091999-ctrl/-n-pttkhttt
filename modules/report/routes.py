from datetime import datetime
import sqlite3

from flask import Blueprint, jsonify, render_template, request

from modules.admin.routes import role_required
from database.db_helper import get_db

report_bp = Blueprint("report", __name__)


@report_bp.route("/bills.html")
@role_required("staff", "admin")
def bills_page():
    return render_template("staff/bills.html")


@report_bp.route("/dashboard.html")
@role_required("staff", "admin")
def dashboard_page():
    return render_template("staff/dashboard.html")


@report_bp.route("/index.html")
@role_required("staff", "admin")
def staff_index_page():
    return render_template("staff/dashboard.html")


def date_filter(prefix="o"):
    from_date = (request.args.get("from") or "").strip()
    to_date = (request.args.get("to") or "").strip()
    clauses = []
    params = []
    for value, operator in ((from_date, ">="), (to_date, "<=")):
        if not value:
            continue
        try:
            datetime.strptime(value, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Ngày lọc phải theo định dạng YYYY-MM-DD.")
        column = f"{prefix}.created_at"
        if operator == ">=":
            clauses.append(f"date({column}) >= date(?)")
        else:
            clauses.append(f"date({column}) <= date(?)")
        params.append(value)
    return clauses, params


@report_bp.route("/api/report", methods=["GET"])
@role_required("staff", "admin")
def report_summary():
    db = get_db()
    try:
        clauses, params = date_filter()
        where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
        total_revenue = db.execute(f"SELECT COALESCE(SUM(total), 0) AS value FROM orders o{where} AND o.status = 'approved'" if where else "SELECT COALESCE(SUM(total), 0) AS value FROM orders o WHERE o.status = 'approved'", params).fetchone()["value"]
        approved = db.execute(f"SELECT COUNT(*) FROM orders o{where} AND o.status = 'approved'" if where else "SELECT COUNT(*) FROM orders o WHERE o.status = 'approved'", params).fetchone()[0]
        cancelled = db.execute(f"SELECT COUNT(*) FROM orders o{where} AND o.status = 'cancelled'" if where else "SELECT COUNT(*) FROM orders o WHERE o.status = 'cancelled'", params).fetchone()[0]
        pending = db.execute(f"SELECT COUNT(*) FROM orders o{where} AND o.status = 'pending'" if where else "SELECT COUNT(*) FROM orders o WHERE o.status = 'pending'", params).fetchone()[0]
        return jsonify({"ok": True, "summary": {"revenue": total_revenue, "approved": approved, "cancelled": cancelled, "pending": pending}})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except sqlite3.OperationalError:
        return jsonify({"ok": False, "error": "Không thể thống kê dữ liệu."}), 503
    finally:
        db.close()


@report_bp.route("/api/invoices", methods=["GET"])
@role_required("staff", "admin")
def list_invoices():
    db = get_db()
    try:
        clauses, params = date_filter()
        where = (" AND " + " AND ".join(clauses)) if clauses else ""
        rows = db.execute(
            """SELECT o.id, o.status, o.total, o.customer_name, o.phone, o.delivery_address,
                      o.created_at, u.username
               FROM orders o JOIN users u ON u.id = o.customer_id
               WHERE o.status = 'approved'""" + where + " ORDER BY o.id DESC",
            params,
        ).fetchall()
        result = []
        for order in rows:
            items = db.execute("SELECT p.name, oi.quantity, oi.price FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ? ORDER BY oi.id", (order["id"],)).fetchall()
            result.append({**dict(order), "items": [dict(item) for item in items]})
            db.execute("INSERT OR IGNORE INTO invoices (order_id) VALUES (?)", (order["id"],))
        db.commit()
        return jsonify({"ok": True, "invoices": result})
    except ValueError as exc:
        return jsonify({"ok": False, "error": str(exc)}), 400
    except sqlite3.OperationalError:
        return jsonify({"ok": False, "error": "Không thể tải hóa đơn."}), 503
    finally:
        db.close()
