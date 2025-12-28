
# -*- coding: utf-8 -*-
"""
api_download.py
- Streaming HTTP de arquivos locais/UNC via caminho absoluto.
"""

import os
import mimetypes
from fastapi import APIRouter, HTTPException, Response, Query

router = APIRouter(prefix="", tags=["Download"])

@router.get("/download")
def download(path: str = Query(..., description="Caminho absoluto (UNC ou local)")):
    if not path:
        raise HTTPException(400, "path obrigatório")
    if not os.path.exists(path):
        # Se o serviço não tiver acesso ao share, retornará 404
        raise HTTPException(404, f"Arquivo não encontrado: {path}")

    def iterfile():
        with open(path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)  # 1MB
                if not chunk:
                    break
                yield chunk

    mime, _ = mimetypes.guess_type(path)
    headers = {"Content-Disposition": f'inline; filename="{os.path.basename(path)}"'}
    return Response(content=iterfile(), media_type=mime or "application/octet-stream", headers=headers)
