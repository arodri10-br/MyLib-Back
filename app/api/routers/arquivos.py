
# -*- coding: utf-8 -*-
"""
api_arquivos.py
- Consulta de metadados dos arquivos carregados em 'files'.
- Filtros por root_id, extensão, tamanho e mtime (epoch seconds).
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.models import File, RootFolderPermission, User
from app.db.database import get_db
from app.core.deps import get_current_user

router = APIRouter(prefix="/files", tags=["Arquivos (Metadados, dependencies=[Depends(get_current_user)])"])

class FileOut(BaseModel):
    id: int
    root_id: int
    path: str
    name: str
    ext: Optional[str]
    size: Optional[int]
    mtime: Optional[int]

    class Config:
        orm_mode = True

@router.get("", response_model=List[FileOut])
def list_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    root_id: Optional[int] = Query(None),
    ext: Optional[str] = Query(None, description="ex.: pdf,docx (uma extensão)"),
    min_size: Optional[int] = Query(None, ge=0),
    max_size: Optional[int] = Query(None, ge=0),
    min_mtime: Optional[int] = Query(None, ge=0, description="epoch seconds"),
    max_mtime: Optional[int] = Query(None, ge=0, description="epoch seconds"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    q = db.query(File)
    conds = []

    if root_id is not None:
        conds.append(File.root_id == root_id)

    if ext:
        e = ext.strip().lower()
        if not e.startswith("."):
            e = "." + e
        conds.append(File.ext == e)

    if min_size is not None:
        conds.append(File.size >= min_size)

    if max_size is not None:
        conds.append(File.size <= max_size)

    if min_mtime is not None:
        conds.append(File.mtime >= min_mtime)

    if max_mtime is not None:
        conds.append(File.mtime <= max_mtime)

    if conds:
        q = q.filter(and_(*conds))

    rows = q.order_by(File.mtime.desc().nullslast(), File.id.asc()).limit(limit).offset(offset).all()
    return rows

@router.get("/{file_id}", response_model=FileOut)
def get_file(file_id: int, db: Session = Depends(get_db)):
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
            raise HTTPException(status_code=403, detail="Sem permissão para este diretório raiz")
    return f
