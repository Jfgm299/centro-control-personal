from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.auth.user_schema import UserCreate, UserResponse, Token, LoginForm, RefreshRequest, LogoutRequest
from app.core.auth.user_service import register_user, login_user, refresh_access_token, logout_user
from app.core.auth.user import User
from app.core.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(data: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, data)


@router.post("/login", response_model=Token)
def login(data: LoginForm, db: Session = Depends(get_db)):
    return login_user(db, data.email, data.password)


@router.post("/refresh", response_model=Token)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)):
    return refresh_access_token(db, data.refresh_token)


@router.post("/logout", status_code=204)
def logout(data: LogoutRequest, db: Session = Depends(get_db)):
    logout_user(db, data.refresh_token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    return current_user