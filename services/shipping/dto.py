from typing import Optional
from pydantic import BaseModel


class Quote(BaseModel):
    subtotal: float
    cep: Optional[str] = None
