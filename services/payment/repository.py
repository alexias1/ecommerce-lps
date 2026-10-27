from common.lps import db


class PaymentRepository:
    def __init__(self):
        self.conn = db("payment")
        self.conn.execute("CREATE TABLE IF NOT EXISTS payments(id TEXT PRIMARY KEY, method TEXT, amount REAL, status TEXT)")

    def save(self, pid, method, amount, status):
        self.conn.execute("INSERT INTO payments VALUES(?,?,?,?)", (pid, method, amount, status))
        self.conn.commit()
