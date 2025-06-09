from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..models.db_models import Commission
from ..schemas.commission import CommissionCreate, CommissionRead
from ..db.database import get_session

router = APIRouter(prefix="/commissions", tags=["Commissions"])

@router.post("/", response_model=CommissionRead)
def create_commission(commission: CommissionCreate, session: Session = Depends(get_session)):
    db_commission = Commission.from_orm(commission)
    session.add(db_commission)
    session.commit()
    session.refresh(db_commission)
    return db_commission

@router.get("/", response_model=list[CommissionRead])
def list_commissions(session: Session = Depends(get_session)):
    return session.exec(select(Commission)).all()

@router.get("/{commission_id}", response_model=CommissionRead)
def get_commission(commission_id: int, session: Session = Depends(get_session)):
    commission = session.get(Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    return commission

@router.delete("/{commission_id}")
def delete_commission(commission_id: int, session: Session = Depends(get_session)):
    commission = session.get(Commission, commission_id)
    if not commission:
        raise HTTPException(status_code=404, detail="Commission not found")
    session.delete(commission)
    session.commit()
    return {"ok": True}