from pydantic import BaseModel


class Notice(BaseModel):
    user_id: int
    message: str
    channel: str = "email"
