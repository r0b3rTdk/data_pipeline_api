"""
Autor: r0b3rT
"""

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.router import api_router
from app.core.errors import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.core.middleware.request_id import RequestIdMiddleware
from app.core.logging import setup_logging
from app.core.settings import settings
from fastapi.middleware.cors import CORSMiddleware
from app.core.middleware.security_headers import SecurityHeadersMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

# Configura logging estruturado
setup_logging(settings.LOG_LEVEL)

# Instância principal da aplicação FastAPI
app = FastAPI(title="Projeto01 - Data Pipeline API")

# Middleware: security headers
app.add_middleware(SecurityHeadersMiddleware)
    
# Middleware: request_id + headers
app.add_middleware(RequestIdMiddleware)

# CORS: configurável via settings   
origins = settings.cors_origins_list()
if origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Handlers: erros padronizados com request_id
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)

# Registro dos módulos de rotas
app.include_router(api_router)
