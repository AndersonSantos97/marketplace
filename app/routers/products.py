from fastapi import APIRouter, HTTPException, Depends, status, Query
from sqlmodel import Session, select
from ..models.product_dto import ProductCreate, ProductRead, ProductUpdate, ProductsPaginatedResponse, ProductWithImage, InactiveProductResponse, ProductImageResponse, ProductStatusUpdateRequest, ProductStatusUpdateResponse
from ..models.db_models import Products, Users, Image, Category, ProductStatus
from ..db.database import create_engine, get_session
from app.auth.dependencies import require_role
from sqlalchemy import func
from typing import List, Optional
from math import ceil
from app.auth.auth import get_current_user
from sqlalchemy.orm import selectinload

router = APIRouter(prefix="/products", tags=["Products"])

@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(product: ProductCreate, session: Session = Depends(get_session)):
    try:
        # Excluir image_url porque va a otra tabla
        product_data = product.model_dump(exclude={"image_url"})
        new_product = Products(**product_data)

        # Guardar el producto
        session.add(new_product)
        session.flush()  # Para obtener el ID del nuevo producto

        # Guardar la imagen asociada si viene
        if product.image_url:
            product_image = Image(
                product_id=new_product.id,
                image_url=product.image_url
            )
            session.add(product_image)

        session.commit()
        session.refresh(new_product)
        return new_product

    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear el producto: {str(e)}"
        )
        
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
def update_product(product_id: int, data: ProductUpdate, session: Session = Depends(get_session)):
        product = session.get(Products, product_id)
        if not product:
            raise HTTPException(status_code=404, detail="Producto no encontrado")
        data_dict = data.model_dump(exclude_unset=True, exclude={"image_url"})
        for key, value in data_dict.items():
            setattr(product, key, value)
        
            # Manejar la imagen si se proporciona
        if data.image_url is not None:
            # Buscar imagen existente
            existing_image = session.exec(
                select(Image).where(Image.product_id == product_id)
            ).first()
            
            if data.image_url == "":
                # Eliminar imagen si se envía string vacío
                if existing_image:
                    session.delete(existing_image)
            else:
                # Actualizar imagen existente o crear nueva
                if existing_image:
                    existing_image.image_url = data.image_url
                else:
                    new_image = Image(
                        product_id=product_id,
                        image_url=data.image_url
                    )
                    session.add(new_image)
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
            Products.stock
        ).where(Products.artist_id == user_id)
        .where(Products.status_id == 1)
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
            "image_url": images_dict.get(row.id),
            "stock": row.stock
        }
        for row in products_result
    ]
    
@router.get("/seller2/{user_id}")
def products_by_seller(user_id: int, session: Session = Depends(get_session)):
    statement = (
        select(
            Products.id,
            Products.artist_id,
            Products.title,
            Products.description,
            Products.price,
            Products.stock
        ).where(Products.artist_id == user_id)
        .where(Products.status_id == 1)
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
            "image_url": images_dict.get(row.id),
            "stock": row.stock
        }
        for row in products_result
    ]
    
@router.get("/by-categories/")
def get_products_by_categories(
    limit_per_category: int = 10,
    session: Session = Depends(get_session)
):
    #subconsulta para limitar productos por categoria
    ranked_products = (
        select(
            Products.id,
            Products.artist_id,
            Products.title,
            Products.description,
            Products.price,
            Products.is_digital,
            Products.stock,
            Products.created_at,
            Products.category_id,
            func.row_number().over(
                partition_by=Products.category_id,
                order_by=Products.created_at.desc()
            ).label("rn")
        )
        .where(Products.status_id != 3)
        .subquery()
    )
    
    #consulta principal con JOIN
    statement = (
        select(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            ranked_products.c.id,
            ranked_products.c.artist_id,
            ranked_products.c.title,
            ranked_products.c.description,
            ranked_products.c.price,
            ranked_products.c.is_digital,
            ranked_products.c.stock,
            ranked_products.c.created_at
        )
        .join(ranked_products, Category.id == ranked_products.c.category_id)
        .where(ranked_products.c.rn <= limit_per_category)
        .order_by(Category.name, ranked_products.c.created_at.desc())
    )
    
    products_result = session.exec(statement).all()
    
    #obtener todas las imagenes de una vez
    product_ids = [row.id for row in products_result]
    
    if product_ids:
        images_statement = select(Image).where(Image.product_id.in_(product_ids))
        images_result = session.exec(images_statement).all()
        
        images_dict = {}
        for image in images_result:
            if image.product_id not in images_dict:
                images_dict[image.product_id] = image.image_url
    else:
        images_dict = {}
        
    #agrupar por categoria
    categories_dict = {}
    
    for row in products_result:
        if row.category_id not in categories_dict:
            categories_dict[row.category_id] = {
                "category_id": row.category_id,
                "category_name": row.category_name,
                "products": [],
                "total_products": 0
            }
        
        categories_dict[row.category_id]["products"].append({
            "id": row.id,
            "artist_id": row.artist_id,
            "title": row.title,
            "description": row.description,
            "price": row.price,
            "is_digital": row.is_digital,
            "stock": row.stock,
            "image_url": images_dict.get(row.id),
            "created_at": row.created_at
        })
        
        categories_dict[row.category_id]["total_products"] += 1
    
    return list(categories_dict.values())


@router.get("/by-category/{category_code}", response_model=ProductsPaginatedResponse)
def get_products_by_category(
    category_code: str,
    page: int = Query(1, ge=1, description="Número de página (mínimo 1)"),
    per_page: int = Query(10, ge=1, le=100, description="Productos por página (1-100)"),
    session: Session = Depends(get_session)
):
    """
    Obtener productos por código de categoría con paginación e imágenes.
    
    - **category_code**: Código de la categoría
    - **page**: Número de página (por defecto 1)
    - **per_page**: Cantidad de productos por página (por defecto 10, máximo 100)
    """
    
    #verificar que la categoria exista
    category_stmt = select(Category).where(Category.id == category_code)
    category = session.exec(category_stmt).first()
    
    if not category:
        raise HTTPException(status_code=404, detail=f"Categoría con código '{category_code}' no encontrada")
    
    #CONTAR TOTAL DE PRODUCTOS EN LA CATEGORIA
    count_stmt = select(func.count(Products.id)).where(Products.category_id == category.id)
    total_products = session.exec(count_stmt).one()
    
    # Calcular offset para la paginación
    offset = (page - 1) * per_page
    
    # Consulta principal con LEFT JOIN para incluir imágenes
    products_stmt = (
        select(Products, Image.image_url)
        .outerjoin(Image, Products.id == Image.product_id)
        .where(Products.category_id == category.id)
        .where(Products.status_id != 3)
        .order_by(Products.created_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    
    results = session.exec(products_stmt).all()
    
    # Convertir resultados a ProductWithImage
    products_with_images = []
    for product, image_url in results:
        product_dict = product.model_dump()
        product_dict["image_url"] = image_url
        products_with_images.append(ProductWithImage(**product_dict))
        
    # Calcular metadatos de paginación
    total_pages = ceil(total_products / per_page) if total_products > 0 else 1
    has_next = page < total_pages
    has_prev = page > 1
    
    
    return ProductsPaginatedResponse(
        products=products_with_images,
        category_name=category.name, 
        total=total_products,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
        has_next=has_next,
        has_prev=has_prev
    )
    
# Endpoint para obtener productos inactivos del vendedor
@router.get("/seller/inactive/{seller_id}", response_model=List[InactiveProductResponse])
async def get_inactive_products(
    seller_id: int,
    status_id: int = 3,
    session: Session = Depends(get_session)
):
    """
    Obtiene todos los productos inactivos (status_id = 3) del vendedor especificado.
    Incluye las imágenes de cada producto.
    """
    
    try:
        
        # Query para obtener productos inactivos del vendedor especificado
        statement = (
            select(Products)
            .where(Products.artist_id == seller_id)
            .where(Products.status_id == status_id)
        )
        
        products = session.exec(statement).all()
        
        if not products:
            return []
        
        # Preparar respuesta con imágenes
        response_products = []
        
        for product in products:
            # Obtener imágenes del producto
            images_statement = select(Image).where(Image.product_id == product.id).limit(1)
            first_image = session.exec(images_statement).first()
            
            # Obtener URL de la primera imagen, si existe
            image_url = first_image.image_url if first_image else None
            # Crear response del producto
            product_response = InactiveProductResponse(
                id=product.id,
                title=product.title,
                description=product.description,
                price=product.price,
                is_digital=product.is_digital,
                file_url=product.file_url,
                stock=product.stock,
                created_at=product.created_at,
                category_id=product.category_id,
                status_id=product.status_id,
                image_url=image_url
            )
            
            response_products.append(product_response)
        
        return response_products
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener productos inactivos: {str(e)}"
        )
        
# Endpoint para actualizar estado de producto (activar/desactivar)
@router.patch("/active/{product_id}", response_model=ProductStatusUpdateResponse)
async def activate_product(
    product_id: int,
    session: Session = Depends(get_session)
):
    """
    Activa un producto (cambia status_id a 1).
    """
    try:
        # Verificar que el producto existe
        product = session.get(Products, product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Producto no encontrado"
            )
        
        # Verificar que el producto no esté ya activo
        if product.status_id == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El producto ya está activo"
            )
        
        # Verificar que el status_id 1 existe en la base de datos
        status_statement = select(ProductStatus).where(ProductStatus.id == 1)
        product_status = session.exec(status_statement).first()
        
        if not product_status:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Estado de producto activo no encontrado en el sistema"
            )
        
        # Actualizar el estado del producto a activo
        product.status_id = 1
        session.add(product)
        session.commit()
        session.refresh(product)
        
        return ProductStatusUpdateResponse(
            success=True,
            message="Producto activado exitosamente",
            product_id=product.id,
            new_status_id=1
        )
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al activar producto: {str(e)}"
        )


@router.get("/search/alike/", response_model=List[ProductWithImage])
def search_products(query: str = Query(..., min_length=1), session: Session = Depends(get_session)):
    statement = select(Products).where(Products.title.ilike(f"%{query}%")).options(selectinload(Products.images))
    results = session.exec(statement).all()

    # Transformar a lista de productos con solo una imagen
    products_with_image = []
    for product in results:
        main_image_url = product.images[0].image_url if product.images else None
        products_with_image.append(ProductWithImage(
            id=product.id,
            artist_id=product.artist_id,
            title=product.title,
            description=product.description,
            price=product.price,
            is_digital=product.is_digital,
            stock=product.stock,
            created_at=product.created_at,
            category_id=product.category_id,
            status_id=product.status_id,
            file_url = product.file_url,
            image_url=main_image_url
        ))

    return products_with_image

# async def update_product_status(
#     product_id: int,
#     request: ProductStatusUpdateRequest,
#     session: Session = Depends(get_session)
# ):
#     """
#     Actualiza el estado de un producto.
#     Solo el propietario del producto puede modificar su estado.
#     """
#     try:
#         # Verificar que el producto existe
#         product = session.get(Products, product_id)
        
#         if not product:
#             raise HTTPException(
#                 status_code=status.HTTP_404_NOT_FOUND,
#                 detail="Producto no encontrado"
#             )
        
#         # Validar que el status_id es válido (1 = activo, 3 = inactivo)
#         if request.status_id not in [1, 3]:
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail="Estado de producto inválido. Use 1 para activo o 3 para inactivo"
#             )
        
#         # Verificar que el estado ya no es el mismo
#         if product.status_id == request.status_id:
#             status_name = "activo" if request.status_id == 1 else "inactivo"
#             raise HTTPException(
#                 status_code=status.HTTP_400_BAD_REQUEST,
#                 detail=f"El producto ya está {status_name}"
#             )
        
#         # Verificar que el status_id existe en la base de datos
#         status_statement = select(ProductStatus).where(ProductStatus.id == request.status_id)
#         product_status = session.exec(status_statement).first()
        
#         if not product_status:
#             raise HTTPException(
#                 status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#                 detail="Estado de producto no encontrado en el sistema"
#             )
        
#         # Actualizar el estado del producto
#         old_status_id = product.status_id
#         product.status_id = request.status_id
#         session.add(product)
#         session.commit()
#         session.refresh(product)
        
#         # Determinar mensaje según el cambio
#         if request.status_id == 1:
#             message = "Producto activado exitosamente"
#         else:
#             message = "Producto desactivado exitosamente"
        
#         return ProductStatusUpdateResponse(
#             success=True,
#             message=message,
#             product_id=product.id,
#             new_status_id=request.status_id
#         )
        
#     except HTTPException:
#         raise
#     except Exception as e:
#         session.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error al actualizar estado del producto: {str(e)}"
#         )

# Endpoint adicional para obtener productos por estado (útil para el futuro)
@router.get("/products/seller/{seller_id}/status/{status_id}", response_model=List[InactiveProductResponse])
async def get_products_by_status(
    seller_id: int,
    status_id: int,
    session: Session = Depends(get_session)
):
    """
    Obtiene productos de un vendedor filtrados por estado.
    Útil para obtener productos activos (status_id=1) o inactivos (status_id=3).
    """
    try:
        # Query para obtener productos del vendedor por estado
        statement = (
            select(Products)
            .where(Products.artist_id == seller_id)
            .where(Products.status_id == status_id)
        )
        
        products = session.exec(statement).all()
        
        if not products:
            return []
        
        # Preparar respuesta con imágenes
        response_products = []
        
        for product in products:
            # Obtener imágenes del producto
            images_statement = select(Image).where(Image.product_id == product.id)
            images = session.exec(images_statement).all()
            
            # Convertir imágenes a response model
            product_images = [
                ProductImageResponse(
                    id=image.id,
                    image_url=image.image_url
                )
                for image in images
            ]
            
            # Crear response del producto
            product_response = InactiveProductResponse(
                id=product.id,
                title=product.title,
                description=product.description,
                price=product.price,
                is_digital=product.is_digital,
                file_url=product.file_url,
                stock=product.stock,
                created_at=product.created_at,
                category_id=product.category_id,
                status_id=product.status_id,
                images=product_images
            )
            
            response_products.append(product_response)
        
        return response_products
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener productos por estado: {str(e)}"
        )