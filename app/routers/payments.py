from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session, select
from ..models.db_models import Payments, Order, Users, Order_Items, Products
from ..schemas.payment import PaymentCreate, PaymentRead
from ..db.database import get_session
from ..paypal.paypal import create_order, capture_order, get_access_token
from datetime import datetime
import httpx
from typing import List
from ..models.order_dto import OrderCreatePayload
from ..operations.products_crud import update_product_stock
#from models.order_dto import ItemData, OrderCreatePayload, OrderItemCreate

from app.auth.auth import get_current_user

router = APIRouter(prefix="/payments", tags=["Payments"])


PAYPAL_BASE_URL = "https://api.sandbox.paypal.com"

#UTILIDAD: buscar una orden local asociada al ID de PayPal

def get_order_by_paypal_id(paypal_order_id: str, db: Session) -> Order:
    return db.query(Order).filter(Order.payment_ref == paypal_order_id).first()


@router.post("/create")
async def create_payment(
    payload: OrderCreatePayload,
    db: Session = Depends(get_session),
    current_user: Users = Depends(get_current_user)
    ):
    try:
        
        # Verificar stock
        for item in payload.items:
            product = db.exec(select(Products).where(Products.id == item.product_id)).first()
            if not product:
                raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado.")
            if product.stock <= 0:
                raise HTTPException(status_code=400, detail=f"El producto '{product.title}' está agotado.")
            if item.quantity > product.stock:
                raise HTTPException(
                    status_code=400,
                    detail=f"Cantidad solicitada de '{product.title}' excede el stock disponible ({product.stock})."
                )
        order_data = await create_order(payload.amount)
        paypal_order_id = order_data["id"]
        
        #crear orden local en base de datos
        new_order = Order(
            buyer_id=current_user.id,
            total_amount=payload.amount,
            payment_ref=paypal_order_id,
            status="PENDING"
        )
        db.add(new_order)
        db.flush()
        # db.commit()
        # db.refresh(new_order)
        
        #agregar detalles de la order
        for item in payload.items:
            order_item = Order_Items(
                order_id=new_order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price
            )
            db.add(order_item)
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
    try:
        token = await get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json"
                },
                json={}
            )

        resp.raise_for_status()
        data = resp.json()

        capture_info = data["purchase_units"][0]["payments"]["captures"][0]
        paypal_payment_id = capture_info["id"]
        status = capture_info["status"]
        paid_at = capture_info["create_time"]

        order = get_order_by_paypal_id(order_id, db)
        if not order:
            raise HTTPException(status_code=404, detail="Orden no encontrada en la base de datos")

        # Crear el pago
        payment = Payments(
            order_id=order.id,
            provider="paypal",
            payment_ref=paypal_payment_id,
            status=status,
            paid_at=datetime.fromisoformat(paid_at.replace("Z", "+00:00"))
        )
        db.add(payment)        
        order.status = "PAID"
        db.commit()
        db.refresh(payment)

        return {
            "message": "Pago capturado y registrado exitosamente",
            "payment_id": payment.id,
            "paypal_status": status
        }

    except httpx.HTTPStatusError as e:
        return JSONResponse(
            status_code=e.response.status_code,
            content={"detail": f"Error al capturar en PayPal: {e.response.text}"}
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"detail": f"Error inesperado: {str(e)}"}
        )

@router.post("/confirm/{paypal_order_id}")
def confirm_payment(paypal_order_id: str, db: Session = Depends(get_session)):
    order = get_order_by_paypal_id(paypal_order_id, db)
    if not order:
        raise HTTPException(status_code=404, detail="Orden no encontrada")

    # Verifica si ya está pagada
    if order.status == "PAID":
        return {"message": "La orden ya fue registrada como pagada"}

    # 3️⃣ Descontar stock de cada producto
    for item in order.items:
        product = db.exec(
            select(Products).where(Products.id == item.product_id)
        ).first()

        if not product:
            raise HTTPException(status_code=404, detail=f"Producto {item.product_id} no encontrado.")

        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"No hay stock suficiente para el producto '{product.title}'."
            )

        product.stock -= item.quantity
         # Si el stock llegó a cero, cambiar el estado del producto
        if product.stock == 0:
            product.status_id = 2  
    
    # Registrar pago
    payment = Payments(
        order_id=order.id,
        provider="paypal",
        payment_ref=paypal_order_id,
        status="COMPLETED",
        paid_at=datetime.utcnow(),
    )
    db.add(payment)
    order.status = "PAID"
    db.commit()
    db.refresh(payment)

    return {"message": "Pago confirmado en el backend", "payment_id": payment.id}
    # try:
    #     result = await capture_order(order_id)
    #     return result
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=str(e))