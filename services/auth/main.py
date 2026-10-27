"""Auth Service (porta 8001) — camada Controller."""
from fastapi import FastAPI
from common.lps import install_error_handlers
from services.auth.dto import Credentials, SocialLogin
from services.auth.repository import UserRepository
from services.auth.service import AuthService

app = FastAPI(title="Auth Service")
install_error_handlers(app)
service = AuthService(UserRepository())


@app.get("/health")
def health():
    return {"service": "auth", "variants": service.names}


@app.post("/register")
def register(c: Credentials):
    return service.register(c)


@app.post("/login")
def login(c: Credentials):
    return service.login(c)


@app.post("/login/social")
def login_social(s: SocialLogin):
    return service.login_social(s)
