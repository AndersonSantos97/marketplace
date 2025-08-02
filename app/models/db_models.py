from typing import Optional, List
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime,timedelta
from uuid import uuid4

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    
    products: List["Products"] = Relationship(back_populates="category")
    
class ProductStatus(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str = Field(index=True, unique=True)
    
    products: List["Products"] = Relationship(back_populates="status")
    
class Products(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    artist_id: int = Field(foreign_key="users.id")
    title: str
    description: Optional[str]
    price: float = Field(ge=0)
    is_digital: bool = False
    file_url: Optional[str]
    stock: int = Field(default=1, ge=0)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    category_id: int = Field(foreign_key="category.id")
    status_id: int = Field(foreign_key="productstatus.id")
    
    category: Optional[Category] = Relationship(back_populates="products")
    status: Optional[ProductStatus] = Relationship(back_populates="products")
    images: List["Image"] = Relationship(back_populates="product")
    
class Users(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    email: str = Field(index=True, unique=True)
    password_hash: str
    role: int = Field(foreign_key="roles.id")
    bio: Optional[str]
    avatar_url: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
class Image(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    image_url: str
    
    product: Optional["Products"] = Relationship(back_populates="images")
    
class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    buyer_id: int = Field(foreign_key="users.id")
    total_amount: float
    status: str = "PENDING"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    payment_ref: Optional[str] = None 
    
    items: List["Order_Items"] = Relationship(back_populates="order")
    
class Order_Items(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="products.id")
    quantity: int = Field(ge=1)
    price: float
    
    order: Optional["Order"] = Relationship(back_populates="items")

class Payments(SQLModel, table= True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    provider: str
    payment_ref: str
    status: str
    paid_at: datetime = Field(default_factory=datetime.utcnow)
    
class Review(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    product_id: int = Field(foreign_key="products.id")
    rating: int = Field(ge=1, le=5)
    comment: Optional[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Commission(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id")
    amount: float
    percentage: float = Field(ge=0, le=100)

class Roles(SQLModel, table= True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    
class PasswordResetToken(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid4()), primary_key=True)
    user_id: int
    token: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(hours=1))