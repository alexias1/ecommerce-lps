from common.lps import db


class NotificationRepository:
    def __init__(self):
        self.conn = db("notification")
        self.conn.execute("CREATE TABLE IF NOT EXISTS log(user_id INTEGER, channel TEXT, message TEXT)")

    def add(self, n):
        self.conn.execute("INSERT INTO log VALUES(?,?,?)", (n.user_id, n.channel, n.message))
        self.conn.commit()

    def all(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM log")]
