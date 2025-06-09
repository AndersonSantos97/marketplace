from typing import Optional
from sqlmodel import Session, select
from ..models.db_models import Product
from ..db.database import create_engine

def get_product_by_id(product_id: int) -> Optional[Product]:
    with Session(create_engine) as session:
        statement = select(Product).where(Product.id == product_id)
        result = session.exec(statement).first()
        return result