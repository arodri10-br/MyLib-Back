# -*- coding: utf-8 -*-
"""
Download seguro
- Faz download a partir de file_id (banco), evitando path arbitrário.
- Exige JWT e permissão mínima (reader) no root_id do arquivo.
"""

import os
import mimetypes

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.models import File, RootFolderPermission, User

router = APIRouter(prefix="", tags=["Download"])

@router.get("/download/{file_id}")
def download_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    f = db.query(File).filter(File.id == file_id).first()
    if not f:
        raise HTTPException(status_code=404, detail="Arquivo não encontrado")

    if current_user.is_superuser != 1:
        perm = (
            db.query(RootFolderPermission)
            .filter(RootFolderPermission.root_id == f.root_id, RootFolderPermission.user_id == current_user.id)
            .first()
        )
        if not perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para este diretório raiz")

    path = f.path
    if not path or not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Arquivo não acessível no servidor")

    mime, _ = mimetypes.guess_type(path)
    mime = mime or "application/octet-stream"

    def iterfile():
        with open(path, "rb") as fp:
            while True:
                chunk = fp.read(1024 * 1024)
                if not chunk:
                    break
                yield chunk

    headers = {"Content-Disposition": f'attachment; filename="{f.name}"'}
    return StreamingResponse(iterfile(), media_type=mime, headers=headers)
