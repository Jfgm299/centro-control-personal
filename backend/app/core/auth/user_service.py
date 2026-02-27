from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.core.auth.user import User
from app.core.auth.refresh_token import RefreshToken
from app.core.auth.user_schema import UserCreate
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, get_refresh_token_expiry
)


def _create_tokens(db: Session, user: User) -> dict:
    """Crea access + refresh token y guarda el refresh en BD"""
    # Limpiar tokens expirados del usuario antes de crear uno nuevo
    db.query(RefreshToken).filter(
        RefreshToken.user_id == user.id,
        RefreshToken.expires_at < datetime.utcnow()
    ).delete()

    access_token = create_access_token({"sub": str(user.id)})
    refresh_token_value = create_refresh_token()

    refresh_token = RefreshToken(
        token=refresh_token_value,
        user_id=user.id,
        expires_at=get_refresh_token_expiry()
    )
    db.add(refresh_token)
    db.commit()

    return {
        "access_token": access_token,
        "refresh_token": refresh_token_value,
        "token_type": "bearer"
    }


def register_user(db: Session, data: UserCreate) -> User:
    if db.query(User).filter(User.email == data.email).first():
        raise HTTPException(status_code=400, detail="El email ya está registrado")
    if db.query(User).filter(User.username == data.username).first():
        raise HTTPException(status_code=400, detail="El username ya está en uso")

    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, email: str, password: str) -> dict:
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )
    return _create_tokens(db, user)


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    token_db = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token,
        RefreshToken.revoked == False,
        RefreshToken.expires_at > datetime.utcnow()
    ).first()

    if not token_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido o expirado"
        )

    user = db.query(User).filter(
        User.id == token_db.user_id,
        User.is_active == True
    ).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no encontrado"
        )

    # Refresh token rotation — revocar el actual y crear uno nuevo
    token_db.revoked = True
    db.commit()

    return _create_tokens(db, user)


def logout_user(db: Session, refresh_token: str) -> None:
    token_db = db.query(RefreshToken).filter(
        RefreshToken.token == refresh_token
    ).first()

    if token_db:
        token_db.revoked = True
        db.commit()