from typing import Optional
from pydantic import BaseModel


class Notice(BaseModel):
    user_id: int
    message: str
    channel: Optional[str] = None  # None = envia por todos os canais habilitados no produto
