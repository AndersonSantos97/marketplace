from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional
from app.models.db_models import Users

from fastapi import Security, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from sqlmodel import Session
from ..db.database import get_session 

#secret key, should be estronger in production 
SECRET_KEY = "myultrasecretkey123"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password):
    return pwd_context.hash(password)

def authenticate_user(email: str, password: str, db_session):
    from sqlmodel import select
    user = db_session.exec(select(Users).where(Users.email == email)).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

def get_current_user(token: str = Security(oauth2_scheme), db: Session = Depends(get_session))->Users:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Token inválido")
        user = db.query(Users).filter(Users.id == int(user_id)).first()
        if not user:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return user
    except JWTError:
        raise HTTPException(status_code=403, detail="Token inválido o expirado")
    pass