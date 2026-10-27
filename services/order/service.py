"""Componente de pedidos: OrderInterface (contrato) e OrderService (orquestra os outros serviços)."""
from abc import ABC, abstractmethod
from common.lps import ServiceError, call, call_bg


class OrderInterface(ABC):
    @abstractmethod
    def checkout(self, c): ...

    @abstractmethod
    def list_orders(self, user_id): ...


class OrderService(OrderInterface):
    def __init__(self, repo):
        self.repo = repo

    def checkout(self, c):
        cart = call("GET", "cart", f"/cart/{c.user_id}")
        if not cart or not cart["items"]:
            raise ServiceError(400, "Carrinho vazio ou serviço de carrinho indisponível")
        subtotal = cart["total"]

        quote = call("POST", "shipping", "/quote", json={"subtotal": subtotal, "cep": c.cep})  # opcional
        shipping = quote["cost"] if quote else 0.0
        total = round(subtotal + shipping, 2)

        pay = call("POST", "payment", "/payments", json={"amount": total, "method": c.payment_method})
        if pay is None:
            raise ServiceError(502, "Pagamento recusado ou indisponível (método habilitado?)")

        order_id = self.repo.add(c.user_id, subtotal, shipping, total, c.payment_method, pay["status"])

        for it in cart["items"]:  # opcional: alimenta o histórico de recomendação
            call("POST", "recommendation", "/events",
                 json={"user_id": c.user_id, "product_id": it["product_id"], "category": it["category"], "type": "purchase"})
        call_bg("POST", "notification", "/notify",  # opcional, sem esperar
             json={"user_id": c.user_id, "message": f"Pedido #{order_id} recebido ({pay['status']})", "channel": "email"})
        call("DELETE", "cart", f"/cart/{c.user_id}")
        return {"order_id": order_id, "subtotal": subtotal, "shipping": shipping, "total": total, "payment": pay}

    def list_orders(self, user_id):
        return self.repo.by_user(user_id)
