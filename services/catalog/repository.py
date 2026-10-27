from common.lps import db

SEED = [
    ("Fone Bluetooth", "eletronicos", 199.9), ("Smartwatch", "eletronicos", 599.0),
    ("Carregador USB-C", "eletronicos", 79.9), ("Teclado Mecânico", "eletronicos", 349.0),
    ("Livro Engenharia de Software", "livros", 129.9), ("Livro Python Fluente", "livros", 159.9),
    ("Livro Microsserviços", "livros", 99.9), ("Camiseta Básica", "moda", 49.9),
    ("Tênis Esportivo", "moda", 289.9), ("Jaqueta Jeans", "moda", 219.9),
    ("Cafeteira Elétrica", "casa", 169.9), ("Luminária de Mesa", "casa", 89.9),
]


class ProductRepository:
    def __init__(self):
        self.conn = db("catalog")
        self.conn.execute("CREATE TABLE IF NOT EXISTS products(id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL)")
        if self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            self.conn.executemany("INSERT INTO products(name,category,price) VALUES(?,?,?)", SEED)
            self.conn.commit()

    def all(self):
        return [dict(r) for r in self.conn.execute("SELECT * FROM products")]

    def search(self, q=None, category=None):
        sql, args = "SELECT * FROM products WHERE 1=1", []
        if q:
            sql += " AND name LIKE ?"
            args.append(f"%{q}%")
        if category:
            sql += " AND category=?"
            args.append(category)
        return [dict(r) for r in self.conn.execute(sql, args)]

    def get(self, pid):
        row = self.conn.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
        return dict(row) if row else None
