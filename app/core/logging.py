"""
Structured logging configuration.

Provides JSON-formatted logs for:
- Application logs
- Security events
- Request tracing

Designed for production-ready observability.
"""
import json
import logging
import sys
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        # Estrutura base do payload de log
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Campos extras úteis (quando existirem)
        for key in ("request_id", "path", "method", "status_code", "process_time_ms"):
            if hasattr(record, key):
                payload[key] = getattr(record, key)

        # Stack trace só no log (não vai pra resposta)
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def setup_logging(level: str = "INFO") -> None:
    root = logging.getLogger()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # evita log duplicado
    root.handlers.clear()
    root.addHandler(handler)