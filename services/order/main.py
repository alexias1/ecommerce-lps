"""Order Service (porta 8004) — camada Controller."""
from fastapi import FastAPI
from common.lps import install_error_handlers
from services.order.dto import Checkout
from services.order.repository import OrderRepository
from services.order.service import OrderService

app = FastAPI(title="Order Service")
install_error_handlers(app)
orders = OrderService(OrderRepository())


@app.get("/health")
def health():
    return {"service": "order"}


@app.post("/orders")
def create_order(c: Checkout):
    return orders.checkout(c)


@app.get("/orders/{user_id}")
def list_orders(user_id: int):
    return orders.list_orders(user_id)
