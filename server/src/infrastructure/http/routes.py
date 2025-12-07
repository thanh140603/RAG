"""
Routes - Infrastructure Layer (HTTP)
Single Responsibility: Register all API routes
"""
from fastapi import FastAPI

from src.infrastructure.http.controllers import (
    auth_controller,
    chat_controller,
    document_controller,
    group_controller,
    rag_controller,
    token_controller,
)


def register_routes(app: FastAPI):
    """
    Register all API routes
    """
    app.include_router(auth_controller.router)
    app.include_router(rag_controller.router)
    app.include_router(document_controller.router)
    app.include_router(group_controller.router)
    app.include_router(chat_controller.router)
    app.include_router(token_controller.router)

