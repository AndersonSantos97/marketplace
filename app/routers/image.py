from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from ..models.db_models import Image
from ..db.database import get_session

router = APIRouter(prefix="/images", tags=["Images"])

@router.post("/", response_model=Image)
def create_image(image: Image, session: Session = Depends(get_session)):
    session.add(image)
    session.commit()
    session.refresh(image)
    return image

@router.get("/", response_model=list[Image])
def read_images(session: Session = Depends(get_session)):
    return session.exec(select(Image)).all()

@router.get("/by-product/{product_id}", response_model=List[Image])
def read_images_by_product(product_id: int, session: Session = Depends(get_session)):
    return session.exec(select(Image).where(Image.product_id == product_id)).all()

@router.get("/{image_id}", response_model=Image)
def read_image(image_id: int, session: Session = Depends(get_session)):
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image

@router.put("/{image_id}", response_model=Image)
def update_image(image_id: int, updated: Image, session: Session = Depends(get_session)):
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    image.image_url = updated.image_url
    image.product_id = updated.product_id
    session.add(image)
    session.commit()
    session.refresh(image)
    return image

@router.delete("/{image_id}")
def delete_image(image_id: int, session: Session = Depends(get_session)):
    image = session.get(Image, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    session.delete(image)
    session.commit()
    return {"ok": True, "message": "Image deleted"}