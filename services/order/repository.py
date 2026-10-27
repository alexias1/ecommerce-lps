from common.lps import db


class OrderRepository:
    def __init__(self):
        self.conn = db("order")
        self.conn.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, subtotal REAL, shipping REAL, total REAL, method TEXT, status TEXT)")

    def add(self, user_id, subtotal, shipping, total, method, status):
        cur = self.conn.execute("INSERT INTO orders(user_id,subtotal,shipping,total,method,status) VALUES(?,?,?,?,?,?)",
                                (user_id, subtotal, shipping, total, method, status))
        self.conn.commit()
        return cur.lastrowid

    def by_user(self, user_id):
        return [dict(r) for r in self.conn.execute("SELECT * FROM orders WHERE user_id=?", (user_id,))]
