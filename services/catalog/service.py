"""Componente de catálogo.

CatalogInterface é o contrato. Variantes do ponto de variação "Catálogo":
SimpleCatalog (lista simples) e SearchCatalog (com filtros/busca).
"""
from abc import ABC, abstractmethod
from common.lps import ServiceError, build, call, variants


class CatalogInterface(ABC):
    name = ""

    def __init__(self, repo):
        self.repo = repo

    @abstractmethod
    def list_products(self, q=None, category=None):
        ...


class SimpleCatalog(CatalogInterface):
    name = "simple"

    def list_products(self, q=None, category=None):
        return self.repo.all()  # ignora filtros


class SearchCatalog(CatalogInterface):
    name = "search"

    def list_products(self, q=None, category=None):
        return self.repo.search(q, category)


CATALOGS = {"simple": SimpleCatalog, "search": SearchCatalog}


class CatalogService:
    def __init__(self, repo):
        self.repo = repo
        self.variant = variants("CATALOG_VARIANT", "simple")[0]
        self.catalog = build(CATALOGS, [self.variant], repo)[self.variant]

    def list_products(self, q=None, category=None):
        return self.catalog.list_products(q, category)

    def get_product(self, pid, user_id=None):
        p = self.repo.get(pid)
        if p is None:
            raise ServiceError(404, "Produto não encontrado")
        if user_id is not None:  # feature opcional: guarda a visualização no histórico
            call("POST", "recommendation", "/events",
                 json={"user_id": user_id, "product_id": pid, "category": p["category"], "type": "view"})
        return p
