"""Nghiệp vụ đơn hàng: danh sách/lọc, duyệt đơn, hủy đơn + tồn kho."""

from database.db_helper import get_db

STATUS_LABELS = {
    "pending": "Chờ duyệt",
    "approved": "Đã duyệt",
    "cancelled": "Đã huỷ",
}


def list_orders(search="", date_from="", date_to=""):
    db = get_db()
    try:
        clauses = []
        params = []

        search = (search or "").strip()
        if search:
            like = f"%{search}%"
            clauses.append(
                "(CAST(o.id AS TEXT) LIKE ?"
                " OR EXISTS (SELECT 1 FROM order_items oi"
                "   JOIN products p ON p.id = oi.product_id"
                "  WHERE oi.order_id = o.id AND p.name LIKE ?))"
            )
            params.extend([like, like])

        if date_from:
            clauses.append("date(o.created_at) >= date(?)")
            params.append(date_from)
        if date_to:
            clauses.append("date(o.created_at) <= date(?)")
            params.append(date_to)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = db.execute(
            f"""
            SELECT o.id, o.customer_id, o.status, o.total, o.created_at,
                   u.username AS customer
              FROM orders o
              LEFT JOIN users u ON u.id = o.customer_id
              {where}
              ORDER BY o.id DESC
            """,
            params,
        ).fetchall()

        orders = []
        for row in rows:
            items = db.execute(
                """
                SELECT COALESCE(p.name, 'Sản phẩm đã ngừng kinh doanh') AS name,
                       oi.quantity
                  FROM order_items oi
                  LEFT JOIN products p ON p.id = oi.product_id
                 WHERE oi.order_id = ?
                """,
                (row["id"],),
            ).fetchall()
            orders.append(
                {
                    "id": row["id"],
                    "customer": row["customer"] or f"Khách hàng #{row['customer_id']}",
                    "status": row["status"],
                    "status_label": STATUS_LABELS.get(row["status"], row["status"]),
                    "total": row["total"],
                    "created_at": row["created_at"],
                    "items": [
                        {"name": item["name"], "quantity": item["quantity"]}
                        for item in items
                    ],
                }
            )

        kpis = {
            "pending": db.execute(
                "SELECT COUNT(*) FROM orders WHERE status = 'pending'"
            ).fetchone()[0],
            "approved_today": db.execute(
                "SELECT COUNT(*) FROM orders"
                " WHERE status = 'approved'"
                " AND date(approved_at) = date('now', 'localtime')"
            ).fetchone()[0],
            "stock": db.execute(
                "SELECT COALESCE(SUM(stock), 0) FROM products"
            ).fetchone()[0],
        }
        return {"ok": True, "orders": orders, "kpis": kpis}
    finally:
        db.close()


def approve_order(order_id):
    db = get_db()
    try:
        order = db.execute(
            "SELECT status FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if order is None:
            return {"ok": False, "error": "Không tìm thấy đơn hàng"}
        if order["status"] != "pending":
            return {"ok": False, "error": "Chỉ duyệt được đơn đang chờ duyệt"}

        items = db.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
        for item in items:
            db.execute(
                "UPDATE products SET stock = stock - ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
        db.execute(
            "UPDATE orders SET status = 'approved',"
            " approved_at = datetime('now', 'localtime') WHERE id = ?",
            (order_id,),
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()


def cancel_order(order_id):
    db = get_db()
    try:
        order = db.execute(
            "SELECT status FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if order is None:
            return {"ok": False, "error": "Không tìm thấy đơn hàng"}
        if order["status"] == "cancelled":
            return {"ok": False, "error": "Đơn hàng đã bị hủy trước đó"}

        # Đơn đã duyệt đã từng trừ kho: hủy thì hoàn trả lại số lượng ly.
        if order["status"] == "approved":
            items = db.execute(
                "SELECT product_id, quantity FROM order_items WHERE order_id = ?",
                (order_id,),
            ).fetchall()
            for item in items:
                db.execute(
                    "UPDATE products SET stock = stock + ? WHERE id = ?",
                    (item["quantity"], item["product_id"]),
                )

        db.execute(
            "UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,)
        )
        db.commit()
        return {"ok": True}
    finally:
        db.close()
