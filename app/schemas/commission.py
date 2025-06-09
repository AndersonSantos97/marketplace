from sqlmodel import SQLModel
from typing import Optional

class CommissionBase(SQLModel):
    product_id: int
    amount: float
    percentage: float

class CommissionCreate(CommissionBase):
    pass

class CommissionRead(CommissionBase):
    id: int

    class Config:
        orm_mode = True
    
