import json
import os
import sqlite3
import sys
import urllib.parse
import urllib.request
import unicodedata

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR = os.path.join(BASE_DIR, "static", "images")
os.makedirs(SAVE_DIR, exist_ok=True)

# (ten_mon_trong_database, ten_file_luu, tu_khoa_tai_anh)
DRINKS = [
    ("Bạc xỉu", "bac_xiu.jpg", "Vietnamese white coffee iced milk"),
    ("Cà phê sữa đá", "cafe_sua_da.jpg", "Ca phe sua da Vietnamese iced coffee"),
    ("Cà phê đen đá", "cafe_den_da.jpg", "iced black coffee glass"),
    ("Pudding trứng", "pudding_trung.jpg", "caramel egg pudding dessert"),
    ("Thạch phô mai", "thach_pho_mai.jpg", "cheese jelly dessert cubes"),
    ("Thạch trái cây", "thach_trai_cay.jpg", "colorful fruit jelly cubes dessert"),
    ("Trân châu đen", "tran_chau_den.jpg", "black tapioca pearls boba"),
    ("Trà sữa caramel", "tra_sua_caramel.jpg", "caramel milk tea boba"),
    ("Trà sữa chocolate", "tra_sua_socola.jpg", "chocolate bubble tea"),
    ("Trà sữa dâu", "tra_sua_dau.jpg", "strawberry milk tea boba"),
    ("Trà sữa khoai môn", "tra_sua_khoai_mon.jpg", "taro bubble tea purple"),
    ("Trà sữa matcha", "tra_sua_matcha.jpg", "iced matcha milk tea"),
    ("Trà sữa truyền thống", "tra_sua_truyen_thong.jpg", "classic pearl milk tea boba"),
    ("Trà sữa ô long", "tra_sua_o_long.jpg", "oolong milk tea iced"),
    ("Trà chanh mật ong", "tra_chanh_mat_ong.jpg", "iced lemon honey tea"),
    ("Trà dâu tằm", "tra_dau_tam.jpg", "berry iced fruit tea"),
    ("Trà vải", "tra_vai.jpg", "lychee iced tea"),
    ("Trà xoài nhiệt đới", "tra_xoai_nhiet_doi.jpg", "mango iced tea"),
    ("Trà đào cam sả", "tra_dao_cam_sa.jpg", "peach iced tea"),
    ("Cacao sữa nóng", "cacao_sua_nong.jpg", "hot chocolate cocoa cup"),
    ("Sữa tươi trân châu đường đen", "sua_tuoi_tran_chau_duong_den.jpg", "brown sugar boba milk"),
]

HEADERS = {"User-Agent": "MilkTeaStudentProject/1.0 (Educational Demo)"}


def fetch_wikimedia_image(query, save_path):
    api_url = (
        "https://commons.wikimedia.org/w/api.php?"
        + urllib.parse.urlencode(
            {
                "action": "query",
                "generator": "search",
                "gsrsearch": f"filetype:bitmap {query}",
                "gsrnamespace": 6,
                "gsrlimit": 5,
                "prop": "imageinfo",
                "iiprop": "url",
                "iiurlwidth": 600,
                "format": "json",
            }
        )
    )
    req = urllib.request.Request(api_url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    pages = data.get("query", {}).get("pages", {})
    for page in pages.values():
        info = page.get("imageinfo", [{}])[0]
        img_url = info.get("thumburl") or info.get("url")
        if img_url and img_url.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
            img_req = urllib.request.Request(img_url, headers=HEADERS)
            with urllib.request.urlopen(img_req, timeout=20) as img_resp:
                with open(save_path, "wb") as f:
                    f.write(img_resp.read())
            return True
    return False

def update_database_image_urls():
    sys.path.insert(0, BASE_DIR)
    from database.db_helper import DB_PATH, init_db

    init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        for product_name, filename, _ in DRINKS:
            local_file = os.path.join(SAVE_DIR, filename)
            if os.path.isfile(local_file) and os.path.getsize(local_file) > 0:
                conn.execute(
                    "UPDATE products SET image_url = ? WHERE name = ?",
                    (f"/static/images/{filename}", product_name),
                )
            else:
                conn.execute(
                    "UPDATE products SET image_url = '' WHERE name = ?",
                    (product_name,),
                )
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    print("Dang tai 21 anh san pham vao thu muc static/images/ ...")
    for idx, (product_name, filename, keyword) in enumerate(DRINKS, 1):
        target = os.path.join(SAVE_DIR, filename)
        try:
            ok = fetch_wikimedia_image(keyword, target)
            status = "THANH CONG" if ok else "KHONG TIM THAY (tai thu cong)"
            print(f"[{idx:02d}/21] {filename} -> {status}")
        except Exception as e:
            print(f"[{idx:02d}/21] {filename} -> LOI: {e}")
    update_database_image_urls()
    print("Da gan anh cho san pham theo ten trong co so du lieu.")
    print("Hoan tat! Kiem tra thu muc static/images/ va xoa file download_images.py neu muon.")