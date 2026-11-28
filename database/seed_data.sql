-- Dữ liệu demo cho toàn bộ hệ thống (hỗ trợ chạy độc lập sau schema.sql hoặc qua init_db()).

INSERT OR IGNORE INTO users (username, password_hash, role) VALUES
    ('admin', 'scrypt:32768:8:1$T3hGwUFW8dEeJE7I$92e50024d879dc4bd73dadd98e65fa6c420c9bcdc51c2db50f3bff01e59f977d22c2c0597388b772bf9f311b68d93d3f97a19d0d56aa329fd8fc91ae9ebeff27', 'admin'),
    ('staff', 'scrypt:32768:8:1$l3sbgPieMyX5aK52$ff29af62b3d0c6861814a07f4ad2d27ca1a17cf16e77994a93778c1cbf719926c677c8eaa29403bbcb788a5f278244324fb5239e51d82036785ce0b58ffebddc', 'staff'),
    ('customer', 'scrypt:32768:8:1$vbSWyaSg0FicHZdg$f824e3f23cd7e80f8b01b43df9ff5d0d25023f1eee2681f71df7e521c026da7f70663c5d34037eb6a4e719af4e5315a24cd9680cec93ba7522a0645552db26d6', 'customer'),
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
