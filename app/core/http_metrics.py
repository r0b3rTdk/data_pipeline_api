"""
In-memory metrics counters.

Tracks basic request/error totals, process uptime, and per-route latency stats.
Thread-safe via a lock.
"""

import time
from threading import Lock
from dataclasses import dataclass

_lock = Lock()
_started_at = time.time()

_requests_total = 0
_errors_4xx_total = 0
_errors_5xx_total = 0

# Estrutura para estatísticas por rota
@dataclass
class RouteStats:
    count: int = 0
    total_ms: float = 0.0

_route_stats: dict[str, RouteStats] = {}

def record(status_code: int) -> None:
    global _requests_total, _errors_4xx_total, _errors_5xx_total
    # Atualiza contadores de forma segura 
    with _lock:
        _requests_total += 1
        # Conta respostas 4xx (erros do cliente)
        if 400 <= status_code <= 499:
            _errors_4xx_total += 1
        # Conta respostas 5xx (erros do servidor)
        elif 500 <= status_code <= 599:
            _errors_5xx_total += 1


def snapshot() -> dict:
    # Tira uma “foto” consistente dos numeros
    with _lock:
        # Uptime = há quanto tempo o processo esta de pe
        uptime_seconds = int(time.time() - _started_at)
        return {
            "uptime_seconds": uptime_seconds,
            "requests_total": _requests_total,
            "errors_4xx_total": _errors_4xx_total,
            "errors_5xx_total": _errors_5xx_total,
        }

def record_route(method: str, route: str, duration_ms: float) -> None:
    # Atualiza estatísticas de rota de forma segura
    key = f"{method} {route}"
    with _lock:
        stats = _route_stats.get(key)
        if stats is None:
            stats = RouteStats()
            _route_stats[key] = stats
        stats.count += 1
        stats.total_ms += float(duration_ms)


def routes_snapshot() -> dict:
    # “Foto” consistente das métricas por rota
    with _lock:
        out: dict[str, dict] = {}
        for key, stats in _route_stats.items():
            avg = (stats.total_ms / stats.count) if stats.count else 0.0
            out[key] = {"count": stats.count, "avg_ms": round(avg, 2)}
        return out