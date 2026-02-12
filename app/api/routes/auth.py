"""
Authentication endpoints.

Handles user login and JWT token issuance.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.infra.db.repositories.user_repo import get_user_by_username
from app.core.security import verify_password, create_access_token


# Router do módulo de autenticação
router = APIRouter(prefix="/api/v1", tags=["auth"])


# Payload de login
class LoginRequest(BaseModel):
    username: str
    password: str


# Resposta de login (JWT)
class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/auth/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    # Busca usuário pelo username
    user = get_user_by_username(db, payload.username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )

    # Verifica senha (hash)
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials",
        )

    # Gera JWT com identidade e papel do usuário
    token = create_access_token(
        sub=user.username,
        role=user.role,
        user_id=int(user.id),
    )

    return LoginResponse(access_token=token)