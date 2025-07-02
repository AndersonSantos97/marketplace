from pydantic import BaseModel
from typing import List

class ItemData(BaseModel):
    product_id: int
    quantity: int
    price: float


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int
    price: float

class OrderCreatePayload(BaseModel):
    amount: float
    items: List[OrderItemCreate]
