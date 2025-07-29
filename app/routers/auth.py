from fastapi import APIRouter, Depends, HTTPException, status, Body
from jose import JWTError
from sqlalchemy.exc import IntegrityError
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session, select
from app.models.db_models import Users
from app.models.user_dto import UserCreate, UserRead
from app.auth.auth import hash_password, verify_token
from app.db.database import get_session
from app.auth.auth import authenticate_user, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, create_refresh_token
from datetime import timedelta

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), session: Session = Depends(get_session)):
    user = authenticate_user(form_data.username, form_data.password, session)
    if not user:
        raise HTTPException(status_code=400, detail="Invalid Credentials")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "role":user.role}
    )
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "bio": user.bio,
            "avatar_url": user.avatar_url,
            "created_at": user.created_at
        }
    }
    
@router.post("/refresh")
def refresh_token(refresh_token: str = Body(...)):
    try:
        payload = verify_token(refresh_token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Refresh token inválido")

        # Crear nuevo Access Token
        new_access_token = create_access_token({"sub": str(user_id)})
        return {"access_token": new_access_token}
    except JWTError:
        raise HTTPException(status_code=401, detail="Refresh token expirado")

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(user_data: UserCreate, session: Session = Depends(get_session)):
    #verify if the email already exists
    existing_user = session.exec(select(Users).where(Users.email == user_data.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = Users(
        name=user_data.name,
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role="1",
        bio=user_data.bio,
        avatar_url=user_data.avatar_url)
    
    session.add(user)
    try:
        session.commit()
        session.refresh(user)
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=400, detail="User could not be created")
    
    return user