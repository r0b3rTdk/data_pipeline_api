"""
Autor: r0b3rT
Projeto: ...
Data: ...
Descrição: ...
"""

from fastapi import FastAPI, HTTPException
from app.api.router import api_router
from app.core.errors import http_exception_handler, unhandled_exception_handler
from app.core.middleware.request_id import RequestIdMiddleware

# Instância principal da aplicação FastAPI
app = FastAPI(title="Projeto01 - Data Pipeline API")

# Middleware: request_id + headers
app.add_middleware(RequestIdMiddleware)

# Handlers: erros padronizados com request_id
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# Registro dos módulos de rotas
app.include_router(api_router)
