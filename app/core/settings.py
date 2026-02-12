"""
Application settings.

Centralizes environment-based configuration.
"""
import os

class Settings:
    
    # JWT (Auth/Login)
    JWT_SECRET: str = os.getenv("JWT_SECRET", "dev-secret-change-me")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    JWT_EXPIRES_MIN: int = int(os.getenv("JWT_EXPIRES_MIN", "60"))

settings = Settings()