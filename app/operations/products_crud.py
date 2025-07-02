from fastapi import HTTPException
from typing import Optional
from sqlmodel import Session, select
from ..models.db_models import Products
from ..db.database import create_engine, Session

# def get_product_by_id(product_id: int) -> Optional[Product]:
#     with Session(create_engine) as session:
#         statement = select(Product).where(Product.id == product_id)
#         result = session.exec(statement).first()
#         return result
    
def update_product_stock(db: Session, product_id: int, quantity_sold: int):
    """
    Actualiza el stock de un producto y cambia su estado si es necesario
    """
    
    product = db.query(Products).filter(Products.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail=f"Producto {product_id} no encontrado")
    
    if product.stock < quantity_sold:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuficiente para el producto {product.name}. Stock disponible: {product.stock}"
        )
    
    #Rebajar el stock
    product.stock -= quantity_sold
    
    # Si el stock llega a cero, cambiar estado a sold (2)
    if product.stock <= 0:
        product.stock = 0
        product.status = 2  # sold
    
    return product