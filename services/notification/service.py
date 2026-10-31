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
        """Sem canal informado, usa todos os canais habilitados; com canal, ele precisa estar habilitado."""
        if n.channel is not None and n.channel not in self.channels:
            raise ServiceError(400, f"Canal '{n.channel}' não habilitado neste produto: {self.names}")
        targets = [n.channel] if n.channel else self.names
        for ch in targets:
            self.channels[ch].send(n.user_id, n.message)
            self.repo.add(n.user_id, ch, n.message)
        return {"sent": True, "channels": targets}

    def log(self):
        return self.repo.all()
