from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.db_models import Users
from app.models.user_dto import UserCreate, UserRead, UserUpdate
from passlib.context import CryptContext
from app.auth.dependencies import get_current_user, require_role
from sqlalchemy import func
from sqlalchemy.dialects import mysql

router = APIRouter(prefix="/users", tags=["Users"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

#function to hash password
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

@router.get("/admin")
def admin_dashboard(current_user: Users = Depends(require_role("admin"))):
    return {"msg": "Bienvenido. administrador."}

@router.get("/me")
def read_my_profile(current_user: Users = Depends(get_current_user)):
    return current_user

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    existing_user = session.exec(select(Users).where(Users.email == user.email)).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_data = user.dict(exclude={"password"})
    user_data["password_hash"] = hash_password(user.password)
    db_user = Users(**user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

#get all
@router.get("/", response_model=list[UserRead])
def get_users(session: Session = Depends(get_session)):
    users = session.exec(select(Users)).all()
    return users

#get by id
@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/role/{user_role}", response_model=list[UserRead])
def get_artist(user_role: int, session: Session = Depends(get_session)):
    statement = select(Users).where(Users.role == user_role).order_by(func.rand()) .limit(6)
    #statement = select(Users).join(Roles).where(Users.role == user_role).limit(10)
    artis = session.exec(statement).all()
    if not artis:
        raise HTTPException(status_code=404, detail="User not found")
    return artis

@router.get("/test/{user_role}")
def test_get_users(user_role: int, session: Session = Depends(get_session)):
    users = session.exec(select(Users).where(Users.role == user_role).limit(10)).all()
    return {"count": len(users), "users": [u.name for u in users]}

#update
@router.patch("/{user_id}", response_model=UserRead)
def update_user(user_id: int, updates: UserUpdate, session: Session = Depends(get_session)):
    user = session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_data = updates.dict(exclude_unset=True)
    if "password" in user_data:
        user_data["password_hash"] = hash_password(user_data.pop("password"))
        
    for key, value in user_data.items():
        setattr(user, key, value)
        
    session.add(user)
    session.commit()
    session.refresh(user)
    return user

#delete
@router.delete("/{user_id}")
def delete_user(user_id: int, session: Session = Depends(get_session)):
    user = session.get(Users, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    session.delete(user)
    session.commit()
    return {"message": "user deleted"}

