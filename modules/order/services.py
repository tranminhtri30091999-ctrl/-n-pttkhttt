import sqlite3


def transition_order_status(db, order_id, target_status, customer_id=None):
    if target_status not in {"approved", "cancelled"}:
        raise ValueError("Unsupported order status")
    db.execute("BEGIN IMMEDIATE")
    sql = "SELECT id, status FROM orders WHERE id = ?"
    params = [order_id]
    if customer_id is not None:
        sql += " AND customer_id = ?"
        params.append(customer_id)
    order = db.execute(sql, params).fetchone()
    if order is None:
        db.rollback()
        return None, "not_found"
    current_status = order["status"]
    if customer_id is not None and target_status == "cancelled" and current_status != "pending":
        db.rollback()
        return None, "invalid_transition"
    if target_status == "approved" and current_status != "pending":
        db.rollback()
        return None, "invalid_transition"
    if target_status == "cancelled" and current_status not in {"pending", "approved"}:
        db.rollback()
        return None, "invalid_transition"
    if target_status == "approved":
        items = db.execute("SELECT oi.product_id, oi.quantity, p.name, p.stock FROM order_items oi JOIN products p ON p.id = oi.product_id WHERE oi.order_id = ?", (order_id,)).fetchall()
        for item in items:
            if item["stock"] < item["quantity"]:
                db.rollback()
                return None, "insufficient_stock"
        for item in items:
            cursor = db.execute("UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?", (item["quantity"], item["product_id"], item["quantity"]))
            if cursor.rowcount != 1:
                db.rollback()
                return None, "insufficient_stock"
    if target_status == "cancelled" and current_status == "approved":
        items = db.execute("SELECT product_id, quantity FROM order_items WHERE order_id = ?", (order_id,)).fetchall()
        for item in items:
            cursor = db.execute("UPDATE products SET stock = stock + ? WHERE id = ?", (item["quantity"], item["product_id"]))
            if cursor.rowcount != 1:
                db.rollback()
                return None, "product_missing"
    db.execute("UPDATE orders SET status = ? WHERE id = ?", (target_status, order_id))
    if db.execute("SELECT changes()").fetchone()[0] != 1:
        db.rollback()
        return None, "invalid_transition"
    db.commit()
    return {"id": order_id, "status": target_status}, None
