from common.lps import db


class CartRepository:
    def __init__(self):
        self.conn = db("cart")
        self.conn.execute("CREATE TABLE IF NOT EXISTS items(user_id INTEGER, product_id INTEGER, name TEXT, category TEXT, price REAL, qty INTEGER)")

    def items(self, user_id):
        return [dict(r) for r in self.conn.execute("SELECT * FROM items WHERE user_id=?", (user_id,))]

    def add(self, user_id, product, qty):
        self.conn.execute("INSERT INTO items VALUES(?,?,?,?,?,?)",
                          (user_id, product["id"], product["name"], product["category"], product["price"], qty))
        self.conn.commit()

    def clear(self, user_id):
        self.conn.execute("DELETE FROM items WHERE user_id=?", (user_id,))
        self.conn.commit()
