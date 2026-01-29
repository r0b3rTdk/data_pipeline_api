from pydantic import BaseModel
from typing import Any

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
