from pydantic import BaseModel

# Item individual de rejeição
class RejectionItem(BaseModel):
    id: int
    raw_ingestion_id: int        # ID do evento bruto
    category: str                # Tipo da rejeição
    field: str | None = None     # Campo afetado (se houver)
    rule: str | None = None      # Regra violada (se houver)
    severity: str                # Nível da rejeição
    message: str                 # Mensagem explicativa
    created_at: str              # Data em ISO

# Resposta paginada de rejeições
class PageResponse(BaseModel):
    page: int
    page_size: int
    total: int
    items: list[RejectionItem]
