from fastapi import Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.security import verify_api_key
from app.infra.db.repositories.source_repo import get_source_by_name
from app.infra.db.repositories.security_event_repo import create_security_event


def require_api_key_for_ingest(
    request: Request,
    db: Session,
    source: str,
):
    # pega do request (case-insensitive)
    x_api_key = request.headers.get("X-API-Key")
    
    # Metadados da requisição (para auditoria)
    client_ip = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    endpoint = str(request.url.path)
    
    src = None  # <-- evita gambiarra com locals()


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
            request_id=None,
            details={
            "reason": detail,
            "source_name": source,
            "endpoint": endpoint,
            "request_id": request.headers.get("x-request-id")  # se existir

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

    # 3) API key precisa bater com o hash salvo
    if not verify_api_key(x_api_key, src.api_key_hash):
        deny("invalid api key", "AUTH_FAILED")

    # Autenticação OK → retorna a fonte autenticada
    return src
