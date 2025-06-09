from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..models.db_models import Review
from ..schemas.review import ReviewCreate, ReviewRead
from ..db.database import get_session

router = APIRouter(prefix="/reviews", tags=["Reviews"])

@router.post("/", response_model=ReviewRead)
def create_review(review: ReviewCreate, session: Session = Depends(get_session)):
    db_review = Review.from_orm(review)
    session.add(db_review)
    session.commit()
    session.refresh(db_review)
    return db_review

@router.get("/", response_model=list[ReviewRead])
def list_reviews(session: Session = Depends(get_session)):
    return session.exec(select(Review)).all()

@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: int, session: Session = Depends(get_session)):
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    return review

@router.delete("/{review_id}")
def delete_review(review_id: int, session: Session = Depends(get_session)):
    review = session.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")
    session.delete(review)
    session.commit()
    return {"ok": True}