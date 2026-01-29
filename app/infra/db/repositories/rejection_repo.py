from sqlalchemy.orm import Session
from sqlalchemy import func
from app.infra.db.models.rejection import Rejection

# Esse padrão permite retornar total + itens, ideal para API paginada.

def insert_rejections(db: Session, rejections: list[Rejection]) -> None:
    # Insere várias rejeições de uma vez
    db.add_all(rejections)
    db.commit()

def list_rejections(
    db: Session,
    category: str | None = None,
    severity: str | None = None,
    page: int = 1,
    page_size: int = 50,
):
    # Query base
    q = db.query(Rejection)

    # Filtros opcionais
    if category:
        q = q.filter(Rejection.category == category)
    if severity:
        q = q.filter(Rejection.severity == severity)

    # Total antes da paginação
    total = q.with_entities(func.count()).scalar() or 0

    # Página atual
    items = (
        q.order_by(Rejection.id.desc())
         .offset((page - 1) * page_size)
         .limit(page_size)
         .all()
    )

    return total, items
