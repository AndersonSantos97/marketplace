from fastapi import FastAPI
from app.routers import products,users,auth, category, product_status, image, orders, payments, reviews, commissions, sales
from app.db.database import create_db_and_tables
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)

app.include_router(category.router)
app.include_router(product_status.router)

app.include_router(image.router)
app.include_router(orders.router)

app.include_router(payments.router)
app.include_router(reviews.router)

app.include_router(commissions.router)

app.include_router(sales.router)