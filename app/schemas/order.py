from typing import Optional, List
from sqlmodel import SQLModel
from datetime import datetime

class OrderBase(SQLModel):
    buyer_id: int
    total_amount: float
    status: str

class OrderCreate(OrderBase):
    pass

class OrderRead(OrderBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True
        
class OrderItemBase(SQLModel):
    order_id: int
    product_id: int
    quantity: int
    price: float

class OrderItemCreate(OrderItemBase):
    pass

class OrderItemRead(OrderItemBase):
    id: int

    class Config:
        orm_mode = True
        