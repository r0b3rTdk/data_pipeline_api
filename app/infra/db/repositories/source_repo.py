from sqlalchemy.orm import Session
from app.infra.db.models.source_system import SourceSystem

# Esse método facilita onboarding automático de novas fontes.

def get_source_by_name(db: Session, name: str) -> SourceSystem | None:
    # Busca uma fonte pelo nome
    return db.query(SourceSystem).filter(SourceSystem.name == name).first()

def create_source_if_missing(db: Session, name: str) -> SourceSystem:
    # Retorna a fonte se existir
    src = get_source_by_name(db, name)
    if src:
        return src

    # Cria a fonte caso não exista
    src = SourceSystem(name=name, status="active")
    db.add(src)
    db.commit()
    db.refresh(src)
    return src
