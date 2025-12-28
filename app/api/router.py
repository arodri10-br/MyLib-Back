from fastapi import APIRouter

from app.api.routers import pastas, scan, indexacao, busca, download, arquivos, auth

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(pastas.router)
api_router.include_router(scan.router)
api_router.include_router(indexacao.router)
api_router.include_router(busca.router)
api_router.include_router(download.router)
api_router.include_router(arquivos.router)
