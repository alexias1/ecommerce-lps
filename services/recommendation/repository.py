from collections import Counter
from common.lps import db


class EventRepository:
    def __init__(self):
        self.conn = db("recommendation")
        self.conn.execute("CREATE TABLE IF NOT EXISTS events(user_id INTEGER, product_id INTEGER, category TEXT, type TEXT)")

    def add(self, e):
        self.conn.execute("INSERT INTO events VALUES(?,?,?,?)", (e.user_id, e.product_id, e.category, e.type))
        self.conn.commit()

    def by_user(self, user_id):
        return self.conn.execute("SELECT product_id, category, type FROM events WHERE user_id=?", (user_id,)).fetchall()

    def popularity(self):
        return Counter(r["product_id"] for r in self.conn.execute("SELECT product_id FROM events"))
