from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from ..models.db_models import Category
from ..db.database import get_session

router = APIRouter(prefix="/categories", tags=["categories"])

@router.post("/", response_model=Category)
def create_category(category: Category, session: Session = Depends(get_session)):
    existing = session.exec(select(Category).where(Category.name == category.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.get("/", response_model=List[Category])
def read_categories(session: Session = Depends(get_session)):
    return session.exec(select(Category)).all()

@router.get("/{category_id}", response_model=Category)
def read_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=Category)
def update_category(category_id: int, updated: Category, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.name = updated.name
    session.add(category)
    session.commit()
    session.refresh(category)
    return category

@router.delete("/{category_id}")
def delete_category(category_id: int, session: Session = Depends(get_session)):
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(category)
    session.commit()
    return {"ok": True, "message": "Category deleted"}