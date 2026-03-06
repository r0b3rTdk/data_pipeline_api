"""
In-memory login attempt throttling.

Tracks failed attempts per IP and temporarily blocks after a threshold.
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Dict


@dataclass
class AttemptState:
    count: int  # Quantas falhas já aconteceram
    blocked_until: datetime | None = None  # Até quando esse IP fica bloqueado


_failed: Dict[str, AttemptState] = {}  # Estado por IP (memória do processo)

MAX_ATTEMPTS = 5  # Número máximo de falhas antes de bloquear
BLOCK_MINUTES = 10  # Duração do bloqueio (minutos)


def register_failure(ip: str) -> None:
    # Registra uma falha para o IP e aplica bloqueio ao atingir o limite
    st = _failed.get(ip) or AttemptState(count=0)
    st.count += 1
    if st.count >= MAX_ATTEMPTS:
        st.blocked_until = datetime.now(timezone.utc) + timedelta(minutes=BLOCK_MINUTES)
    _failed[ip] = st


def reset(ip: str) -> None:
    # Remove o histórico desse IP (ex: login bem-sucedido)
    _failed.pop(ip, None)


def is_blocked(ip: str) -> bool:
    # Verifica se o IP está bloqueado agora
    st = _failed.get(ip)
    if not st:
        return False
    if st.blocked_until is None:
        return False

    now = datetime.now(timezone.utc)
    if now >= st.blocked_until:
        # Bloqueio expirou → limpa o estado
        _failed.pop(ip, None)
        return False

    return True


def reset_all() -> None:
    # Zera todos os bloqueios/contadores (útil em testes)
    _failed.clear()