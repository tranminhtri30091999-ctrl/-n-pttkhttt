import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

DEMO_PRODUCTS = [
    ("Trà sữa trân châu", 45000, 24, "Trà sữa thơm béo kết hợp trân châu dai giòn."),
    ("Trà sữa matcha", 50000, 18, "Matcha thơm dịu, vị trà xanh cân bằng cùng sữa tươi."),
    ("Trà sữa khoai môn", 48000, 12, "Khoai môn bùi mịn, thơm ngon và dễ uống."),
    ("Trà sữa chocolate", 52000, 9, "Chocolate đậm vị dành cho tín đồ cacao."),
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
        conn.executescript(schema_file.read())

    # Add checkout fields to databases created before the customer shopping flow.
    existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(orders)")}
    for column, definition in (
        ("customer_name", "TEXT NOT NULL DEFAULT ''"),
        ("phone", "TEXT NOT NULL DEFAULT ''"),
        ("delivery_address", "TEXT NOT NULL DEFAULT ''"),
    ):
        if column not in existing_columns:
            conn.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")

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
            [(username, generate_password_hash(password), role) for username, password, role in seed_users],
        )

    product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if product_count == 0:
        conn.executemany(
            "INSERT INTO products (name, price, stock, description) VALUES (?, ?, ?, ?)",
            DEMO_PRODUCTS,
        )
    conn.commit()
    conn.close()
