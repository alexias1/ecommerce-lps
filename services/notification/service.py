"""Componente de notificação.

NotificationChannel é o contrato. Variantes do ponto de variação "Notificações":
EmailChannel e SmsChannel (envio simulado).
"""
from abc import ABC, abstractmethod
from common.lps import ServiceError, build, variants


class NotificationChannel(ABC):
    name = ""

    @abstractmethod
    def send(self, user_id: int, message: str) -> None:
        ...


class EmailChannel(NotificationChannel):
    name = "email"

    def send(self, user_id, message):
        print(f"[EMAIL] user={user_id}: {message}")


class SmsChannel(NotificationChannel):
    name = "sms"

    def send(self, user_id, message):
        print(f"[SMS] user={user_id}: {message}")


CHANNELS = {"email": EmailChannel, "sms": SmsChannel}


class NotificationService:
    def __init__(self, repo):
        self.repo = repo
        self.names = variants("NOTIFICATION_CHANNELS", "email")
        self.channels = build(CHANNELS, self.names)

    def notify(self, n):
        if n.channel not in self.channels:
            raise ServiceError(400, f"Canal '{n.channel}' não habilitado: {self.names}")
        self.channels[n.channel].send(n.user_id, n.message)
        self.repo.add(n)
        return {"sent": True}

    def log(self):
        return self.repo.all()
