"""Utilitários compartilhados pelos microserviços da LPS de e-commerce.

- PORTS / enabled() / url(): portas e features ativas no produto atual
  (ENABLED_SERVICES é gerada pelo generate_product.py a partir do features.json).
- variants() / build(): lêem as variantes escolhidas e instanciam as implementações
  (componentes) correspondentes a partir de um registro {nome: classe}.
- ServiceError: erro de negócio que a camada Controller converte em resposta HTTP.
- call(): chamada HTTP entre serviços; devolve None se o serviço estiver desativado
  ou indisponível (feature opcional não derruba o produto).
"""
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse

PORTS = {
    "auth": 8001, "catalog": 8002, "cart": 8003, "order": 8004,
    "payment": 8005, "recommendation": 8006, "shipping": 8007,
    "notification": 8008,
}
GATEWAY_PORT = 8000


class ServiceError(Exception):
    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status, self.detail = status, detail


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ServiceError)
    async def _handle(_, exc: ServiceError):
        return JSONResponse({"detail": exc.detail}, status_code=exc.status)


def variants(env: str, default: str) -> list:
    return [v.strip() for v in os.getenv(env, default).split(",") if v.strip()]


def build(registry: dict, names: list, *args) -> dict:
    """Instancia só as variantes escolhidas: {nome: componente}."""
    missing = [n for n in names if n not in registry]
    if missing:
        raise ValueError(f"Variante(s) inexistente(s) {missing}. Opções: {list(registry)}")
    return {n: registry[n](*args) for n in names}


def enabled(name: str) -> bool:
    return name in os.getenv("ENABLED_SERVICES", ",".join(PORTS)).split(",")


def url(name: str) -> str:
    return os.getenv(f"{name.upper()}_URL", f"http://127.0.0.1:{PORTS[name]}")  # 127.0.0.1 evita a demora do "localhost" (IPv6) no Windows


def db(name: str) -> sqlite3.Connection:
    """Cada microserviço tem o seu próprio banco SQLite (database per service)."""
    folder = os.getenv("DATA_DIR", "data")
    os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(os.path.join(folder, f"{name}.db"), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


_client = httpx.Client(timeout=5)  # cliente compartilhado: reaproveita conexões entre as chamadas
_pool = ThreadPoolExecutor(max_workers=4)


def call(method: str, name: str, path: str, **kwargs):
    if not enabled(name):
        return None
    try:
        r = _client.request(method, url(name) + path, **kwargs)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


def call_bg(method: str, name: str, path: str, **kwargs) -> None:
    """Chamada sem espera (fire-and-forget), para efeitos que ninguém consulta na hora (ex.: notificação)."""
    _pool.submit(call, method, name, path, **kwargs)
