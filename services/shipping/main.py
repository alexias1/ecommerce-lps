"""Shipping Service (porta 8007, opcional) — camada Controller."""
from fastapi import FastAPI
from services.shipping.dto import Quote
from services.shipping.service import ShippingService

app = FastAPI(title="Shipping Service")
service = ShippingService()


@app.get("/health")
def health():
    return {"service": "shipping", "variant": service.variant}


@app.post("/quote")
def quote(q: Quote):
    return service.quote(q)
