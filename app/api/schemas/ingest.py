"""
Ingestion request schemas.

DTOs that define the payload contract for event ingestion endpoints.
"""

from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime

# Schema do payload de ingestão
class IngestRequest(BaseModel):
    # Identifica a origem do evento (ex: sistema, parceiro, sensor)
    source: str = Field(..., min_length=1)

    # ID externo do evento na origem
    external_id: str = Field(..., min_length=1, max_length=120)

    # Versão do schema para compatibilidade futura
    schema_version: str = Field(default="v1", max_length=20)

    # Entidade relacionada ao evento
    entity_id: str = Field(..., min_length=1, max_length=120)

    # Tipo do evento (ex: created, updated)
    event_type: str = Field(..., min_length=1, max_length=50)

    # Status do evento (ex: success, failed)
    event_status: str = Field(..., min_length=1, max_length=50)

    # Momento real em que o evento ocorreu
    event_timestamp: datetime

    # Dados adicionais livres do evento
    attributes: dict = Field(default_factory=dict)

    # Injeta um exemplo real na documentação do Swagger
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "source": "partner_api_1",
                "external_id": "evt-78901",
                "schema_version": "v1",
                "entity_id": "user-456",
                "event_type": "ACCOUNT_CREATED",
                "event_status": "SUCCESS",
                "event_timestamp": "2026-08-11T20:00:00Z",
                "attributes": {
                    "plan": "premium",
                    "region": "BR"
                }
            }
        }
    )