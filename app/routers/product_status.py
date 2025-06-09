from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from ..models.db_models import ProductStatus
from ..db.database import get_session

router = APIRouter(prefix="/product-statuses", tags=["Product Statuses"])

@router.post("/", response_model=ProductStatus)
def create_status(status: ProductStatus, session: Session = Depends(get_session)):
    existing = session.exec(select(ProductStatus).where(ProductStatus.status == status.status)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Status already exists")
    session.add(status)
    session.commit()
    session.refresh(status)
    return status

@router.get("/", response_model=List[ProductStatus])
def read_statuses(session: Session = Depends(get_session)):
    return session.exec(select(ProductStatus)).all()

@router.get("/{status_id}", response_model=ProductStatus)
def read_status(status_id: int, session: Session = Depends(get_session)):
    status = session.get(ProductStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    return status

@router.put("/{status_id}", response_model=ProductStatus)
def update_status(status_id: int, updated: ProductStatus, session: Session = Depends(get_session)):
    status = session.get(ProductStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    status.status = updated.status
    session.add(status)
    session.commit()
    session.refresh(status)
    return status

@router.delete("/{status_id}")
def delete_status(status_id: int, session: Session = Depends(get_session)):
    status = session.get(ProductStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    session.delete(status)
    session.commit()
    return {"ok": True, "message": "Status deleted"}