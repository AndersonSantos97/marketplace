from typing import Optional, List
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
    image_url: Optional[str] = None 
    
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
    image_url: Optional[str] = None 
    
# Modelo para producto con imagen
class ProductWithImage(SQLModel):
    id: int
    artist_id: int
    title: str
    description: Optional[str]
    price: float
    is_digital: bool
    file_url: Optional[str]
    stock: int
    created_at: datetime
    category_id: int
    status_id: int
    image_url: Optional[str] = None  # URL de la imagen
    
class ProductsPaginatedResponse(SQLModel):
    products: List[ProductWithImage]
    category_name: str
    total: int
    page: int
    per_page: int
    total_pages: int
    has_next: bool
    has_prev: bool