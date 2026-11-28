import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "database.db")
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "schema.sql")

DEMO_PRODUCTS = [
    ("Trà sữa truyền thống", 45000, 24, "Trà sữa thơm béo kết hợp trân châu dai giòn.", "Trà sữa"),
    ("Trà sữa matcha", 50000, 18, "Matcha thơm dịu, vị trà xanh cân bằng cùng sữa tươi.", "Trà sữa"),
    ("Trà sữa khoai môn", 48000, 12, "Khoai môn bùi mịn, thơm ngon và dễ uống.", "Trà sữa"),
    ("Trà sữa chocolate", 52000, 9, "Chocolate đậm vị dành cho tín đồ cacao.", "Trà sữa"),
    ("Trà sữa ô long", 49000, 16, "Trà ô long thơm nhẹ, hậu vị thanh.", "Trà sữa"),
    ("Trà sữa lài", 42000, 20, "Hương hoa lài dịu nhẹ kết hợp sữa tươi.", "Trà sữa"),
    ("Trà sữa caramel", 53000, 14, "Vị caramel ngọt thơm, béo vừa phải.", "Trà sữa"),
    ("Trà sữa dâu", 50000, 15, "Dâu tươi chua ngọt kết hợp trà sữa.", "Trà sữa"),
    ("Trà đào cam sả", 45000, 22, "Trà đào thơm mát cùng cam và sả.", "Trà trái cây"),
    ("Trà vải", 43000, 19, "Trà thanh mát với vải ngọt dịu.", "Trà trái cây"),
    ("Trà chanh mật ong", 35000, 25, "Trà chanh tươi và mật ong dịu ngọt.", "Trà trái cây"),
    ("Trà dâu tằm", 42000, 17, "Dâu tằm chua ngọt pha cùng trà lài.", "Trà trái cây"),
    ("Trà xoài nhiệt đới", 47000, 13, "Xoài chín thơm cùng trà trái cây.", "Trà trái cây"),
    ("Cà phê sữa đá", 35000, 20, "Cà phê rang xay pha cùng sữa đặc.", "Cà phê"),
    ("Bạc xỉu", 38000, 18, "Cà phê sữa nhiều sữa, vị nhẹ nhàng.", "Cà phê"),
    ("Cà phê đen đá", 30000, 21, "Cà phê đậm vị, dùng cùng đá.", "Cà phê"),
    ("Cacao sữa nóng", 40000, 12, "Cacao thơm béo, phục vụ nóng.", "Đồ uống khác"),
    ("Sữa tươi trân châu đường đen", 52000, 16, "Sữa tươi và trân châu đường đen.", "Đồ uống khác"),
    ("Trân châu đen", 10000, 40, "Topping trân châu đen dai ngon.", "Topping"),
    ("Thạch trái cây", 12000, 30, "Topping thạch trái cây nhiều màu.", "Topping"),
    ("Pudding trứng", 15000, 24, "Pudding trứng mềm mịn.", "Topping"),
    ("Thạch phô mai", 18000, 20, "Thạch phô mai béo nhẹ.", "Topping"),
]


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_db():
    conn = get_db()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as schema_file:
            conn.executescript(schema_file.read())

        existing_columns = {row["name"] for row in conn.execute("PRAGMA table_info(orders)")}
        for column, definition in (
            ("customer_name", "TEXT NOT NULL DEFAULT ''"),
            ("phone", "TEXT NOT NULL DEFAULT ''"),
            ("delivery_address", "TEXT NOT NULL DEFAULT ''"),
        ):
            if column not in existing_columns:
                conn.execute(f"ALTER TABLE orders ADD COLUMN {column} {definition}")

        product_columns = {row["name"] for row in conn.execute("PRAGMA table_info(products)")}
        if "category" not in product_columns:
            conn.execute("ALTER TABLE products ADD COLUMN category TEXT NOT NULL DEFAULT 'Khác'")
        if "image_url" not in product_columns:
            conn.execute("ALTER TABLE products ADD COLUMN image_url TEXT NOT NULL DEFAULT ''")

        user_columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)")}
        if "active" not in user_columns:
            conn.execute("ALTER TABLE users ADD COLUMN active INTEGER NOT NULL DEFAULT 1")

        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            from werkzeug.security import generate_password_hash
            seed_users = [("admin", "admin123", "admin"), ("staff", "staff123", "staff"), ("customer", "customer123", "customer")]
            conn.executemany(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                [(u, generate_password_hash(p), r) for u, p, r in seed_users],
            )

        for name, price, stock, description, category in DEMO_PRODUCTS:
            conn.execute(
                "INSERT INTO products (name, price, stock, description, category) SELECT ?, ?, ?, ?, ? WHERE NOT EXISTS (SELECT 1 FROM products WHERE name = ?)",
                (name, price, stock, description, category, name),
            )
        conn.commit()
    finally:
        conn.close()
