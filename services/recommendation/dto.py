from pydantic import BaseModel


class Event(BaseModel):
    user_id: int
    product_id: int
    category: str
    type: str = "view"  # view | purchase
