from flask import Blueprint, render_template, request, jsonify
from modules.order.services import get_all_orders, approve_order, cancel_order

order_bp = Blueprint('order', __name__)


# URL thực tế sẽ là: http://127.0.0.1:5000/staff/orders
@order_bp.route('/orders', methods=['GET'])
def staff_orders_page():
    raw_status = request.args.get('status')
    current_status = raw_status.lower() if raw_status else None
    orders = get_all_orders(current_status)
    return render_template('staff/orders.html', orders=orders, current_status=current_status)


# URL thực tế: /staff/api/orders
@order_bp.route('/api/orders', methods=['GET'])
def api_get_orders():
    raw_status = request.args.get('status')
    current_status = raw_status.lower() if raw_status else None
    orders = get_all_orders(current_status)
    return jsonify({"success": True, "data": orders}), 200


# URL thực tế: /staff/api/orders/<order_id>/approve
@order_bp.route('/api/orders/<int:order_id>/approve', methods=['POST'])
def api_approve_order(order_id):
    result = approve_order(order_id)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code


# URL thực tế: /staff/api/orders/<order_id>/cancel
@order_bp.route('/api/orders/<int:order_id>/cancel', methods=['POST'])
def api_cancel_order(order_id):
    result = cancel_order(order_id)
    status_code = 200 if result['success'] else 400
    return jsonify(result), status_code