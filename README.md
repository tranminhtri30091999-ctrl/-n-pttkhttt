## Cấu trúc thư mục dự án

```text
he-thong-ban-hang/
│
├── .gitignore                 # Bỏ qua venv, file db tạm, cache
├── README.md                  # Hướng dẫn cài đặt, chạy dự án và phân công
├── requirements.txt           # Danh sách thư viện Python cần cài
├── app.py                     # File chạy chính kết nối các Blueprint
├── database.db                # (Không push lên git, tạo qua script)
│
├── database/                  # Phụ trách: Thành viên 2
│   ├── schema.sql             # Script tạo toàn bộ bảng CSDL
│   ├── seed_data.sql          # Dữ liệu thử nghiệm (Dummy data) để demo
│   └── db_helper.py           # Hàm kết nối cơ sở dữ liệu dùng chung
│
├── modules/                   # Tách riêng biệt từng phân hệ theo thành viên
│   ├── admin/                 # Phụ trách: Thành viên 1
│   │   ├── routes.py          # API/Route quản lý user, phân quyền
│   │   └── services.py        # Xử lý logic nghiệp vụ Admin
│   │
│   ├── products/              # Phụ trách: Thành viên 2
│   │   ├── routes.py          # API CRUD sản phẩm cho nhân viên
│   │   └── services.py        # Logic kiểm tra, thêm sửa xóa hàng hóa
│   │
│   ├── client/                # Phụ trách: Thành viên 3 (Trưởng nhóm)
│   │   ├── routes.py          # API tìm kiếm, lọc giá, gửi đơn đặt hàng
│   │   └── services.py        # Logic giỏ hàng, tính tổng tiền
│   │
│   ├── order/                 # Phụ trách: Thành viên 4
│   │   ├── routes.py          # API duyệt đơn, hủy đơn cho nhân viên
│   │   └── services.py        # Logic trừ tồn kho và hoàn trả kho
│   │
│   └── report/                # Phụ trách: Thành viên 5
│       ├── routes.py          # API xem hóa đơn, xuất hóa đơn, thống kê
│       └── services.py        # Tính doanh thu, lọc hóa đơn theo ngày
│
├── templates/                 # Chứa giao diện HTML
│   ├── admin/                 # TV1: Giao diện quản trị Admin riêng biệt
│   │   └── users.html
│   ├── staff/                 # Giao diện dành cho Nhân viên bán hàng
│   │   ├── products.html      # TV2: Màn hình CRUD sản phẩm
│   │   ├── orders.html        # TV4: Màn hình Duyệt/Hủy đơn hàng
│   │   ├── bills.html         # TV5: Màn hình hóa đơn
│   │   └── dashboard.html     # TV5: Màn hình báo cáo doanh thu
│   └── client/                # TV3: Giao diện người mua hàng
│       ├── index.html         # Trang danh mục & bộ lọc
│       └── checkout.html      # Trang thanh toán / đặt hàng
│
├── static/                    # Tài nguyên tĩnh dùng chung
│   ├── css/                   # Style CSS cho từng phân hệ
│   │   ├── admin.css
│   │   ├── staff.css
│   │   └── client.css
│   ├── js/                    # JavaScript xử lý phía Client/Staff
│   └── images/                # Ảnh sản phẩm demo, logo
│
└── docs/                      # Tài liệu báo cáo (TV1, TV2, TV3, TV4, TV5 phụ trách)
    ├── DFD_So_do/             # Chứa file ảnh/draw.io các sơ đồ DFD, BFD
    └── Huong_dan_su_dung.docx # Hướng dẫn sử dụng hệ thống
```
