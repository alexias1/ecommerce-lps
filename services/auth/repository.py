import sqlite3
from common.lps import db


class UserRepository:
    def __init__(self):
        self.conn = db("auth")
        self.conn.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, email TEXT UNIQUE, password TEXT)")

    def add(self, email, password_hash):
        try:
            cur = self.conn.execute("INSERT INTO users(email,password) VALUES(?,?)", (email, password_hash))
            self.conn.commit()
            return cur.lastrowid
        except sqlite3.IntegrityError:
            return None

    def find_by_credentials(self, email, password_hash):
        row = self.conn.execute("SELECT id FROM users WHERE email=? AND password=?", (email, password_hash)).fetchone()
        return row["id"] if row else None

    def find_by_email(self, email):
        row = self.conn.execute("SELECT id FROM users WHERE email=?", (email,)).fetchone()
        return row["id"] if row else None
