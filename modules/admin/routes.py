from functools import wraps

from flask import Blueprint, jsonify, render_template, request, session

from database.db_helper import get_db

admin_bp = Blueprint("admin", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            return jsonify({"ok": False, "error": "Authentication required"}), 401
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if "user_id" not in session:
                return jsonify({"ok": False, "error": "Authentication required"}), 401
            if session.get("role") not in roles:
                return jsonify({"ok": False, "error": "Forbidden"}), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator


@admin_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or request.form
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    selected_role = (data.get("role") or "").strip()

    db = get_db()
    user = db.execute(
        "SELECT id, username, password_hash, role, active FROM users WHERE username = ?",
        (username,),
    ).fetchone()
    db.close()

    from werkzeug.security import check_password_hash

    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"ok": False, "error": "Invalid username or password"}), 401
    if user["active"] == 0:
        return jsonify({"ok": False, "error": "Tài khoản đã bị khóa"}), 403
    if selected_role and selected_role != user["role"]:
        return jsonify({"ok": False, "error": "Vai trò đăng nhập không khớp với tài khoản"}), 403

    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]
    return jsonify(
        {
            "ok": True,
            "user": {
                "id": user["id"],
                "username": user["username"],
                "role": user["role"],
            },
        }
    )


@admin_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"ok": True})


@admin_bp.route("/me", methods=["GET"])
@login_required
def me():
    return jsonify(
        {
            "ok": True,
            "user": {
                "id": session["user_id"],
                "username": session["username"],
                "role": session["role"],
            },
        }
    )


@admin_bp.route("/users.html", methods=["GET"])
@role_required("admin")
def users_page():
    return render_template("admin/users.html")


@admin_bp.route("/api/users", methods=["GET"])
@role_required("admin")
def list_users():
    db = get_db()
    rows = db.execute("SELECT id, username, role, active, created_at FROM users ORDER BY id").fetchall()
    db.close()
    return jsonify({"ok": True, "users": [dict(row) for row in rows]})


@admin_bp.route("/api/users", methods=["POST"])
@role_required("admin")
def create_user():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role") or "customer"

    if not username or not password:
        return jsonify({"ok": False, "error": "Username and password are required"}), 400
    if role not in ("admin", "staff", "customer"):
        return jsonify({"ok": False, "error": "Invalid role"}), 400

    from werkzeug.security import generate_password_hash

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, generate_password_hash(password), role),
        )
        db.commit()
    except Exception:
        db.close()
        return jsonify({"ok": False, "error": "Username already exists"}), 409
    db.close()
    return jsonify({"ok": True})


@admin_bp.route("/api/users/<int:user_id>", methods=["PUT"])
@role_required("admin")
def update_user(user_id):
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    role = data.get("role")
    active = data.get("active")

    if role is not None and role not in ("admin", "staff", "customer"):
        return jsonify({"ok": False, "error": "Invalid role"}), 400
    if active is not None and active not in (0, 1, True, False):
        return jsonify({"ok": False, "error": "Invalid active state"}), 400

    db = get_db()
    user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if user is None:
        db.close()
        return jsonify({"ok": False, "error": "User not found"}), 404

    fields = []
    values = []
    if username:
        fields.append("username = ?")
        values.append(username)
    if role:
        fields.append("role = ?")
        values.append(role)
    if active is not None:
        fields.append("active = ?")
        values.append(1 if active else 0)
    if password:
        from werkzeug.security import generate_password_hash

        fields.append("password_hash = ?")
        values.append(generate_password_hash(password))

    if fields:
        values.append(user_id)
        try:
            db.execute(f"UPDATE users SET {', '.join(fields)} WHERE id = ?", values)
            db.commit()
        except Exception:
            db.close()
            return jsonify({"ok": False, "error": "Username already exists"}), 409
    db.close()
    return jsonify({"ok": True})


@admin_bp.route("/api/users/<int:user_id>", methods=["DELETE"])
@role_required("admin")
def delete_user(user_id):
    if user_id == session.get("user_id"):
        return jsonify({"ok": False, "error": "Cannot delete your own account"}), 400

    db = get_db()
    try:
        if db.execute("SELECT 1 FROM orders WHERE customer_id = ? LIMIT 1", (user_id,)).fetchone():
            db.close()
            return jsonify({"ok": False, "error": "Không thể xóa tài khoản đã có đơn hàng. Hãy khóa tài khoản."}), 409
        db.execute("DELETE FROM users WHERE id = ?", (user_id,))
        db.commit()
    finally:
        db.close()
    return jsonify({"ok": True})