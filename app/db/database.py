from sqlalchemy.orm import sessionmaker, declarative_base
from sqlmodel import SQLModel, create_engine, Session

SQLACHEMY_DATABASE_URL = "mysql+pymysql://root:Conexion+2025@localhost/marketplacedb"

engine = create_engine(SQLACHEMY_DATABASE_URL, echo=True)

def get_session():
    with Session(engine) as session:
        yield session
        
def create_db_and_tables():
    SQLModel.metadata.create_all(engine)