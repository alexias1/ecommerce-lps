"""Componente de frete.

ShippingStrategy é o contrato. Variantes do ponto de variação "Frete":
FixedShipping (valor fixo) e CepShipping (calculado pelo CEP).
"""
from abc import ABC, abstractmethod
from common.lps import build, variants


class ShippingStrategy(ABC):
    name = ""

    @abstractmethod
    def quote(self, subtotal: float, cep) -> float:
        ...


class FixedShipping(ShippingStrategy):
    name = "fixed"

    def quote(self, subtotal, cep):
        return 15.0


class CepShipping(ShippingStrategy):
    name = "cep"

    def quote(self, subtotal, cep):
        if cep and cep[:1].isdigit():
            return 10.0 + int(cep[0]) * 3  # regra simples e determinística (didática)
        return 15.0


STRATEGIES = {"fixed": FixedShipping, "cep": CepShipping}


class ShippingService:
    def __init__(self):
        self.variant = variants("SHIPPING_VARIANT", "fixed")[0]
        self.strategy = build(STRATEGIES, [self.variant])[self.variant]

    def quote(self, q):
        return {"cost": self.strategy.quote(q.subtotal, q.cep), "variant": self.variant}
