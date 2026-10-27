from typing import Optional
from pydantic import BaseModel


class Checkout(BaseModel):
    user_id: int
    payment_method: str
    cep: Optional[str] = None
