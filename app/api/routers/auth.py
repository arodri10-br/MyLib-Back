from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.security import verify_password, create_access_token
from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginIn(BaseModel):
    username: str
    password: str


class UserOut(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_superuser: bool

    class Config:
        from_attributes = True


@router.post("/login", response_model=TokenOut)
def login(payload: LoginIn, db: Session = Depends(get_db)):
    # Login via JSON (sem multipart/form-data)
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or user.is_active != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário/senha inválidos")
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário/senha inválidos")

    token = create_access_token(subject=user.username)
    return TokenOut(access_token=token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_superuser=bool(current_user.is_superuser == 1),
    )
