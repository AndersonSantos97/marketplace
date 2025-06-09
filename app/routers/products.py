from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from ..models.product_dto import ProductCreate, ProductRead, ProductUpdate
from ..models.db_models import Products, Users, Image
from ..db.database import create_engine, get_session
from app.auth.dependencies import require_role

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead)
def create_product(product: ProductCreate, current_user: Users = Depends(require_role("admin","artist"))):
    new_product = Products.from_orm(product)
    with Session(create_engine) as session:
        session.add(new_product)
        session.commit()
        session.refresh(new_product)
        return new_product
    
@router.get("/", response_model=list[ProductRead])
def list_products():
    with Session(create_engine) as session:
        products = session.exec(select(Products)).all()
        return products
    
@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int):
    with Session(create_engine) as session:
        product = session.get(Products, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        return product
    
@router.patch("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, data: ProductUpdate):
    with Session(create_engine) as session:
        product = session.get(Products, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        data_dict = data.dict(exclude_unset=True)
        for key, value in data_dict.items():
            setattr(product, key, value)
        session.add(product)
        session.commit()
        session.refresh(product)
        return product
    
@router.delete("/{product_id}")
def delete_product(product_id: int):
    with Session(create_engine) as session:
        product = session.get(Products, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        session.delete(product)
        session.commit
        return {"message": "Producto eliminado correctamente"}
    
    
@router.get("/seller/{user_id}")
def products_by_seller(user_id: int, session: Session = Depends(get_session)):
    statement = (
        select(
            Products.id,
            Products.artist_id,
            Products.title,
            Products.description,
            Products.price,
        ).where(Products.artist_id == user_id)
    )
    
    products_result = session.exec(statement).all()
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
            "image_url": images_dict.get(row.id)
        }
        for row in products_result
    ]
    