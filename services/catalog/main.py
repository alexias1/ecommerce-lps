"""Catalog Service (porta 8002) — camada Controller."""
from typing import Optional
from fastapi import FastAPI, Header
from common.lps import install_error_handlers
from services.catalog.repository import ProductRepository
from services.catalog.service import CatalogService

app = FastAPI(title="Catalog Service")
install_error_handlers(app)
service = CatalogService(ProductRepository())


@app.get("/health")
def health():
    return {"service": "catalog", "variant": service.variant}


@app.get("/products")
def list_products(q: Optional[str] = None, category: Optional[str] = None):
    return service.list_products(q, category)


@app.get("/products/{pid}")
def get_product(pid: int, x_user_id: Optional[int] = Header(default=None)):
    return service.get_product(pid, x_user_id)
