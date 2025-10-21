from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_current_user,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, Token

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    #Verificar mail
    if db.query(User).filter(User.email == user_data.email).first():
        raise HTTPException(
            status_code=400,
            detail="Email ya esta registrado a un usuario"
        )
    
    #Verificar username
    if db.query(User).filter(User.username == user_data.username).first():
        raise HTTPException(
            status_code=400,
            detail="Un usuario con ese username ya existe"
        )
    
    db_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=get_password_hash(user_data.password),
        is_active=True
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    #Buscar usuario
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=403,
            detail="Usuario inactivo"
        )
    
    user.last_login = datetime.now()
    db.commit()

    #Crear token de acceso
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=UserResponse)
def get_me(
    current_user: User = Depends(get_current_user)
):
    return current_user 