from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..db.database import get_session
from ..models.db_models import Order, Order_Items
from ..schemas.order import OrderCreate, OrderRead, OrderItemCreate, OrderItemRead
from typing import List

router = APIRouter(prefix="/orders", tags=["Orders"])

#orders

@router.post("/", response_model=OrderRead)
def create_order(order: OrderCreate, session: Session = Depends(get_session)):
    db_order = Order.from_orm(order)
    session.add(db_order)
    session.commit()
    session.refresh(db_order)
    return db_order

@router.get("/", response_model=List[OrderRead])
def list_orders(session: Session = Depends(get_session)):
    return session.exec(select(Order)).all()

@router.get("/{order_id}", response_model=OrderRead)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@router.delete("/{order_id}")
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    session.delete(order)
    session.commit()
    return {"ok": True}

# Order Items

@router.post("/items/", response_model=OrderItemRead)
def create_order_item(item: OrderItemCreate, session: Session = Depends(get_session)):
    db_item = Order_Items.from_orm(item)
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item

@router.get("/items/", response_model=List[OrderItemRead])
def list_order_items(session: Session = Depends(get_session)):
    return session.exec(select(Order_Items)).all()

@router.get("/items/{item_id}", response_model=OrderItemRead)
def get_order_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Order_Items, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@router.delete("/items/{item_id}")
def delete_order_item(item_id: int, session: Session = Depends(get_session)):
    item = session.get(Order_Items, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
    return {"ok": True}

