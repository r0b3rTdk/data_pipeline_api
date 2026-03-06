"""
Authentication endpoints.

- Issues JWT access/refresh tokens via username/password login
- Enforces rate limits and in-memory brute-force blocking by client IP
- Supports refresh token exchange for a new access token
- Emits structured auth logs (success/failure/block/refresh) with request context
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.infra.db.session import get_db
from app.infra.db.repositories.user_repo import get_user_by_username
from app.core.settings import settings
from app.core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.rate_limit import limiter
from app.core.login_attempts import is_blocked, register_failure, reset

# Logger específico para este módulo
logger = logging.getLogger("security.auth")

# Router do módulo de autenticação
router = APIRouter(prefix="/api/v1", tags=["auth"])

# Payload de login
class LoginRequest(BaseModel):
    username: str
    password: str


# Resposta de login (JWT)
class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class RefreshRequest(BaseModel):
    refresh_token: str

# Resposta de refresh (novo JWT)
class RefreshResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Função auxiliar para obter IP do cliente 
def _client_ip(request: Request) -> str:
    return request.headers.get("X-Client-IP") or (request.client.host if request.client else "unknown")

# Função auxiliar para obter User-Agent
def _user_agent(request: Request) -> str:
    return request.headers.get("User-Agent", "")


@router.post("/auth/login", response_model=LoginResponse)
@limiter.limit(lambda: settings.LOGIN_RATE_LIMIT)
def login(
    request: Request,
    payload: LoginRequest,
    db: Session = Depends(get_db),
):
    ip = _client_ip(request)
    ua = _user_agent(request)
    
     # Brute force block
    if is_blocked(ip):
        logger.info(
            "login_blocked", 
            extra={
                "client_ip": ip, 
                "user_agent": ua, 
                "path": str(request.url.path), 
                "method": request.method}
        )
        raise HTTPException(status_code=429, detail="too_many_login_attempts")

    user = get_user_by_username(db, payload.username)
    if not user or not user.is_active:
        register_failure(ip)
        logger.info(
            "login_failed", 
            extra={
                "client_ip": ip, 
                "user_agent": ua, 
                "path": str(request.url.path), 
                "method": request.method}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    if not verify_password(payload.password, user.password_hash):
        register_failure(ip)
        logger.info(
            "login_failed", 
            extra={
                "client_ip": ip, 
                "user_agent": ua, 
                "user_id": int(user.id), 
                "path": str(request.url.path), 
                "method": request.method}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_credentials")

    # sucesso → reseta brute force
    reset(ip)

    access = create_access_token(sub=user.username, role=user.role, user_id=int(user.id))
    refresh = create_refresh_token(sub=user.username, role=user.role, user_id=int(user.id))

    logger.info(
        "login_success",
        extra={
            "client_ip": ip,
            "user_agent": ua,
            "user_id": int(user.id),
            "role": user.role,
            "path": str(request.url.path),
            "method": request.method,
        },
    )
    return LoginResponse(access_token=access, refresh_token=refresh)


@router.post("/auth/refresh", response_model=RefreshResponse)
def refresh_token(
    request: Request,
    payload: RefreshRequest,
):
    ip = _client_ip(request)
    ua = _user_agent(request)

    try:
        data = decode_token(payload.refresh_token)
    except ValueError:
        logger.info(
            "token_refresh_failed", 
            extra={
                "client_ip": ip, 
                "user_agent": ua, 
                "path": str(request.url.path), 
                "method": request.method}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token")

    if data.get("typ") != "refresh":
        logger.info(
            "token_refresh_failed", 
            extra={
                "client_ip": ip, 
                "user_agent": ua, 
                "path": str(request.url.path), 
                "method": request.method}
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid_token_type")

    # Emissão de novo access token
    new_access = create_access_token(
        sub=str(data["sub"]),
        role=str(data["role"]),
        user_id=int(data["uid"]),
    )

    logger.info(
        "token_refresh",
        extra={
            "client_ip": ip,
            "user_agent": ua,
            "user_id": int(data["uid"]),
            "role": str(data["role"]),
            "path": str(request.url.path),
            "method": request.method,
        },
    )
    return RefreshResponse(access_token=new_access)