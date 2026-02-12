"""
API dependencies.

Authentication, authorization (RBAC),
and security guards used across the API.
"""

from fastapi import Header, HTTPException, Request, Depends, status
from sqlalchemy.orm import Session

from app.core.security import verify_api_key, decode_token
from app.infra.db.repositories.source_repo import get_source_by_name
from app.infra.db.repositories.security_event_repo import create_security_event
from app.infra.db.repositories.user_repo import get_user_by_id
from app.infra.db.session import get_db


def require_api_key_for_ingest(
    request: Request,
    db: Session,
    source: str,
):
    # API key enviada no header (case-insensitive)
    x_api_key = request.headers.get("X-API-Key")

    # Metadados da requisição (auditoria)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    endpoint = str(request.url.path)

    src = None  # Evita uso de locals() / gambiarra
    rid = getattr(request.state, "request_id", None)

    # Função interna para negar acesso e registrar evento de segurança
    def deny(detail: str, event_type: str):
        create_security_event(
            db=db,
            event_type=event_type,
            severity="HIGH",
            source_id=src.id if src else None,
            user_id=None,
            ip=client_ip,
            user_agent=user_agent,
            request_id=rid,
            details={
                "reason": detail,
                "source_name": source,
                "endpoint": endpoint,
            },
        )
        raise HTTPException(status_code=401, detail=detail)

    # 1) Header obrigatório
    if not x_api_key:
        deny("missing X-API-Key", "AUTH_FAILED")

    # 2) Fonte precisa existir e estar ativa
    src = get_source_by_name(db, source)
    if not src or src.status != "active":
        deny("invalid source", "AUTH_FAILED")

    # 3) API key deve bater com o hash salvo
    if not verify_api_key(x_api_key, src.api_key_hash):
        deny("invalid api key", "AUTH_FAILED")

    # Autenticação OK → retorna a fonte autenticada
    return src


def get_current_user(
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
):
    # Header Authorization obrigatório
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing_bearer_token",
        )

    token = authorization.removeprefix("Bearer ").strip()

    # Decodifica e valida JWT
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token",
        )

    # Extrai identidade do usuário
    user_id = payload.get("uid")
    if not isinstance(user_id, int):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_token_payload",
        )

    # Busca usuário no banco
    user = get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="inactive_or_missing_user",
        )

    return user


def require_roles(allowed: list[str]):
    # Conjunto de papéis permitidos
    allowed_set = set(allowed)

    def _dep(user=Depends(get_current_user)):
        # Verifica se o papel do usuário é permitido
        if user.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="forbidden",
            )
        return user

    return _dep