from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.infra.db.session import get_db

# Router modular com prefixo e tag para documentação
router = APIRouter(prefix="/api/v1", tags=["health"])

@router.get("/health")
def health(db: Session = Depends(get_db)):
    # Executa uma query simples só para testar conexão com o banco
    db.execute(text("select 1"))

    # Se chegou aqui, API e banco estão funcionando
    return {"status": "ok"}
