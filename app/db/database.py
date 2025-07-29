import os
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlmodel import SQLModel, create_engine, Session
from dotenv import load_dotenv
from pathlib import Path

# Cargar variables del .env

# dotenv_path = Path(__file__).resolve().parent.parent /".env"
# load_dotenv(dotenv_path=dotenv_path)
load_dotenv() 

SQLACHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

if not SQLACHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL no está definida en el archivo .env")

engine = create_engine(SQLACHEMY_DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
        
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)