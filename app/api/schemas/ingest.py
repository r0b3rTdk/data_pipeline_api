from pydantic import BaseModel, Field
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
