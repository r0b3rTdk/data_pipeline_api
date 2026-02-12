from pydantic import BaseModel


class TopCategoryItem(BaseModel):
    category: str # Categoria de rejeicao
    count: int # Quantidade de ocorrencias dessa categoria


class MetricsResponse(BaseModel):
    total_raw: int # Total de eventos recebidos
    total_trusted: int # Total de eventos aceitos
    total_rejected: int # Total de eventos rejeitados
    rejection_rate: float # Percentual de rejeicao
    duplicates: int # Total de eventos duplicados
    top_rejection_categories: list[TopCategoryItem] # Ranking de categorias de rejeicao