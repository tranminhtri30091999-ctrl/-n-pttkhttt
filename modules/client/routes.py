from functools import wraps
import math
import re
import sqlite3

from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.security import generate_password_hash

from database.db_helper import get_db
from modules.order.services import transition_order_status

client_bp = Blueprint("client", __name__)


def customer_api_required():
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "Vui lòng đăng nhập để tiếp tục."}), 401
    if session.get("role") != "customer":
        return jsonify({"ok": False, "error": "Chỉ tài khoản khách hàng mới có thể thực hiện thao tác này."}), 403
    return None


def product_dict(row):
    return {"id": row["id"], "name": row["name"], "price": row["price"], "stock": row["stock"], "description": row["description"] or "", "category": row["category"] or "Khác"}


@client_bp.route("/")
def home():
    return render_template("client/index.html")


@client_bp.route("/client/index.html")
def index_page():
    return render_template("client/index.html")


@client_bp.route("/client/storeproduct.html")
def storeproduct_page():
    return render_template("client/storeproduct.html")


@client_bp.route("/client/product/<int:product_id>")
def product_page(product_id):
    return render_template("client/product.html", product_id=product_id)


@client_bp.route("/client/checkout.html")
def checkout_page():
    return render_template("client/checkout.html")


@client_bp.route("/client/orders.html")
def orders_page():
    return render_template("client/orders.html")


@client_bp.route("/client/login.html")
def login_page():
    return render_template("client/login.html")


@client_bp.route("/api/client/register", methods=["POST"])
def register_customer():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
        return jsonify({"ok": False, "error": "Tên đăng nhập cần dài 3–30 ký tự (chữ, số, ., _ hoặc -)."}), 400
    if len(password) < 8 or len(password) > 128:
        return jsonify({"ok": False, "error": "Mật khẩu cần dài từ 8 đến 128 ký tự."}), 400
    db = get_db()
    try:
        cursor = db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, 'customer')",
            (username, generate_password_hash(password)),
        )
        db.commit()
        session.clear()
        session["user_id"] = cursor.lastrowid
        session["username"] = username
        session["role"] = "customer"
        return jsonify({"ok": True, "user": {"id": cursor.lastrowid, "username": username, "role": "customer"}}), 201
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"ok": False, "error": "Tên đăng nhập đã được sử dụng."}), 409
    finally:
        db.close()


@client_bp.route("/api/products/categories")
def list_categories():
    db = get_db()
    try:
        rows = db.execute("SELECT DISTINCT category FROM products WHERE category IS NOT NULL AND TRIM(category) <> '' ORDER BY category COLLATE NOCASE").fetchall()
        return jsonify({"ok": True, "categories": [row["category"] for row in rows]})
    finally:
        db.close()


@client_bp.route("/api/products")
def list_products():
    query = (request.args.get("q") or "").strip()
    category = (request.args.get("category") or "").strip()
    try:
        min_price = float(request.args["min_price"]) if request.args.get("min_price") else None
        max_price = float(request.args["max_price"]) if request.args.get("max_price") else None
        if any(value is not None and (not math.isfinite(value) or value < 0) for value in (min_price, max_price)):
            raise ValueError
    except ValueError:
        return jsonify({"ok": False, "error": "Khoảng giá phải là số hợp lệ và không âm."}), 400
    if min_price is not None and max_price is not None and min_price > max_price:
        return jsonify({"ok": False, "error": "Giá từ phải nhỏ hơn hoặc bằng giá đến."}), 400

    clauses, params = [], []
    if query:
        clauses.append("name LIKE ?")
        params.append(f"%{query}%")
    if category:
        clauses.append("category = ?")
        params.append(category)
    if min_price is not None:
        clauses.append("price >= ?")
        params.append(min_price)
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)
    sql = "SELECT id, name, price, stock, description, category FROM products"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY category COLLATE NOCASE, name COLLATE NOCASE, id"
    db = get_db()
    try:
        rows = db.execute(sql, params).fetchall()
        return jsonify({"ok": True, "products": [product_dict(row) for row in rows]})
    finally:
        db.close()


@client_bp.route("/api/products/<int:product_id>")
def get_product(product_id):
    db = get_db()
    try:
        row = db.execute("SELECT id, name, price, stock, description, category FROM products WHERE id = ?", (product_id,)).fetchone()
        if row is None:
            return jsonify({"ok": False, "error": "Không tìm thấy sản phẩm."}), 404
        return jsonify({"ok": True, "product": product_dict(row)})
    finally:
        db.close()


@client_bp.route("/api/client/orders", methods=["GET"])
def list_customer_orders():
    auth_error = customer_api_required()
    if auth_error:
        return auth_error
    db = get_db()
    try:
        orders = db.execute("SELECT id, status, total, created_at, customer_name, phone, delivery_address FROM orders WHERE customer_id = ? ORDER BY id DESC", (session["user_id"],)).fetchall()
        result = []
        for order in orders:
            items = db.execute("SELECT oi.product_id, p.name, oi.quantity, oi.price FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ? ORDER BY oi.id", (order["id"],)).fetchall()
            result.append({**dict(order), "items": [dict(item) for item in items]})
        return jsonify({"ok": True, "orders": result})
    finally:
        db.close()


@client_bp.route("/api/client/orders", methods=["POST"])
def create_customer_order():
    auth_error = customer_api_required()
    if auth_error:
        return auth_error
    data = request.get_json(silent=True) or {}
    customer_name = (data.get("customer_name") or "").strip()
    phone = (data.get("phone") or "").strip()
    address = (data.get("delivery_address") or "").strip()
    items = data.get("items")
    if not customer_name or not phone or not address or len(customer_name) > 120 or len(phone) > 40 or len(address) > 500:
        return jsonify({"ok": False, "error": "Vui lòng nhập thông tin giao hàng hợp lệ."}), 400
    if not isinstance(items, list) or not items or len(items) > 50:
        return jsonify({"ok": False, "error": "Giỏ hàng đang trống hoặc có quá nhiều mặt hàng."}), 400
    quantities = {}
    try:
        for item in items:
            product_id, quantity = int(item.get("product_id")), int(item.get("quantity"))
            if product_id <= 0 or quantity <= 0 or quantity > 99:
                raise ValueError
            quantities[product_id] = quantities.get(product_id, 0) + quantity
            if quantities[product_id] > 99:
                raise ValueError
    except (AttributeError, TypeError, ValueError):
        return jsonify({"ok": False, "error": "Sản phẩm hoặc số lượng trong giỏ hàng không hợp lệ."}), 400

    db = get_db()
    try:
        db.execute("BEGIN IMMEDIATE")
        products = {}
        for product_id, quantity in quantities.items():
            product = db.execute("SELECT id, name, price, stock FROM products WHERE id = ?", (product_id,)).fetchone()
            if product is None or product["stock"] < quantity:
                db.rollback()
                return jsonify({"ok": False, "error": "Sản phẩm không tồn tại hoặc không đủ tồn kho. Hãy cập nhật giỏ hàng."}), 409
            products[product_id] = product
        total = sum(products[pid]["price"] * quantity for pid, quantity in quantities.items())
        cursor = db.execute("INSERT INTO orders (customer_id, status, total, customer_name, phone, delivery_address) VALUES (?, 'pending', ?, ?, ?, ?)", (session["user_id"], total, customer_name, phone, address))
        order_id = cursor.lastrowid
        for product_id, quantity in quantities.items():
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", (order_id, product_id, quantity, products[product_id]["price"]))
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (quantity, product_id, quantity))
            if db.execute("SELECT changes()").fetchone()[0] != 1:
                raise sqlite3.IntegrityError("stock changed")
        db.commit()
        return jsonify({"ok": True, "order_id": order_id, "total": total}), 201
    except sqlite3.OperationalError:
        db.rollback()
        return jsonify({"ok": False, "error": "Cơ sở dữ liệu đang bận. Vui lòng thử lại."}), 503
    except Exception:
        db.rollback()
        return jsonify({"ok": False, "error": "Không thể tạo đơn hàng lúc này. Vui lòng thử lại."}), 500
    finally:
        db.close()


@client_bp.route("/api/client/orders/<int:order_id>/cancel", methods=["POST"])
def cancel_customer_order(order_id):
    auth_error = customer_api_required()
    if auth_error:
        return auth_error
    db = get_db()
    try:
        result, error = transition_order_status(db, order_id, "cancelled", customer_id=session["user_id"])
        if error == "not_found":
            return jsonify({"ok": False, "error": "Không tìm thấy đơn hàng."}), 404
        if error == "invalid_transition":
            return jsonify({"ok": False, "error": "Chỉ đơn đang chờ mới có thể được khách hàng hủy."}), 409
        if error:
            return jsonify({"ok": False, "error": "Không thể hoàn kho cho đơn này."}), 409
        return jsonify({"ok": True, "order": result})
    except sqlite3.OperationalError:
        db.rollback()
        return jsonify({"ok": False, "error": "Cơ sở dữ liệu đang bận. Vui lòng thử lại."}), 503
    finally:
        db.close()
