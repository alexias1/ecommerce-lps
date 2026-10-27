from pydantic import BaseModel


class Credentials(BaseModel):
    email: str
    password: str


class SocialLogin(BaseModel):
    provider: str
    email: str
