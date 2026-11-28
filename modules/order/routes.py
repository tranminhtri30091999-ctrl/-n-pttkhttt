from flask import Blueprint, jsonify, render_template, request

from flask import Blueprint, jsonify, render_template

from database.db_helper import get_db
from modules.admin.routes import role_required
from modules.order import services

order_bp = Blueprint("order", __name__)


def transition_response(order_id, target_status):
    db = get_db()
    try:
        result, error = transition_order_status(db, order_id, target_status)
        if error == "not_found":
            return jsonify({"ok": False, "error": "Không tìm thấy đơn hàng."}), 404
        if error == "invalid_transition":
            return jsonify({"ok": False, "error": "Chỉ đơn đang chờ mới có thể được duyệt hoặc hủy."}), 409
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
