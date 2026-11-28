import math
import sqlite3

from flask import Blueprint, jsonify, render_template, request

from modules.admin.routes import role_required
from database.db_helper import get_db

products_bp = Blueprint("products", __name__)


@products_bp.route("/products.html")
@role_required("staff", "admin")
def products_page():
    return render_template("staff/products.html")


def product_payload(row):
    return {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "stock": row["stock"],
        "description": row["description"] or "",
        "category": row["category"] or "Khác",
        "image_url": row["image_url"] or "",
    }


def validate_product(data, require_name=True):
    name = (data.get("name") or "").strip()
    category = (data.get("category") or "Khác").strip() or "Khác"
    description = (data.get("description") or "").strip()
    image_url = (data.get("image_url") or "").strip()
    try:
        price = float(data.get("price", 0))
        stock = int(data.get("stock", 0))
    except (TypeError, ValueError):
        return None, "Giá và số lượng phải là số hợp lệ."
    if require_name and not name:
        return None, "Tên sản phẩm là bắt buộc."
    if name and len(name) > 120:
        return None, "Tên sản phẩm không quá 120 ký tự."
    if not math.isfinite(price) or price < 0:
        return None, "Giá phải là số không âm."
    if stock < 0 or stock > 1000000:
        return None, "Số lượng tồn phải nằm trong khoảng 0 đến 1.000.000."
    if len(description) > 1000 or len(category) > 80 or len(image_url) > 500:
        return None, "Thông tin sản phẩm vượt quá độ dài cho phép."
    return {"name": name, "price": price, "stock": stock, "description": description, "category": category, "image_url": image_url}, None


@products_bp.route("/api/products", methods=["GET"])
@role_required("staff", "admin")
def list_products():
    db = get_db()
    try:
        rows = db.execute("SELECT id, name, price, stock, description, category, image_url FROM products ORDER BY category, name, id").fetchall()
        return jsonify({"ok": True, "products": [product_payload(row) for row in rows]})
    finally:
        db.close()


@products_bp.route("/api/products", methods=["POST"])
@role_required("staff", "admin")
def create_product():
    payload, error = validate_product(request.get_json(silent=True) or {})
    if error:
        return jsonify({"ok": False, "error": error}), 400
    db = get_db()
    try:
        cursor = db.execute("INSERT INTO products (name, price, stock, description, category, image_url) VALUES (?, ?, ?, ?, ?, ?)", (payload["name"], payload["price"], payload["stock"], payload["description"], payload["category"], payload["image_url"]))
        db.commit()
        return jsonify({"ok": True, "id": cursor.lastrowid}), 201
    except sqlite3.IntegrityError:
        db.rollback()
        return jsonify({"ok": False, "error": "Dữ liệu sản phẩm không hợp lệ."}), 400
    finally:
        db.close()


@products_bp.route("/api/products/<int:product_id>", methods=["PUT"])
@role_required("staff", "admin")
def update_product(product_id):
    data = request.get_json(silent=True) or {}
    payload, error = validate_product(data, require_name=False)
    if error:
        return jsonify({"ok": False, "error": error}), 400
    if "name" in data and not payload["name"]:
        return jsonify({"ok": False, "error": "Tên sản phẩm là bắt buộc."}), 400
    db = get_db()
    existing = db.execute("SELECT id FROM products WHERE id = ?", (product_id,)).fetchone()
    if existing is None:
        db.close()
        return jsonify({"ok": False, "error": "Không tìm thấy sản phẩm."}), 404
    fields = []
    values = []
    for key in ("name", "price", "stock", "description", "category", "image_url"):
        if key in data:
            fields.append(f"{key} = ?")
            values.append(payload[key])
    if fields:
        values.append(product_id)
        db.execute(f"UPDATE products SET {', '.join(fields)} WHERE id = ?", values)
        db.commit()
    db.close()
    return jsonify({"ok": True})


@products_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
@role_required("staff", "admin")
def delete_product(product_id):
    db = get_db()
    try:
        if db.execute("SELECT 1 FROM order_items WHERE product_id = ? LIMIT 1", (product_id,)).fetchone():
            return jsonify({"ok": False, "error": "Sản phẩm đã nằm trong đơn hàng, không thể xóa."}), 409
        cursor = db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        if cursor.rowcount != 1:
            return jsonify({"ok": False, "error": "Không tìm thấy sản phẩm."}), 404
        return jsonify({"ok": True})
    finally:
        db.close()
