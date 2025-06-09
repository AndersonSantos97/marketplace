from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from ..models.db_models import Payment, Order, Users
from ..schemas.payment import PaymentCreate, PaymentRead
from ..db.database import get_session
from ..paypal.paypal import create_order, capture_order, get_access_token
from datetime import datetime
import httpx

from app.auth.auth import get_current_user



router = APIRouter(prefix="/payments", tags=["Payments"])

# @router.post("/", response_model=PaymentRead)
# def create_payment(payment: PaymentCreate, session: Session = Depends(get_session)):
#     db_payment = Payment.from_orm(payment)
#     session.add(db_payment)
#     session.commit()
#     session.refresh(db_payment)
#     return db_payment

# @router.get("/", response_model=list[PaymentRead])
# def list_payments(session: Session = Depends(get_session)):
#     return session.exec(select(Payment)).all()

# @router.get("/{payment_id}", response_model=PaymentRead)
# def get_payment(payment_id: int, session: Session = Depends(get_session)):
#     payment = session.get(Payment, payment_id)
#     if not payment:
#         raise HTTPException(status_code=404, detail="Payment not found")
#     return payment

# @router.delete("/{payment_id}")
# def delete_payment(payment_id: int, session: Session = Depends(get_session)):
#     payment = session.get(Payment, payment_id)
#     if not payment:
#         raise HTTPException(status_code=404, detail="Payment not found")
#     session.delete(payment)
#     session.commit()
#     return {"ok": True}


PAYPAL_BASE_URL = "https://api.sandbox.paypal.com"

#UTILIDAD: buscar una orden local asociada al ID de PayPal

def get_order_by_paypal_id(paypal_order_id: str, db: Session) -> Order:
    return db.query(Order).filter(Order.payment_ref == paypal_order_id).first()


@router.post("/create")
async def create_payment(
    amount: float, 
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
    ):
    try:
        order_data = await create_order(amount)
        paypal_order_id = order_data["id"]
        
        #crear orden local en base de datos
        new_order = Order(
            user_id=current_user,
            total_amount=amount,
            payment_ref=paypal_order_id,
            status="PENDING"
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        
        return {
            "message": "Orden creada exitosamente",
            "paypal_order": order_data,
            "local_order_id": new_order.id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/capture/{order_id}")
async def capture_payment(order_id: str, db: Session = Depends(get_session)):
    token = await get_access_token()
    async with httpx.AsyncClient as client:
        resp = await client.post(
            f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {token}"},
        )
        
        resp.raise_for_status()
        data = resp.json()
        
        # Extraer detalles del pago
        capture_info = data["purchase_units"][0]["payments"]["captures"][0]
        paypal_payment_id = capture_info["id"]
        status = capture_info["status"]
        paid_at = capture_info["create_time"]
        
        # Buscar orden local por order_id de PayPal
        order = get_order_by_paypal_id(order_id, db)
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada en la base de datos")
        
        # Crear y guardar el pago en base de datos
        payment = Payment(
            order_id=order.id,
            provider="paypal",
            payment_ref=paypal_payment_id,
            status=status,
            paid_at=datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
        )
        db.add(payment)
        
        # Actualizar estado de la orden
        order.status = "PAID"

        db.commit()
        db.refresh(payment)

        return {
            "message": "Pago capturado y registrado exitosamente",
            "payment_id": payment.id,
            "paypal_status": status
        }
        
    # try:
    #     result = await capture_order(order_id)
    #     return result
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))