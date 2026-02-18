"""
Application settings.

Centralizes environment-based configuration.
Low-risk approach: plain os.getenv (no Pydantic yet).
"""
from __future__ import annotations

import os
from typing import List

class Settings:
    def __init__(self) -> None:
        # Ambiente
        self.APP_ENV: str = os.getenv("APP_ENV", "dev").strip().lower()  # dev|prod
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").strip().upper()
 
        # Banco
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "").strip()

        # JWT (Auth/Login)
        self.JWT_ALG: str = os.getenv("JWT_ALG", "HS256").strip()
        self.JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))
    
        secret = os.getenv("JWT_SECRET")
        
        # Regra segura: em produção, JWT_SECRET tem que existir e não pode ser placeholder
        if self.APP_ENV in ("prod", "production"):
            if not secret or secret.strip() in ("dev-secret-change-me", "change-me-in-production"):
                raise RuntimeError("JWT_SECRET must be set (strong) in production.")
        self.JWT_SECRET: str = (secret or "dev-secret-change-me").strip()

        # Segurança leve
        self.CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "").strip()  # CSV
        self.MAX_BODY_BYTES: int = int(os.getenv("MAX_BODY_BYTES", "1000000"))  # 1MB
        
        # Seed / Bootstrap (Fase 6)
        self.SEED_ON_STARTUP: bool = os.getenv("SEED_ON_STARTUP", "false").strip().lower() == "true"
        self.SEED_ADMIN_EMAIL: str = os.getenv("SEED_ADMIN_EMAIL", "admin@local").strip()
        self.SEED_ADMIN_PASSWORD: str = os.getenv("SEED_ADMIN_PASSWORD", "admin123").strip()
        self.SEED_SOURCE_NAME: str = os.getenv("SEED_SOURCE_NAME", "partner_a").strip()
        self.SEED_SOURCE_API_KEY: str = os.getenv("SEED_SOURCE_API_KEY", "partner_a_key_change_me").strip()
        
        
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "").strip()

    def cors_origins_list(self) -> List[str]:
        if not self.CORS_ORIGINS:
            return []
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
    
settings = Settings()