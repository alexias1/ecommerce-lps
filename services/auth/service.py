"""Componente de autenticação.

AuthProvider é o contrato (interface). Cada variante do ponto de variação
"Autenticação" é uma implementação: EmailPasswordProvider e SocialProvider.
"""
import hashlib
import hmac
import os
from abc import ABC, abstractmethod
from common.lps import ServiceError, build, variants

SECRET = os.getenv("AUTH_SECRET", "dev-secret").encode()


def _hash(pw: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), SECRET, 10_000).hex()


class AuthProvider(ABC):
    name = ""

    def __init__(self, users):
        self.users = users

    @abstractmethod
    def login(self, **data) -> int:
        """Devolve o id do usuário autenticado."""


class EmailPasswordProvider(AuthProvider):
    name = "email"

    def register(self, email, password):
        uid = self.users.add(email, _hash(password))
        if uid is None:
            raise ServiceError(409, "Email já cadastrado")
        return uid

    def login(self, email, password):
        uid = self.users.find_by_credentials(email, _hash(password))
        if uid is None:
            raise ServiceError(401, "Credenciais inválidas")
        return uid


class SocialProvider(AuthProvider):
    """Login social simulado (mock): cria o usuário se não existir."""
    name = "social"

    def login(self, provider, email):
        return self.users.find_by_email(email) or self.users.add(email, f"social:{provider}")


PROVIDERS = {"email": EmailPasswordProvider, "social": SocialProvider}


class AuthService:
    def __init__(self, users):
        self.names = variants("AUTH_VARIANT", "email")
        self.providers = build(PROVIDERS, self.names, users)

    def _get(self, name):
        if name not in self.providers:
            raise ServiceError(404, f"Variante '{name}' desabilitada neste produto")
        return self.providers[name]

    @staticmethod
    def token(uid: int) -> str:
        return f"{uid}.{hmac.new(SECRET, str(uid).encode(), hashlib.sha256).hexdigest()[:16]}"

    def register(self, c):
        return {"user_id": self._get("email").register(c.email, c.password)}

    def login(self, c):
        uid = self._get("email").login(email=c.email, password=c.password)
        return {"user_id": uid, "token": self.token(uid)}

    def login_social(self, s):
        uid = self._get("social").login(provider=s.provider, email=s.email)
        return {"user_id": uid, "token": self.token(uid), "provider": s.provider}
