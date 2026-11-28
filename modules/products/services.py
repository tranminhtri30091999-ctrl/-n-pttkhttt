"""Nghiệp vụ quản lý sản phẩm cho nhân viên bán hàng: CRUD, kiểm tra dữ liệu và ảnh."""

from contextlib import contextmanager
import math
import os
import sqlite3
import uuid

from database.db_helper import BASE_DIR, get_db

LOW_STOCK_THRESHOLD = 20
MAX_NAME_LENGTH = 150
MAX_DESCRIPTION_LENGTH = 1000
MAX_IMAGE_BYTES = 5 * 1024 * 1024
ALLOWED_IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}
UPLOAD_URL_PREFIX = "/static/images/products/uploads/"
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "images", "products", "uploads")
PRODUCT_SELECT_COLUMNS = "id, name, price, stock, description, image_url, created_at"


def _parse_name(raw_name):
    if raw_name is None:
        return None, "Tên sản phẩm là bắt buộc"
    name = str(raw_name).strip()
    if not name:
        return None, "Tên sản phẩm không được để trống"
    if len(name) > MAX_NAME_LENGTH:
        return None, f"Tên sản phẩm không được vượt quá {MAX_NAME_LENGTH} ký tự"
    return name, None


def _parse_price(raw_price):
    if raw_price is None or str(raw_price).strip() == "" or isinstance(raw_price, bool):
        return None, "Giá bán là bắt buộc"
    try:
        price = float(raw_price)
    except (TypeError, ValueError):
        return None, "Giá bán phải là số hợp lệ"
    if not math.isfinite(price) or price < 0:
        return None, "Giá bán phải là số không âm"
    return price, None


def _parse_stock(raw_stock):
    if raw_stock is None or str(raw_stock).strip() == "" or isinstance(raw_stock, bool):
        return None, "Số lượng tồn kho là bắt buộc"
    if isinstance(raw_stock, float) and not raw_stock.is_integer():
        return None, "Số lượng tồn kho phải là số nguyên không âm"
    try:
        stock_str = str(raw_stock).strip()
        stock = int(stock_str) if isinstance(raw_stock, str) else int(raw_stock)
    except (TypeError, ValueError):
        return None, "Số lượng tồn kho phải là số nguyên không âm"
    if stock < 0:
        return None, "Số lượng tồn kho phải lớn hơn hoặc bằng 0"
    return stock, None


def _parse_description(raw_desc):
    if raw_desc is None:
        return "", None
    desc = str(raw_desc).strip()
    if len(desc) > MAX_DESCRIPTION_LENGTH:
        return None, f"Mô tả không được vượt quá {MAX_DESCRIPTION_LENGTH} ký tự"
    return desc, None


def _validate_image_url(raw_url):
    if raw_url is None:
        return "", None
    url = str(raw_url).strip()
    if not url:
        return "", None
    lowered = url.lower()
    if lowered.startswith(("/static/", "http://", "https://")):
        return url, None
    return None, "Đường dẫn hình ảnh phải bắt đầu bằng /static/, http:// hoặc https://"


def _save_uploaded_image(image_file):
    """Kiểm tra định dạng/dung lượng và lưu ảnh sản phẩm tải lên."""
    filename = (image_file.filename or "").strip()
    if not filename:
        return None, None

    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        return None, f"Định dạng ảnh không hỗ trợ (chỉ nhận: {allowed})"

    data = image_file.read(MAX_IMAGE_BYTES + 1)
    if len(data) > MAX_IMAGE_BYTES:
        return None, "Dung lượng ảnh tối đa là 5 MB"
    if not data:
        return None, "Tệp hình ảnh rỗng"

    os.makedirs(UPLOAD_DIR, exist_ok=True)
    stored_name = f"{uuid.uuid4().hex}{ext}"
    stored_path = os.path.join(UPLOAD_DIR, stored_name)
    with open(stored_path, "wb") as f:
        f.write(data)

    return f"{UPLOAD_URL_PREFIX}{stored_name}", None


def _cleanup_orphan_upload(db, image_url):
    """Xóa tệp ảnh tải lên nếu không còn sản phẩm nào sử dụng."""
    if not image_url or not image_url.startswith(UPLOAD_URL_PREFIX):
        return
    in_use = db.execute(
        "SELECT 1 FROM products WHERE image_url = ? LIMIT 1", (image_url,)
    ).fetchone()
    if in_use:
        return
    rel_name = image_url[len(UPLOAD_URL_PREFIX) :]
    if not rel_name or "/" in rel_name or "\\" in rel_name:
        return
    target_path = os.path.join(UPLOAD_DIR, rel_name)
    if os.path.isfile(target_path):
        os.remove(target_path)


_FIELD_PARSERS = (
    ("name", _parse_name, None),
    ("price", _parse_price, None),
    ("stock", _parse_stock, None),
    ("description", _parse_description, ""),
)


def _parse_product_fields(payload, existing=None):
    """Kiểm tra và chuẩn hóa các trường thông tin sản phẩm từ payload."""
    parsed = {}
    for field, parser, default in _FIELD_PARSERS:
        if existing is not None and field not in payload:
            value = existing[field]
            parsed[field] = default if value is None and default is not None else value
            continue
        value, err = parser(payload.get(field))
        if err:
            return None, err
        parsed[field] = value
    return parsed, None


def _error_result(message, status=400):
    return {"ok": False, "error": message, "status": status}


def _resolve_product_image(payload, image_file, current_image_url="", allow_clear=False):
    """Xác định image_url cuối cùng và lưu tệp ảnh tải lên nếu có."""
    image_url = current_image_url
    clear_image = allow_clear and str(payload.get("clear_image", "")).strip().lower() in (
        "1",
        "true",
        "yes",
    )
    if clear_image:
        image_url = ""
    elif not allow_clear or "image_url" in payload:
        image_url, err = _validate_image_url(payload.get("image_url"))
        if err:
            return None, None, err

    uploaded_url = None
    if image_file is not None and (image_file.filename or "").strip():
        uploaded_url, err = _save_uploaded_image(image_file)
        if err:
            return None, None, err
        image_url = uploaded_url

    return image_url, uploaded_url, None


@contextmanager
def _managed_upload_cleanup(db):
    """Dọn tệp ảnh mới tải lên nếu quá trình lưu CSDL gặp lỗi."""
    state = {"uploaded_url": None}
    try:
        yield state
    except Exception:
        db.rollback()
        if state["uploaded_url"]:
            _cleanup_orphan_upload(db, state["uploaded_url"])
        raise


def _get_stock_status(stock):
    if stock <= 0:
        return "out_of_stock"
    if stock <= LOW_STOCK_THRESHOLD:
        return "low_stock"
    return "in_stock"


def _fetch_product(db, product_id):
    """Truy vấn bản ghi sản phẩm theo ID."""
    return db.execute(
        f"SELECT {PRODUCT_SELECT_COLUMNS} FROM products WHERE id = ?",
        (product_id,),
    ).fetchone()


def _row_to_product(row):
    stock = row["stock"]
    return {
        "id": row["id"],
        "name": row["name"],
        "price": row["price"],
        "stock": stock,
        "stock_status": _get_stock_status(stock),
        "description": row["description"] or "",
        "image_url": row["image_url"] or "",
        "created_at": row["created_at"],
    }


def list_products(search="", stock_filter=""):
    """Trả về danh sách sản phẩm theo từ khóa/trạng thái kho và các chỉ số tổng quan."""
    db = get_db()
    try:
        clauses = []
        params = []

        keyword = (search or "").strip()
        if keyword:
            like = f"%{keyword}%"
            clauses.append(
                "(name LIKE ? OR COALESCE(description, '') LIKE ? OR CAST(id AS TEXT) LIKE ?)"
            )
            params.extend([like, like, like])

        if stock_filter == "in_stock":
            clauses.append("stock > 0")
        elif stock_filter == "low_stock":
            clauses.append("stock > 0 AND stock <= ?")
            params.append(LOW_STOCK_THRESHOLD)
        elif stock_filter == "out_of_stock":
            clauses.append("stock <= 0")

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = db.execute(
            f"""
            SELECT {PRODUCT_SELECT_COLUMNS}
              FROM products
              {where}
             ORDER BY id DESC
            """,
            params,
        ).fetchall()

        kpis = {
            "total_products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
            "total_stock": db.execute(
                "SELECT COALESCE(SUM(stock), 0) FROM products"
            ).fetchone()[0],
            "low_stock": db.execute(
                "SELECT COUNT(*) FROM products WHERE stock <= ?",
                (LOW_STOCK_THRESHOLD,),
            ).fetchone()[0],
        }

        return {
            "ok": True,
            "products": [_row_to_product(row) for row in rows],
            "kpis": kpis,
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
        }
    finally:
        db.close()


def get_product(product_id):
    """Lấy chi tiết một sản phẩm theo ID."""
    db = get_db()
    try:
        row = _fetch_product(db, product_id)
        if row is None:
            return _error_result("Không tìm thấy sản phẩm", 404)
        return {"ok": True, "product": _row_to_product(row)}
    finally:
        db.close()


def create_product(payload, image_file=None):
    """Kiểm tra dữ liệu và thêm sản phẩm mới."""
    payload = payload or {}
    fields, err = _parse_product_fields(payload)
    if err:
        return _error_result(err, 400)

    db = get_db()
    try:
        with _managed_upload_cleanup(db) as upload_state:
            image_url, upload_state["uploaded_url"], err = _resolve_product_image(
                payload, image_file
            )
            if err:
                return _error_result(err, 400)

            cursor = db.execute(
                """
                INSERT INTO products (name, price, stock, description, image_url)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    fields["name"],
                    fields["price"],
                    fields["stock"],
                    fields["description"],
                    image_url,
                ),
            )
            db.commit()
            row = _fetch_product(db, cursor.lastrowid)
            return {"ok": True, "product": _row_to_product(row)}
    finally:
        db.close()


def update_product(product_id, payload, image_file=None):
    """Cập nhật thông tin sản phẩm theo ID."""
    payload = payload or {}
    db = get_db()
    try:
        with _managed_upload_cleanup(db) as upload_state:
            existing = _fetch_product(db, product_id)
            if existing is None:
                return _error_result("Không tìm thấy sản phẩm", 404)

            fields, err = _parse_product_fields(payload, existing=existing)
            if err:
                return _error_result(err, 400)

            old_image_url = existing["image_url"] or ""
            image_url, upload_state["uploaded_url"], err = _resolve_product_image(
                payload,
                image_file,
                current_image_url=old_image_url,
                allow_clear=True,
            )
            if err:
                return _error_result(err, 400)

            db.execute(
                """
                UPDATE products
                   SET name = ?, price = ?, stock = ?, description = ?, image_url = ?
                 WHERE id = ?
                """,
                (
                    fields["name"],
                    fields["price"],
                    fields["stock"],
                    fields["description"],
                    image_url,
                    product_id,
                ),
            )
            db.commit()

            if old_image_url and old_image_url != image_url:
                _cleanup_orphan_upload(db, old_image_url)

            row = _fetch_product(db, product_id)
            return {"ok": True, "product": _row_to_product(row)}
    finally:
        db.close()


def delete_product(product_id):
    """Xóa sản phẩm theo ID và dọn tệp ảnh tải lên nếu không còn được tham chiếu."""
    db = get_db()
    try:
        existing = _fetch_product(db, product_id)
        if existing is None:
            return _error_result("Không tìm thấy sản phẩm", 404)

        referenced = db.execute(
            "SELECT 1 FROM order_items WHERE product_id = ? LIMIT 1",
            (product_id,),
        ).fetchone()
        if referenced is not None:
            return _error_result(
                "Không thể xóa sản phẩm đã có trong lịch sử đơn hàng", 409
            )

        old_image_url = existing["image_url"] or ""
        try:
            db.execute("DELETE FROM products WHERE id = ?", (product_id,))
            db.commit()
        except sqlite3.IntegrityError:
            db.rollback()
            return _error_result(
                "Không thể xóa sản phẩm đã có trong lịch sử đơn hàng", 409
            )

        _cleanup_orphan_upload(db, old_image_url)
        return {"ok": True}
    finally:
        db.close()
