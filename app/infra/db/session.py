import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# URL de conexão com o banco (vinda do ambiente)
DATABASE_URL = os.getenv("DATABASE_URL")

# Engine do SQLAlchemy
# pool_pre_ping evita conexões quebradas no pool
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

# Factory de sessões do banco
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

def get_db():
    # Cria uma sessão por request
    db = SessionLocal()
    try:
        yield db
    finally:
        # Garante fechamento da sessão
        db.close()
