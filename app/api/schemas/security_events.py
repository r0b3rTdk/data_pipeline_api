"""
Security event schemas.

DTOs used to expose security audit events via the API.
"""

from pydantic import BaseModel
from typing import Any


class SecurityEventItem(BaseModel):
    id: int # ID do evento
    event_type: str # Tipo do evento (ex: AUTH_FAILED, ACCESS_DENIED)
    severity: str # Severidade do evento
    source_id: int | None # ID da fonte
    user_id: int | None # ID do usuário
    
    # Metadados da requisição
    ip: str | None 
    user_agent: str | None
    request_id: str | None
    
    details: dict[str, Any] | None # Detalhes adicionais do evento
    created_at: str  # Data de criação em formato ISO


class PageResponse(BaseModel):
    page: int # Página atual
    page_size: int # Tamanho da página
    total: int # Total de registros disponíveis
    items: list[SecurityEventItem] # Lista de eventos de seguranca