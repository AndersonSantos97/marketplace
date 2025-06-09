from sqlmodel import SQLModel
from typing import Optional
from datetime import datetime

class ReviewBase(SQLModel):
    user_id: int
    product_id: int
    rating: int
    comment: Optional[str] = None

class ReviewCreate(ReviewBase):
    pass

class ReviewRead(ReviewBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True