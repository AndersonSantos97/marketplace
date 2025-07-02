import httpx
import os
from dotenv import load_dotenv
from pathlib import Path
from fastapi import HTTPException

dotenv_path = Path(__file__).resolve().parent.parent /".env"
load_dotenv(dotenv_path=dotenv_path)

PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
PAYPAL_SECRET = os.getenv("PAYPAL_SECRET")
PAYPAL_BASE_URL = os.getenv("PAYPAL_BASE_URL")

async def get_access_token():
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
            data={"grant_type": "client_credentials"},
        )
            
        resp.raise_for_status()
        return resp.json()["access_token"]
    
async def create_order(amount: float, currency: str = "USD"):
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    data = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "amount": {
                "currency_code": currency,
                "value": f"{amount:.2f}"
            }
        }],
        "application_context": {
            "return_url": "http://localhost:5173/paypal-redirect",
            "cancel_url": "http://localhost:5173/"
        }
    }
    
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{PAYPAL_BASE_URL}/v2/checkout/orders", headers=headers, json=data)
        resp.raise_for_status()
        return resp.json()
    
async def capture_order(order_id: str):
    token = await get_access_token()
    headers = {
        "Authorization": f"Bearer {token}",
        #"Content-Type": "application/json"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
                headers=headers,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            # PayPal rechazó la captura
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error al capturar orden en PayPal: {e.response.text}"
            )

    data = resp.json()