import sqlite3


def transition_order_status(db, order_id, target_status, customer_id=None):
    """Atomically transition an order and restock its items exactly once on cancellation."""
    if target_status not in {"approved", "cancelled"}:
        raise ValueError("Unsupported order status")

    db.execute("BEGIN IMMEDIATE")
    query = "SELECT id, status FROM orders WHERE id = ?"
    params = [order_id]
    if customer_id is not None:
        query += " AND customer_id = ?"
        params.append(customer_id)
    order = db.execute(query, params).fetchone()

    if order is None:
        db.rollback()
        return None, "not_found"
    if order["status"] != "pending":
        db.rollback()
        return None, "invalid_transition"

    if target_status == "cancelled":
        items = db.execute(
            "SELECT product_id, quantity FROM order_items WHERE order_id = ?",
            (order_id,),
        ).fetchall()
        for item in items:
            cursor = db.execute(
                "UPDATE products SET stock = stock + ? WHERE id = ?",
                (item["quantity"], item["product_id"]),
            )
            if cursor.rowcount != 1:
                db.rollback()
                return None, "product_missing"

    db.execute("UPDATE orders SET status = ? WHERE id = ?", (target_status, order_id))
    db.commit()
    return {"id": order_id, "status": target_status}, None
