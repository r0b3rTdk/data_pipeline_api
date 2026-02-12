"""
Trusted event schemas.

DTOs for trusted events and controlled update requests.
"""

from pydantic import BaseModel

# Item individual de evento confiável
class TrustedItem(BaseModel):
    id: int
    raw_ingestion_id: int
    source_id: int
    external_id: str
    entity_id: str
    event_type: str
    event_status: str
    event_timestamp: str  # ISO


# Resposta paginada de eventos confiáveis
class PageResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[TrustedItem]


# Request do PATCH /trusted/{id}
class TrustedPatchRequest(BaseModel):
    reason: str # Justificativa obrigatoria para auditoria
    
    # Campos que podem ser alterados
    event_status: str | None = None
    event_type: str | None = None