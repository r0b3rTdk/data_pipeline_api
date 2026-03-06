"""
Test configuration.

- Creates database session with SAVEPOINT strategy
- Overrides FastAPI dependency injection
- Provides helpers for authentication tests
"""

import os
import json
import hashlib
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infra.db.session import get_db
from app.core.security import hash_password
from app.core.login_attempts import reset_all

from app.infra.db.models.user_account import UserAccount
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


@pytest.fixture(autouse=True)
def _reset_login_attempts():
    """
    Limpa o estado de brute force entre testes (in-memory).
    """
    reset_all()
    yield
    reset_all()


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
    # 1) SourceSystem (nome único pra não bater UNIQUE em DB persistente)
    source = SourceSystem(
        name=f"ci-source-{uuid4().hex}",
        # status tem default "active", pode omitir
    )
    db_session.add(source)
    db_session.flush()

    # 2) RawIngestion (preencher campos NOT NULL)
    payload_obj = {"hello": "world"}
    payload_raw = json.dumps(payload_obj, separators=(",", ":"), sort_keys=True)
    payload_hash = hashlib.sha256(payload_raw.encode("utf-8")).hexdigest()

    raw = RawIngestion(
        source_id=source.id,
        external_id=f"raw-ci-{uuid4().hex}",
        event_timestamp=datetime.now(timezone.utc),
        payload_raw=payload_raw,
        payload_hash=payload_hash,
        request_id=str(uuid4()),
        # opcionais (client_ip/user_agent) podem ficar vazios
    )
    db_session.add(raw)
    db_session.flush()

    # 3) TrustedEvent (preencher campos NOT NULL)
    t = TrustedEvent(
        raw_ingestion_id=raw.id,
        source_id=source.id,
        external_id=f"trusted-ci-{uuid4().hex}",
        entity_id="ent-1",
        event_type="ORDER",
        event_status="NEW",
        event_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(t)
    db_session.flush()
    return t