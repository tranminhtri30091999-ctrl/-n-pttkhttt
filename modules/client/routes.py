import math
import re
import sqlite3
from functools import wraps

from flask import Blueprint, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from database.db_helper import get_db
from modules.order.services import transition_order_status

client_bp = Blueprint("client", __name__)
PHONE_RE = re.compile(r"^0\d{9}$")
NAME_RE = re.compile(r"^[^\W\d_][\wÀ-ỹ'’.-]*(?:\s+[^\W\d_][\wÀ-ỹ'’.-]*)+$", re.UNICODE)
SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


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
    full_name = " ".join((data.get("full_name") or "").split())
    phone = (data.get("phone") or "").strip()
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,30}", username):
        return jsonify({"ok": False, "error": "Tên đăng nhập cần dài 3–30 ký tự (chữ, số, ., _ hoặc -)."}), 400
    if not NAME_RE.fullmatch(full_name) or len(full_name) < 2 or len(full_name) > 120:
        return jsonify({"ok": False, "error": "Họ tên phải có ít nhất 2 ký tự và gồm các từ hợp lệ."}), 400
    if not PHONE_RE.fullmatch(phone):
        return jsonify({"ok": False, "error": "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng số 0."}), 400
    if len(password) < 8 or len(password) > 128 or not SPECIAL_RE.search(password):
        return jsonify({"ok": False, "error": "Mật khẩu cần dài 8–128 ký tự và có ít nhất một ký hiệu đặc biệt."}), 400
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO users (username, password_hash, role, full_name, phone) VALUES (?, ?, 'customer', ?, ?)", (username, generate_password_hash(password), full_name, phone))
        db.commit()
        session.clear()
        session["user_id"] = cursor.lastrowid
        session["username"] = username
        session["role"] = "customer"
        return jsonify({"ok": True, "user": {"id": cursor.lastrowid, "username": username, "role": "customer", "full_name": full_name, "phone": phone}}), 201
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"ok": False, "error": "Tên đăng nhập hoặc số điện thoại đã được sử dụng."}), 409
    finally:
        db.close()


@client_bp.route("/api/client/login", methods=["POST"])
def customer_login():
    data = request.get_json(silent=True) or {}
    identifier = (data.get("identifier") or "").strip()
    password = data.get("password") or ""
    if not identifier or not password:
        return jsonify({"ok": False, "error": "Vui lòng nhập tên đăng nhập/số điện thoại và mật khẩu."}), 400
    db = get_db()
    try:
        user = db.execute("SELECT id, username, password_hash, role FROM users WHERE username = ? OR phone = ?", (identifier, identifier)).fetchone()
        if user is None or not check_password_hash(user["password_hash"], password):
            return jsonify({"ok": False, "error": "Tên đăng nhập/số điện thoại hoặc mật khẩu không đúng."}), 401
        session.clear()
        session.update(user_id=user["id"], username=user["username"], role=user["role"])
        return jsonify({"ok": True, "user": {"id": user["id"], "username": user["username"], "role": user["role"]}})
    finally:
        db.close()


@client_bp.route("/api/client/profile", methods=["GET"])
def customer_profile():
    auth_error = customer_api_required()
    if auth_error:
        return auth_error
    db = get_db()
    try:
        row = db.execute("SELECT username, full_name, phone FROM users WHERE id = ?", (session["user_id"],)).fetchone()
        if row is None:
            session.clear()
            return jsonify({"ok": False, "error": "Không tìm thấy tài khoản."}), 404
        return jsonify({"ok": True, "user": dict(row)})
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
    address = " ".join((data.get("delivery_address") or "").split())
    items = data.get("items")
    if len(address) < 10 or len(address) > 500 or not re.search(r"[A-Za-zÀ-ỹ0-9]", address):
        return jsonify({"ok": False, "error": "Địa chỉ cần có ít nhất 10 ký tự và là địa chỉ giao hàng hợp lệ."}), 400
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
        user = db.execute("SELECT full_name, phone FROM users WHERE id = ? AND role = 'customer'", (session["user_id"],)).fetchone()
        if user is None or not user["full_name"] or not user["phone"]:
            db.rollback()
            return jsonify({"ok": False, "error": "Tài khoản chưa có họ tên hoặc số điện thoại hợp lệ. Vui lòng liên hệ cửa hàng."}), 400
        products = {}
        for product_id, quantity in quantities.items():
            product = db.execute("SELECT id, name, price, stock FROM products WHERE id = ?", (product_id,)).fetchone()
            if product is None:
                db.rollback()
                return jsonify({"ok": False, "error": "Sản phẩm không còn tồn tại."}), 409
            if product["stock"] < quantity:
                db.rollback()
                return jsonify({"ok": False, "error": f"Sản phẩm {product['name']} hiện chỉ còn {product['stock']} sản phẩm trong kho."}), 409
            products[product_id] = product
        total = sum(products[pid]["price"] * quantity for pid, quantity in quantities.items())
        cursor = db.execute("INSERT INTO orders (customer_id, status, total, customer_name, phone, delivery_address) VALUES (?, 'pending', ?, ?, ?, ?)", (session["user_id"], total, user["full_name"], user["phone"], address))
        order_id = cursor.lastrowid
        for product_id, quantity in quantities.items():
            product = products[product_id]
            db.execute("INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)", (order_id, product_id, quantity, product["price"]))
            updated = db.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (quantity, product_id, quantity))
            if updated.rowcount != 1:
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
