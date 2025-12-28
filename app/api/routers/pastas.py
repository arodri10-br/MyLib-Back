
# -*- coding: utf-8 -*-
"""
api_pastas.py
CRUD para a tabela root_folders.
"""

from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, Field, validator
from sqlalchemy.orm import Session

from app.models.models import RootFolder
from app.db.database import get_db
from app.core.deps import require_superuser
router = APIRouter(prefix="/roots", tags=["Pastas Raiz"], dependencies=[Depends(require_superuser)])

# -------- Schemas --------
class RootCreate(BaseModel):
    path: str = Field(..., description="Caminho da pasta raiz (UNC ou local)")

    @validator("path")
    def normalize_path(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("path não pode ser vazio")
        return v

class RootUpdate(BaseModel):
    path: Optional[str] = Field(None, description="Atualizar caminho (opcional)")
    last_scan_at: Optional[datetime] = Field(None, description="Data/hora da última verificação")
    files_count: Optional[int] = Field(None, ge=0, description="Estatística futura: número de arquivos")
    total_size_bytes: Optional[int] = Field(None, ge=0, description="Estatística futura: tamanho total em bytes")

    @validator("path")
    def normalize_path(cls, v):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("path não pode ser vazio")
        return v

class RootOut(BaseModel):
    id: int
    path: str
    last_scan_at: Optional[datetime]
    files_count: Optional[int]
    total_size_bytes: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

# -------- Endpoints --------
@router.post("", response_model=RootOut, status_code=201)
def create_root(inp: RootCreate, db: Session = Depends(get_db)):
    # path único
    exists = db.query(RootFolder).filter(RootFolder.path == inp.path).first()
    if exists:
        raise HTTPException(status_code=409, detail="Já existe uma raiz com este path")

    rf = RootFolder(path=inp.path)
    db.add(rf)
    db.commit()
    db.refresh(rf)
    return rf

@router.get("", response_model=List[RootOut])
def list_roots(db: Session = Depends(get_db)):
    rows = db.query(RootFolder).order_by(RootFolder.id.asc()).all()
    return rows

@router.get("/{root_id}", response_model=RootOut)
def get_root(root_id: int, db: Session = Depends(get_db)):
    rf = db.query(RootFolder).filter(RootFolder.id == root_id).first()
    if not rf:
        raise HTTPException(status_code=404, detail="Root não encontrado")
    return rf

@router.put("/{root_id}", response_model=RootOut)
def update_root(root_id: int, inp: RootUpdate, db: Session = Depends(get_db)):
    rf = db.query(RootFolder).filter(RootFolder.id == root_id).first()
    if not rf:
        raise HTTPException(status_code=404, detail="Root não encontrado")

    if inp.path is not None:
        # garantir unicidade de path
        dup = db.query(RootFolder).filter(RootFolder.path == inp.path, RootFolder.id != root_id).first()
        if dup:
            raise HTTPException(status_code=409, detail="Já existe outra raiz com este path")
        rf.path = inp.path

    if inp.last_scan_at is not None:
        rf.last_scan_at = inp.last_scan_at

    if inp.files_count is not None:
        rf.files_count = inp.files_count

    if inp.total_size_bytes is not None:
        rf.total_size_bytes = inp.total_size_bytes

    db.commit()
    db.refresh(rf)
    return rf

@router.delete("/{root_id}", status_code=204)
def delete_root(root_id: int, db: Session = Depends(get_db)):
    rf = db.query(RootFolder).filter(RootFolder.id == root_id).first()
    if not rf:
        raise HTTPException(status_code=404, detail="Root não encontrado")
    db.delete(rf)
    db.commit()
    return Response(status_code=204)
