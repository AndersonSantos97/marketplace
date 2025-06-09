from typing import Optional
from sqlmodel import SQLModel
from datetime import datetime

class UserBase(SQLModel):
    name: str
    email: str
    role: int
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
class UserCreate(UserBase):
    password: str
    
class UserRead(UserBase):
    id: int
    created_at: datetime
    
class UserUpdate(SQLModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[int] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = None #para cambiar password