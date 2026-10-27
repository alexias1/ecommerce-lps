"""Cart Service (porta 8003) — camada Controller."""
from fastapi import FastAPI
from common.lps import install_error_handlers
from services.cart.dto import AddItem
from services.cart.repository import CartRepository
from services.cart.service import Cart

app = FastAPI(title="Cart Service")
install_error_handlers(app)
cart = Cart(CartRepository())


@app.get("/health")
def health():
    return {"service": "cart"}


@app.get("/cart/{user_id}")
def get_cart(user_id: int):
    return cart.get(user_id)


@app.post("/cart/{user_id}/items")
def add_item(user_id: int, item: AddItem):
    return cart.add_item(user_id, item.product_id, item.qty)


@app.delete("/cart/{user_id}")
def clear_cart(user_id: int):
    return cart.clear(user_id)
