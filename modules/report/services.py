"""Nghiệp vụ hóa đơn: tạo/lưu bản ghi hóa đơn cho đơn hàng."""

from database.db_helper import get_db


def create_invoice(order_id):
    db = get_db()
    try:
        order = db.execute(
            """
            SELECT o.id, o.total, o.customer_id, u.username AS customer
              FROM orders o
              LEFT JOIN users u ON u.id = o.customer_id
             WHERE o.id = ?
            """,
            (order_id,),
        ).fetchone()
        if order is None:
            return {"ok": False, "error": "Không tìm thấy đơn hàng"}

        # order_id UNIQUE: in lại đơn đã có hóa đơn thì lấy bản ghi cũ.
        db.execute(
            "INSERT OR IGNORE INTO invoices (order_id) VALUES (?)", (order_id,)
        )
        db.commit()
        invoice = db.execute(
            "SELECT id, issued_at FROM invoices WHERE order_id = ?",
            (order_id,),
        ).fetchone()

        items = db.execute(
            """
            SELECT COALESCE(p.name, 'Sản phẩm đã ngừng kinh doanh') AS name,
                   oi.quantity, oi.price
              FROM order_items oi
              LEFT JOIN products p ON p.id = oi.product_id
             WHERE oi.order_id = ?
            """,
            (order_id,),
        ).fetchall()

        return {
            "ok": True,
            "invoice": {
                "id": invoice["id"],
                "order_id": order_id,
                "issued_at": invoice["issued_at"],
                "customer": order["customer"]
                or f"Khách hàng #{order['customer_id']}",
                "total": order["total"],
                "items": [
                    {
                        "name": item["name"],
                        "quantity": item["quantity"],
                        "price": item["price"],
                    }
                    for item in items
                ],
            },
        }
    finally:
        db.close()
