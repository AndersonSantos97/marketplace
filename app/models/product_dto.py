from typing import Optional
from sqlmodel import SQLModel, Field
from datetime import datetime

class ProductBase(SQLModel):
    title: str
    description: Optional[str] = None
    price: float
    is_digital: bool = False
    file_url: Optional[str] = None
    stock: int
    category_id: int
    status_id: int
    
class ProductCreate(ProductBase):
    artist_id: int
    
class ProductRead(ProductBase):
    id: int
    artist_id: int
    created_at: datetime
    
class ProductUpdate(SQLModel):
    title: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    is_digital: Optional[bool] = None
    file_url: Optional[str] = None
    stock: Optional[int] = None
    category_id: Optional[int] = None
    status_id: Optional[int] = None