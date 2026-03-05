"""
Test configuration.

- Creates database session with SAVEPOINT strategy
- Overrides FastAPI dependency injection
- Provides helpers for authentication tests
"""
import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infra.db.session import get_db
from app.core.security import hash_password

from app.infra.db.models.user_account import UserAccount

from datetime import datetime, timezone
from app.infra.db.models.trusted_event import TrustedEvent
from app.infra.db.models.source_system import SourceSystem
from app.infra.db.models.raw_ingestion import RawIngestion

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL not set in test environment")


engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def db_session():
    """
    Usa SAVEPOINT (begin_nested) para permitir commits dentro da API
    sem quebrar o rollback do teste.
    """
    db = SessionLocal()
    
    # SAVEPOINT para o teste
    db.begin_nested()
    
    # Se o código fizer commit, o savepoint fecha.
    # Este listener recria um novo savepoint automaticamente.
    @event.listens_for(db, "after_transaction_end")
    def _restart_savepoint(session, transaction):
        if transaction.nested and not transaction._parent.nested:
            session.begin_nested()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture()
def client(db_session):
    """
    Override do get_db do FastAPI para usar o db_session do teste.
    """
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def ensure_user(db, username: str, password: str, role: str):
    u = db.query(UserAccount).filter(UserAccount.username == username).one_or_none()
    if not u:
        u = UserAccount(
            username=username,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )
        db.add(u)
        db.flush()
    else:
        u.password_hash = hash_password(password)
        u.role = role
        u.is_active = True
        db.flush()
    return u


def login(client: TestClient, username: str, password: str) -> str:
    r = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    return r.json()["access_token"]

@pytest.fixture()
def trusted_event(db_session):
    # 1) cria source system (source_id obrigatório)
    source = SourceSystem(
        name="ci-source",
        is_active=True,
    )
    db_session.add(source)
    db_session.flush()

    # 2) cria raw ingestion (raw_ingestion_id obrigatório)
    raw = RawIngestion(
        source_id=source.id,
        payload={"hello": "world"},
    )
    db_session.add(raw)
    db_session.flush()

    # 3) cria trusted event (apenas campos que existem no model)
    t = TrustedEvent(
        source_id=source.id,
        raw_ingestion_id=raw.id,
        status="NEW",
    )
    db_session.add(t)
    db_session.flush()
    return t