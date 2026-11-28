from flask import Blueprint, jsonify, render_template, request

from modules.admin.routes import role_required
from modules.products import services

products_bp = Blueprint("products", __name__)


def _extract_payload_and_file():
    """Hỗ trợ cả JSON và multipart/form-data khi thêm hoặc sửa sản phẩm."""
    if request.content_type and "multipart/form-data" in request.content_type:
        payload = request.form.to_dict()
        image_file = request.files.get("image_file")
        return payload, image_file
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        payload = {}
    return payload, None


def _json_response(result, success_status=200):
    """Loại bỏ trường status nội bộ (nếu có) trước khi trả JSON cho client."""
    body = dict(result)
    default_status = success_status if body.get("ok") else 400
    status = body.pop("status", default_status)
    return jsonify(body), status


@products_bp.route("/products.html", methods=["GET"])
@role_required("staff", "admin")
def products_page():
    return render_template("staff/products.html", active_nav="products")


@products_bp.route("/api/products", methods=["GET"])
@role_required("staff", "admin")
def list_products():
    result = services.list_products(
        search=request.args.get("search", ""),
        stock_filter=request.args.get("stock", ""),
    )
    return _json_response(result)


@products_bp.route("/api/products/<int:product_id>", methods=["GET"])
@role_required("staff", "admin")
def get_product(product_id):
    return _json_response(services.get_product(product_id))


@products_bp.route("/api/products", methods=["POST"])
@role_required("staff", "admin")
def create_product():
    payload, image_file = _extract_payload_and_file()
    result = services.create_product(payload, image_file=image_file)
    return _json_response(result, success_status=201)


@products_bp.route("/api/products/<int:product_id>", methods=["PUT"])
@role_required("staff", "admin")
def update_product(product_id):
    payload, image_file = _extract_payload_and_file()
    result = services.update_product(
        product_id, payload, image_file=image_file
    )
    return _json_response(result)


@products_bp.route("/api/products/<int:product_id>", methods=["DELETE"])
@role_required("staff", "admin")
def delete_product(product_id):
    return _json_response(services.delete_product(product_id))
