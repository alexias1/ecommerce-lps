"""Notification Service (porta 8008, opcional) — camada Controller."""
from fastapi import FastAPI
from common.lps import install_error_handlers
from services.notification.dto import Notice
from services.notification.repository import NotificationRepository
from services.notification.service import NotificationService

app = FastAPI(title="Notification Service")
install_error_handlers(app)
service = NotificationService(NotificationRepository())


@app.get("/health")
def health():
    return {"service": "notification", "channels": service.names}


@app.post("/notify")
def notify(n: Notice):
    return service.notify(n)


@app.get("/log")
def log():
    return service.log()
