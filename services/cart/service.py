"""Componente de carrinho: CartInterface (contrato) e Cart (implementação única)."""
from abc import ABC, abstractmethod
from common.lps import ServiceError, call


class CartInterface(ABC):
    @abstractmethod
    def get(self, user_id): ...

    @abstractmethod
    def add_item(self, user_id, product_id, qty): ...

    @abstractmethod
    def clear(self, user_id): ...


class Cart(CartInterface):
    def __init__(self, repo):
        self.repo = repo

    def get(self, user_id):
        items = self.repo.items(user_id)
        return {"user_id": user_id, "items": items, "total": round(sum(i["price"] * i["qty"] for i in items), 2)}

    def add_item(self, user_id, product_id, qty):
        product = call("GET", "catalog", f"/products/{product_id}")
        if product is None:
            raise ServiceError(404, "Produto não encontrado (ou catálogo indisponível)")
        self.repo.add(user_id, product, qty)
        return self.get(user_id)

    def clear(self, user_id):
        self.repo.clear(user_id)
        return {"cleared": True}
