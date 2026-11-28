-- Dữ liệu demo cho trang Quản trị bán hàng.
-- init_db() chạy file này khi bảng products còn trống.

INSERT OR IGNORE INTO users (username, password_hash, role) VALUES
    ('kh_minh', 'scrypt:32768:8:1$9a6vhbUrOY7UXDpw$f8e7530c6bd6764143938444db287adb784fa23a488f710be697ba1b22298e5c6c792eb08155fce2e21a528e602df9bbd54aeac4ab085d02c12f93ac2ed4ec26', 'customer'),
    ('kh_tuan', 'scrypt:32768:8:1$9a6vhbUrOY7UXDpw$f8e7530c6bd6764143938444db287adb784fa23a488f710be697ba1b22298e5c6c792eb08155fce2e21a528e602df9bbd54aeac4ab085d02c12f93ac2ed4ec26', 'customer');

INSERT OR IGNORE INTO products (id, name, price, stock, description, image_url) VALUES
    (1, 'Trà sữa truyền thống', 25000, 120, 'Trà sữa truyền thống trân châu đen', '/static/images/products/tra-sua-truyen-thong.svg'),
    (2, 'Trà đào cam sả', 35000, 80, 'Trà đào pha cam sả thanh mát', '/static/images/products/tra-dao-cam-sa.svg'),
    (3, 'Sữa tươi trân châu đường đen', 30000, 100, 'Sữa tươi thanh trùng kết hợp trân châu đường đen', '/static/images/products/sua-tuoi-duong-den.svg'),
    (4, 'Trà xanh sữa', 28000, 60, 'Trà xanh nhài pha sữa béo nhẹ', '/static/images/products/tra-xanh-sua.svg'),
    (5, 'Cà phê sữa đá', 22000, 90, 'Cà phê phin truyền thống pha sữa đặc', '/static/images/products/ca-phe-sua-da.svg'),
    (6, 'Trà sữa matcha', 38000, 45, 'Matcha Nhật Bản hòa quyện sữa tươi và trân châu trắng', '/static/images/products/tra-sua-matcha.svg'),
    (7, 'Trà sữa khoai môn', 34000, 15, 'Khoai môn nghiền mịn thơm béo cùng trân châu', '/static/images/products/tra-sua-khoai-mon.svg'),
    (8, 'Trà ô long kem cheese', 42000, 35, 'Trà ô long nướng phủ lớp kem phô mai mặn béo', '/static/images/products/tra-o-long-kem-cheese.svg');

INSERT OR IGNORE INTO orders (id, customer_id, status, total, created_at, approved_at) VALUES
    (200000001, (SELECT id FROM users WHERE username = 'customer'), 'pending', 175000, datetime('now', 'localtime'), NULL),
    (200000009, (SELECT id FROM users WHERE username = 'kh_minh'), 'approved', 170000, datetime('now', 'localtime'), datetime('now', 'localtime')),
    (200000015, (SELECT id FROM users WHERE username = 'customer'), 'approved', 146000, datetime('now', 'localtime', '-1 day'), datetime('now', 'localtime', '-1 day')),
    (200000023, (SELECT id FROM users WHERE username = 'kh_tuan'), 'pending', 92000, datetime('now', 'localtime', '-2 days'), NULL),
    (200000031, (SELECT id FROM users WHERE username = 'customer'), 'cancelled', 25000, datetime('now', 'localtime', '-2 days'), NULL),
    (200000040, (SELECT id FROM users WHERE username = 'kh_minh'), 'pending', 126000, datetime('now', 'localtime'), NULL);

INSERT OR IGNORE INTO order_items (order_id, product_id, quantity, price) VALUES
    (200000001, 1, 2, 25000),
    (200000001, 2, 1, 35000),
    (200000001, 3, 3, 30000),
    (200000009, 1, 4, 25000),
    (200000009, 2, 2, 35000),
    (200000015, 3, 3, 30000),
    (200000015, 4, 2, 28000),
    (200000023, 2, 2, 35000),
    (200000023, 5, 1, 22000),
    (200000031, 1, 1, 25000),
    (200000040, 3, 2, 30000),
    (200000040, 5, 3, 22000);

INSERT OR IGNORE INTO invoices (id, order_id, issued_at) VALUES
    (1, 200000015, datetime('now', 'localtime', '-1 day'));
