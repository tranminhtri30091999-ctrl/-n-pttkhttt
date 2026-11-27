import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'database.db')


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_all_orders(status_filter=None):
    conn = get_db_connection()
    try:
        query = """
            SELECT
                o.id,
                o.customer_id,
                u.username AS customer_name,
                o.status,
                o.total,
                o.created_at
            FROM orders o
            JOIN users u ON o.customer_id = u.id
        """
        params = []
        if status_filter and status_filter.lower() in ('pending', 'approved', 'cancelled'):
            query += " WHERE o.status = ?"
            params.append(status_filter.lower())

        query += " ORDER BY o.id DESC"
        orders_rows = conn.execute(query, params).fetchall()
        orders = []

        for row in orders_rows:
            order_dict = dict(row)
            items_rows = conn.execute("""
                SELECT
                    oi.id,
                    oi.product_id,
                    p.name AS product_name,
                    oi.quantity,
                    oi.price,
                    p.stock AS current_stock
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (row['id'],)).fetchall()

            order_dict['items'] = [dict(item) for item in items_rows]
            orders.append(order_dict)

        return orders
    finally:
        conn.close()


def approve_order(order_id):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            conn.rollback()
            return {"success": False, "message": f"Không tìm thấy đơn hàng #{order_id}."}

        if order['status'] == 'approved':
            conn.rollback()
            return {"success": False, "message": f"Đơn hàng #{order_id} đã được duyệt trước đó."}

        if order['status'] == 'cancelled':
            conn.rollback()
            return {"success": False, "message": f"Đơn hàng #{order_id} đã bị hủy, không thể duyệt."}

        items = conn.execute("""
            SELECT oi.product_id, oi.quantity, p.name, p.stock
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,)).fetchall()

        if not items:
            conn.rollback()
            return {"success": False, "message": f"Đơn hàng #{order_id} không có sản phẩm nào."}

        insufficient = []
        for item in items:
            if item['stock'] < item['quantity']:
                insufficient.append(
                    f"{item['name']} (Cần {item['quantity']}, kho còn {item['stock']})"
                )

        if insufficient:
            conn.rollback()
            return {
                "success": False,
                "message": "Không thể duyệt đơn do không đủ tồn kho: " + "; ".join(insufficient)
            }

        changes = []
        for item in items:
            new_stock = item['stock'] - item['quantity']
            conn.execute(
                "UPDATE products SET stock = ? WHERE id = ?",
                (new_stock, item['product_id'])
            )
            changes.append(f"{item['name']}: {item['stock']} -> {new_stock}")

        conn.execute("UPDATE orders SET status = 'approved' WHERE id = ?", (order_id,))
        conn.execute("INSERT OR IGNORE INTO invoices (order_id) VALUES (?)", (order_id,))

        conn.commit()
        return {
            "success": True,
            "message": f"Đã duyệt đơn #{order_id} & trừ kho thành công ({', '.join(changes)})."
        }
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Lỗi khi duyệt đơn: {str(e)}"}
    finally:
        conn.close()


def cancel_order(order_id):
    conn = get_db_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")

        order = conn.execute("SELECT * FROM orders WHERE id = ?", (order_id,)).fetchone()
        if not order:
            conn.rollback()
            return {"success": False, "message": f"Không tìm thấy đơn hàng #{order_id}."}

        if order['status'] == 'cancelled':
            conn.rollback()
            return {"success": False, "message": f"Đơn hàng #{order_id} đã bị hủy trước đó."}

        restored = []
        if order['status'] == 'approved':
            items = conn.execute("""
                SELECT oi.product_id, oi.quantity, p.name, p.stock
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            """, (order_id,)).fetchall()

            for item in items:
                new_stock = item['stock'] + item['quantity']
                conn.execute(
                    "UPDATE products SET stock = ? WHERE id = ?",
                    (new_stock, item['product_id'])
                )
                restored.append(f"{item['name']}: {item['stock']} -> {new_stock} (+{item['quantity']})")

            conn.execute("DELETE FROM invoices WHERE order_id = ?", (order_id,))

        conn.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        conn.commit()

        if restored:
            msg = f"Đã hủy đơn #{order_id} và hoàn trả kho: {', '.join(restored)}."
        else:
            msg = f"Đã hủy đơn #{order_id} (Đơn chờ duyệt chưa trừ kho)."

        return {"success": True, "message": msg}
    except Exception as e:
        conn.rollback()
        return {"success": False, "message": f"Lỗi khi hủy đơn: {str(e)}"}
    finally:
        conn.close()