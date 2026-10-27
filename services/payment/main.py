"""Payment Service (porta 8005) — camada Controller."""
from fastapi import FastAPI
from common.lps import install_error_handlers
from services.payment.dto import Payment
from services.payment.repository import PaymentRepository
from services.payment.service import PaymentService

app = FastAPI(title="Payment Service")
install_error_handlers(app)
service = PaymentService(PaymentRepository())


@app.get("/health")
def health():
    return {"service": "payment", "methods": service.names}


@app.get("/methods")
def methods():
    return {"methods": service.names}


@app.post("/payments")
def pay(p: Payment):
    return service.pay(p.amount, p.method)
