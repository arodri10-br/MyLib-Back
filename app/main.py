# -*- coding: utf-8 -*-
"""
MyLib Back (reorganizado)
- FastAPI + SQLite(FTS5)
- JWT + permissão por diretório raiz (root_id)
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.init_db import init_db
from app.api.router import api_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.APP_NAME)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def _startup():
        init_db()

    @app.get("/health")
    def health():
        return {"status": "ok"}

    app.include_router(api_router)
    return app

app = create_app()
