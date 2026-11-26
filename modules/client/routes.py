from functools import wraps

from flask import Blueprint, jsonify, render_template, request, session

from database.db_helper import get_db

client_bp = Blueprint("client", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return render_template("client/login.html"), 401
        return view(*args, **kwargs)

    return wrapped


def customer_api_required():
    if "user_id" not in session:
        return jsonify({"ok": False, "error": "Vui lòng đăng nhập để tiếp tục."}), 401
    if session.get("role") != "customer":
        return jsonify({"ok": False, "error": "Chỉ tài khoản khách hàng mới có thể đặt hàng."}), 403
    return None


def product_dict(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "stock": row["stock"],
        "description": row["description"] or "",
    }


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


@client_bp.route("/api/products")
def list_products():
    query = (request.args.get("q") or "").strip()
    try:
        min_price = float(request.args["min_price"]) if request.args.get("min_price") else None
        max_price = float(request.args["max_price"]) if request.args.get("max_price") else None
    except ValueError:
        return jsonify({"ok": False, "error": "Khoảng giá không hợp lệ."}), 400
    if min_price is not None and min_price < 0 or max_price is not None and max_price < 0:
        return jsonify({"ok": False, "error": "Giá không được âm."}), 400
    if min_price is not None and max_price is not None and min_price > max_price:
        return jsonify({"ok": False, "error": "Giá từ phải nhỏ hơn hoặc bằng giá đến."}), 400

    clauses = []
    params = []
    if query:
        clauses.append("name LIKE ?")
        params.append(f"%{query}%")
    if min_price is not None:
        clauses.append("price >= ?")
        params.append(min_price)
    if max_price is not None:
        clauses.append("price <= ?")
        params.append(max_price)
    sql = "SELECT id, name, price, stock, description FROM products"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)
    sql += " ORDER BY name COLLATE NOCASE, id"

    db = get_db()
    rows = db.execute(sql, params).fetchall()
    db.close()
    return jsonify({"ok": True, "products": [product_dict(row) for row in rows]})


@client_bp.route("/api/products/<int:product_id>")
def get_product(product_id):
    db = get_db()
    row = db.execute(
        "SELECT id, name, price, stock, description FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()
    db.close()
    if row is None:
        return jsonify({"ok": False, "error": "Không tìm thấy sản phẩm."}), 404
    return jsonify({"ok": True, "product": product_dict(row)})


@client_bp.route("/api/client/orders", methods=["GET"])
def list_customer_orders():
    auth_error = customer_api_required()
    if auth_error:
        return auth_error
    db = get_db()
    orders = db.execute(
        """SELECT id, status, total, created_at, customer_name, phone, delivery_address
           FROM orders WHERE customer_id = ? ORDER BY id DESC""",
        (session["user_id"],),
    ).fetchall()
    result = []
    for order in orders:
        item_rows = db.execute(
            """SELECT oi.product_id, p.name, oi.quantity, oi.price
               FROM order_items oi LEFT JOIN products p ON p.id = oi.product_id
               WHERE oi.order_id = ? ORDER BY oi.id""",
            (order["id"],),
        ).fetchall()
        result.append({
            "id": order["id"],
            "status": order["status"],
            "total": order["total"],
            "created_at": order["created_at"],
            "customer_name": order["customer_name"],
            "phone": order["phone"],
            "delivery_address": order["delivery_address"],
            "items": [dict(item) for item in item_rows],
        })
    db.close()
    return jsonify({"ok": True, "orders": result})


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
    if not customer_name or not phone or not address:
        return jsonify({"ok": False, "error": "Vui lòng nhập họ tên, số điện thoại và địa chỉ giao hàng."}), 400
    if len(customer_name) > 120 or len(phone) > 40 or len(address) > 500:
        return jsonify({"ok": False, "error": "Thông tin giao hàng vượt quá độ dài cho phép."}), 400
    if not isinstance(items, list) or not items or len(items) > 50:
        return jsonify({"ok": False, "error": "Giỏ hàng đang trống hoặc có quá nhiều mặt hàng."}), 400

    quantities = {}
    try:
        for item in items:
            product_id = int(item.get("product_id"))
            quantity = int(item.get("quantity"))
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
            product = db.execute(
                "SELECT id, name, price, stock FROM products WHERE id = ?", (product_id,)
            ).fetchone()
            if product is None:
                db.rollback()
                return jsonify({"ok": False, "error": "Một sản phẩm không còn tồn tại."}), 409
            if product["stock"] < quantity:
                db.rollback()
                return jsonify({"ok": False, "error": f\"Sản phẩm {product['name']} chỉ còn {product['stock']} sản phẩm.\"}), 409
            products[product_id] = product

        total = sum(products[pid]["price"] * quantity for pid, quantity in quantities.items())
        cursor = db.execute(
            """INSERT INTO orders (customer_id, status, total, customer_name, phone, delivery_address)
               VALUES (?, 'pending', ?, ?, ?, ?)""",
            (session["user_id"], total, customer_name, phone, address),
        )
        order_id = cursor.lastrowid
        for product_id, quantity in quantities.items():
            product = products[product_id]
            db.execute(
                "INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (?, ?, ?, ?)",
                (order_id, product_id, quantity, product["price"]),
            )
            db.execute("UPDATE products SET stock = stock - ? WHERE id = ?", (quantity, product_id))
        db.commit()
    except Exception:
        db.rollback()
        return jsonify({"ok": False, "error": "Không thể tạo đơn hàng lúc này. Vui lòng thử lại."}), 500
    finally:
        db.close()

    return jsonify({"ok": True, "order_id": order_id, "total": total}), 201
