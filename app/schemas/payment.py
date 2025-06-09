from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

class PaymentBase(SQLModel):
    order_id: int
    provider: str
    payment_ref: str
    status: str

class PaymentCreate(PaymentBase):
    pass

class PaymentRead(PaymentBase):
    id: int
    paid_at: datetime

    class Config:
        orm_mode = True
        
        