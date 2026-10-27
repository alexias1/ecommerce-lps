"""Componente de pagamento.

PaymentMethod é o contrato. Variantes do ponto de variação "Pagamento":
PixPayment, CardPayment e BoletoPayment (podem coexistir: grupo OR [1,3]).
"""
import uuid
from abc import ABC, abstractmethod
from common.lps import ServiceError, build, variants


class PaymentMethod(ABC):
    name = ""

    @abstractmethod
    def process(self, amount: float) -> str:
        """Devolve o status do pagamento."""


class PixPayment(PaymentMethod):
    name = "pix"

    def process(self, amount):
        return "approved"


class CardPayment(PaymentMethod):
    name = "card"

    def process(self, amount):
        return "approved"


class BoletoPayment(PaymentMethod):
    name = "boleto"

    def process(self, amount):
        return "pending"


METHODS = {"pix": PixPayment, "card": CardPayment, "boleto": BoletoPayment}


class PaymentService:
    def __init__(self, repo):
        self.repo = repo
        self.names = variants("PAYMENT_METHODS", "pix,card,boleto")
        self.methods = build(METHODS, self.names)

    def pay(self, amount, method):
        if method not in self.methods:
            raise ServiceError(400, f"Método '{method}' não habilitado. Opções: {self.names}")
        status = self.methods[method].process(amount)
        pid = str(uuid.uuid4())[:8]
        self.repo.save(pid, method, amount, status)
        return {"payment_id": pid, "method": method, "amount": amount, "status": status}
