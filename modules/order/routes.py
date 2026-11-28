import sqlite3

from flask import Blueprint, jsonify, render_template

from database.db_helper import get_db
from modules.admin.routes import role_required
from modules.order.services import transition_order_status

order_bp = Blueprint("order", __name__)


def transition_response(order_id, target_status):
    db = get_db()
    try:
        result, error = transition_order_status(db, order_id, target_status)
        if error == "not_found":
            return jsonify({"ok": False, "error": "Không tìm thấy đơn hàng."}), 404
        if error == "invalid_transition":
            return jsonify({"ok": False, "error": "Chỉ đơn đang chờ mới có thể được duyệt hoặc hủy."}), 409
        if error == "insufficient_stock":
            return jsonify({"ok": False, "error": "Tồn kho không đủ để duyệt đơn hàng."}), 409
        if error:
            return jsonify({"ok": False, "error": "Không thể cập nhật tồn kho cho đơn này."}), 409
        return jsonify({"ok": True, "order": result})
    except sqlite3.OperationalError:
        db.rollback()
        return jsonify({"ok": False, "error": "Cơ sở dữ liệu đang bận. Vui lòng thử lại."}), 503
    except Exception:
        db.rollback()
        return jsonify({"ok": False, "error": "Không thể cập nhật đơn hàng lúc này."}), 500
    finally:
        db.close()


@order_bp.route("/orders.html")
@role_required("staff", "admin")
def orders_page():
    return render_template("staff/orders.html")


@order_bp.route("/api/orders", methods=["GET"])
@role_required("staff", "admin")
def list_orders():
    db = get_db()
    try:
        orders = db.execute("SELECT o.id, o.status, o.total, o.created_at, o.customer_name, o.phone, o.delivery_address, u.username FROM orders o JOIN users u ON u.id = o.customer_id ORDER BY o.id DESC").fetchall()
        result = []
        for order in orders:
            items = db.execute("SELECT p.name, p.stock, oi.quantity, oi.price FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ? ORDER BY oi.id", (order["id"],)).fetchall()
            result.append({**dict(order), "items": [dict(item) for item in items]})
        return jsonify({"ok": True, "orders": result})
    except sqlite3.OperationalError:
        return jsonify({"ok": False, "error": "Không thể đọc danh sách đơn hàng."}), 503
    finally:
        db.close()


@order_bp.route("/api/orders/<int:order_id>/approve", methods=["POST"])
@role_required("staff", "admin")
def approve_order(order_id):
    return transition_response(order_id, "approved")


@order_bp.route("/api/orders/<int:order_id>/cancel", methods=["POST"])
@role_required("staff", "admin")
def cancel_order(order_id):
    return transition_response(order_id, "cancelled")
