import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")
SEED_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "seed_data.sql")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _migrate(conn):
    """Áp dụng thay đổi schema cho database đã tồn tại (idempotent)."""
    order_cols = {row[1] for row in conn.execute("PRAGMA table_info(orders)")}
    if "approved_at" not in order_cols:
        conn.execute("ALTER TABLE orders ADD COLUMN approved_at TEXT")


def init_db():
    conn = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        conn.executescript(f.read())
    _migrate(conn)

    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if user_count == 0:
        from werkzeug.security import generate_password_hash

        seed_users = [
            ("admin", "admin123", "admin"),
            ("staff", "staff123", "staff"),
            ("customer", "customer123", "customer"),
        ]
        conn.executemany(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            [(u, generate_password_hash(p), r) for u, p, r in seed_users],
        )

    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if product_count == 0 and os.path.exists(SEED_PATH):
        with open(SEED_PATH, "r", encoding="utf-8") as f:
            conn.executescript(f.read())

    conn.commit()
    conn.close()
