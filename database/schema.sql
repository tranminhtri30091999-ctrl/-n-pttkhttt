PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    full_name TEXT,                                           -- (Thêm) Tên hiển thị lên đơn hàng/hóa đơn
    role TEXT NOT NULL CHECK (role IN ('admin', 'staff', 'customer')),
    is_active INTEGER NOT NULL DEFAULT 1,                     -- (Thêm) 1: hoạt động, 0: bị khóa (cho TV1)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    category TEXT DEFAULT 'Trà sữa',                          -- (Thêm) Lọc theo danh mục (cho TV3)
    price REAL NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL DEFAULT 0 CHECK (stock >= 0),      -- (Sửa) Chặn tồn kho âm
    image_url TEXT,                                           -- (Thêm) Ảnh sản phẩm (cho TV2 & TV3)
    description TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,                     -- (Thêm) 1: đang bán, 0: ngừng bán (xóa mềm)
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'approved', 'cancelled')), -- (Sửa) Khóa cứng 3 trạng thái chữ thường
    total REAL NOT NULL DEFAULT 0 CHECK (total >= 0),
    payment_method TEXT DEFAULT 'cash',                       -- (Thêm) cash / transfer / qr
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (customer_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price REAL NOT NULL CHECK (price >= 0),
    size TEXT DEFAULT 'M',                                    -- (Thêm - tùy chọn) Size S/M/L
    note TEXT,                                                -- (Thêm - tùy chọn) Đường, đá, topping
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);

CREATE TABLE IF NOT EXISTS invoices (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL UNIQUE,
    issued_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_id) REFERENCES orders (id)
);