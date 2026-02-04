from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.api.deps import require_api_key_for_ingest
from app.api.schemas.ingest import IngestRequest
from app.infra.db.session import get_db
from app.services.ingest_service import ingest_event

# Router do módulo de ingestão
router = APIRouter(prefix="/api/v1", tags=["ingest"])

@router.post("/ingest")
def ingest(
    req: IngestRequest,              # Payload validado pelo Pydantic
    request: Request,                # Request bruto (headers, IP, etc.)
    db: Session = Depends(get_db)    # Sessão do banco
):
    # valida api key (401 se falhar)
    require_api_key_for_ingest(request=request,db=db, source=req.source)
    
    # IP do cliente (pode ser None em alguns ambientes)
    client_ip = request.client.host if request.client else None

    # User-Agent enviado pelo cliente
    user_agent = request.headers.get("user-agent")

    # Delegação da lógica para a camada de serviço
    return ingest_event(db, req, client_ip, user_agent)
