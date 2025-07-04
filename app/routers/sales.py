from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.db.database import get_session
from ..models.product_dto import ProductRead
from ..models.db_models import Products, Users, Order, Order_Items, Image
from ..db.database import create_engine
from app.auth.dependencies import require_role
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlmodel import select

router = APIRouter(prefix="/sales",tags=["Sales"])

@router.get("/most_sales_now")
def list_most_sales_now(session: Session = Depends(get_session)):
    
    #calc the time 12 hours ago
    twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
    print("HACE DOCE HORAS",twelve_hours_ago)
    
    statement =  (
        select(
            Products.id,
            Products.artist_id,
            Products.title,
            Products.description,
            Products.price,
            Products.stock,
            func.sum(Order_Items.quantity).label("total_sold")
        )
        .join(Order_Items, Products.id == Order_Items.product_id)
        .join(Order, Order_Items.order_id == Order.id)
        .where(Order.created_at >= twelve_hours_ago)
        .group_by(Products.id, 
            Products.artist_id, 
            Products.title, 
            Products.description, 
            Products.price,
            Products.stock)
        .order_by(desc("total_sold"))
        .limit(4)
    )
    
    products_result = session.exec(statement).all()
    
    # Obtener las imágenes de estos productos
    product_ids = [row.id for row in products_result]
    
    if product_ids:
        images_statement = select(Image).where(Image.product_id.in_(product_ids))
        images_result = session.exec(images_statement).all()
        # Crear un diccionario para mapear product_id -> primera imagen
        images_dict = {}
        for image in images_result:
            if image.product_id not in images_dict:
                images_dict[image.product_id] = image.image_url
                
    else:
        images_dict = {}
    
    return [
        {
            "id": row.id,
            "artist_id": row.artist_id,
            "title": row.title,
            "description": row.description,
            "price": row.price,
            "stock": row.stock,
            "image_url": images_dict.get(row.id),
            "total_sold": row.total_sold
        }
        for row in products_result
    ]
    

@router.get("sellers/by-products")
def get_sellers_by_product_count(
    skip: int = 0,
    limit: int = 20,
    session: Session = Depends(get_session)):
    
    statement = (
        select(
            Users.id,
            Users.name,
            Users.email,
            Users.bio,
            Users.avatar_url,
            Users.created_at,
            func.count(Products.id).label("product_count")
        )
        .outerjoin(Products, Users.id == Products.artist_id)
        .where(Users.role == 2)
        .group_by(
            Users.id,
            Users.name,
            Users.email,
            Users.bio,
            Users.avatar_url,
            Users.created_at
        )
        .order_by(desc("product_count"))
        .offset(skip)
        .limit(limit)
    )
    
    result = session.exec(statement).all()
    
    return [
        {
            "id": row.id,
            "name": row.name,
            "email": row.email,
            "bio": row.bio,
            "avatar_url": row.avatar_url,
            "created_at": row.created_at,
            "product_count": row.product_count
        }
        
        for row in result
    ]

#el siguiente es un ejemplo para algo menos complejo
''''
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from sqlmodel import select

@router.get("/most_sales_now", response_model=list[ProductRead])
def list_most_sales_now(session: Session = Depends(get_session)):
    # Calcular el tiempo de hace 12 horas
    twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
    
    # Query para obtener los productos más vendidos en las últimas 12 horas
    statement = (
        select(
            Product,
            func.sum(OrderItem.quantity).label("total_sold")
        )
        .join(OrderItem, Product.id == OrderItem.product_id)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.created_at >= twelve_hours_ago)
        .group_by(Product.id)
        .order_by(desc("total_sold"))
        .limit(4)
    )
    
    result = session.exec(statement).all()
    
    # Extraer solo los productos (sin el total_sold)
    products = [row[0] for row in result]
    
    return products

'''