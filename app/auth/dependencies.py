#protecting routes
from fastapi import Depends, HTTPException, status
from jose import JWTError, jwt
from fastapi.security import OAuth2PasswordBearer
from app.models.db_models import Users
from sqlmodel import Session, select
from app.db.database import get_session
from app.auth.auth import SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

def get_current_user(token: str = Depends(oauth2_scheme), session: Session = Depends(get_session)) -> Users:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = session.get(Users, user_id)
    if not user:
        raise credentials_exception
    return user

def require_role(*allowed_roles: str):
    def dependency(current_user: Users = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(status_code=403,
                                detail=f"Access denied. Role '{current_user.role}' not allowed.")
        return current_user
        
    return dependency