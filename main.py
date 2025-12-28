
# -*- coding: utf-8 -*-
"""
main.py
- Inicializa FastAPI
- Registra routers (pastas, scan, indexação, busca, download, app principal e página pastas)
- Cria DB na inicialização
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import init_db
from api_pastas import router as root_router
from api_scan import router as scan_router
from api_indexacao import router as index_router
from api_busca import router as search_router
from api_download import router as download_router
from api_arquivos import router as files_router

from app_pastas import router as app_pastas_router
from app_principal import router as app_principal_router
from app_arquivos import router as app_arquivos_router

app = FastAPI(title="Doc Index API (Local)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/health")
def health():
    return {"status": "ok"}

# APIs
app.include_router(root_router)
app.include_router(scan_router)
app.include_router(index_router)
app.include_router(search_router)
app.include_router(download_router)
app.include_router(files_router)

# UI
app.include_router(app_pastas_router)      # /app/pastas (página de cadastro/gestão)
app.include_router(app_principal_router)   # /app/principal (principal com sidebar)
app.include_router(app_arquivos_router)    