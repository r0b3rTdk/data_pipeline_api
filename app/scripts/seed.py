"""
Seed / Bootstrap script

Ensures minimal required data exists:
- Default admin user
- Default source_system (partner_a)

Safe to run multiple times (idempotent).
Usage:
    docker compose exec api python -m app.scripts.seed
"""

from __future__ import annotations

import hashlib
import os

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.infra.db.session import SessionLocal  

from app.infra.db.models.user_account import UserAccount
from app.infra.db.models.source_system import SourceSystem

# Helper para hash de API keys (não é para autenticação, apenas para evitar armazenar chaves em texto claro)
def _hash_api_key(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

# Garante que o usuário admin exista e esteja ativo, atualizando a senha se necessário
def _ensure_admin(db: Session, username: str, password: str) -> None:
    admin = db.execute(
        select(UserAccount).where(UserAccount.username == username)
    ).scalar_one_or_none()

    if not admin:
        admin = UserAccount(
            username=username,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )
        db.add(admin)
    else:
        # mantém seed idempotente (atualiza se mudou)
        admin.password_hash = hash_password(password)
        admin.role = "admin"
        admin.is_active = True

# Garante que a fonte de dados exista e esteja ativa, atualizando a chave se necessário
def _ensure_source(db: Session, name: str, api_key: str) -> None:
    src = db.execute(
        select(SourceSystem).where(SourceSystem.name == name)
    ).scalar_one_or_none()

    api_key_hash = _hash_api_key(api_key)

    if not src:
        src = SourceSystem(
            name=name,
            status="active",
            api_key_hash=api_key_hash,
        )
        db.add(src)
    else:
        src.status = "active"
        src.api_key_hash = api_key_hash

# Roda o seed
def run_seed() -> None:
    # Parâmetros do usuário admin
    admin_user = os.getenv("SEED_ADMIN_USERNAME", "admin")
    admin_pass = os.getenv("SEED_ADMIN_PASSWORD", "admin123")

    # Pararâmetros da fonte de dados (source_system)
    source_name = os.getenv("SEED_SOURCE_NAME", "partner_a")
    source_key = os.getenv("SEED_SOURCE_API_KEY", "partner_a_key_change_me")

    db = SessionLocal()
    try:
        _ensure_admin(db, admin_user, admin_pass)
        _ensure_source(db, source_name, source_key)
        db.commit()
        print("Seed OK")
        print(f"Admin username: {admin_user}")
        print(f"Source name: {source_name}")
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()