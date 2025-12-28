
# -*- coding: utf-8 -*-
"""
api_scan.py
- Varredura de uma pasta raiz (RootFolder) para carregar/atualizar metadados de arquivos.
- Atualiza estatísticas da raiz: files_count, total_size_bytes, last_scan_at.

Observações:
- Incremental: se o path já existe em 'files', atualiza size/mtime/ext/name.
- Extensões filtráveis via query (?ext=pdf,docx,xlsx). Se não informar, varre todas.
"""

import os
import time
from datetime import datetime
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import RootFolder, File, get_session

router = APIRouter(prefix="/scan", tags=["Scan / Varredura"])

# --------- Schema de resposta ---------
class ScanResult(BaseModel):
    root_id: int
    root_path: str
    candidates: int
    inserted: int
    updated: int
    skipped: int
    errors: int
    total_size_bytes: int
    files_count: int
    elapsed_sec: float
    last_scan_at: str

# --------- Utilidades ---------
def normalize_ext_list(ext: Optional[str]) -> Optional[List[str]]:
    if not ext:
        return None
    items = []
    for e in ext.split(","):
        e = e.strip().lower()
        if not e:
            continue
        if not e.startswith("."):
            e = "." + e
        items.append(e)
    return items or None

# --------- Endpoint de scan ---------
@router.post("/{root_id}", response_model=ScanResult)
def scan_root(
    root_id: int,
    ext: Optional[str] = Query(None, description="Filtro de extensões: ex 'pdf,docx,xlsx'"),
    db: Session = Depends(get_session)
):
    rf = db.query(RootFolder).filter(RootFolder.id == root_id).first()
    if not rf:
        raise HTTPException(status_code=404, detail="Root não encontrado")
    base_path = rf.path

    # Validação básica: aceita UNC ou caminho local; a existência depende do servidor onde roda
    if not base_path:
        raise HTTPException(status_code=400, detail="Path da raiz está vazio")
    if not os.path.exists(base_path) and not base_path.startswith("\\\\"):
        # Se for UNC e o servidor não tiver acesso, ainda permitimos — apenas falhará ao listar
        raise HTTPException(status_code=404, detail=f"Caminho não existe: {base_path}")

    ext_filter = normalize_ext_list(ext)
    t0 = time.time()

    candidates = 0
    inserted = 0
    updated = 0
    skipped = 0
    errors = 0
    total_size = 0
    files_count = 0

    # Caminhamento
    try:
        for root, dirs, files in os.walk(base_path):
            for fn in files:
                candidates += 1
                full = os.path.join(root, fn)
                # Coleta metadados com tolerância a erro
                try:
                    st = os.stat(full)
                    size = int(st.st_size)
                    mtime = int(st.st_mtime)  # epoch seconds
                    name = fn
                    extn = os.path.splitext(fn)[1].lower()
                    if ext_filter and extn not in ext_filter:
                        skipped += 1
                        continue

                    total_size += size
                    files_count += 1

                    # Upsert manual por path
                    rec = db.query(File).filter(File.path == full).first()
                    if rec is None:
                        rec = File(
                            root_id=root_id,
                            path=full,
                            name=name,
                            ext=extn,
                            size=size,
                            mtime=mtime
                        )
                        db.add(rec)
                        inserted += 1
                    else:
                        changed = False
                        if rec.root_id != root_id:
                            rec.root_id = root_id
                            changed = True
                        if rec.name != name:
                            rec.name = name
                            changed = True
                        if rec.ext != extn:
                            rec.ext = extn
                            changed = True
                        if rec.size != size:
                            rec.size = size
                            changed = True
                        if rec.mtime != mtime:
                            rec.mtime = mtime
                            changed = True
                        if changed:
                            updated += 1
                        else:
                            skipped += 1

                    # Commit em lotes leves (melhorar: transações maiores)
                    if (inserted + updated) % 500 == 0:
                        db.commit()

                except Exception:
                    errors += 1
                    # segue adiante
                    continue

        # Commit final e atualização das stats da raiz
        db.commit()
        rf.files_count = files_count
        rf.total_size_bytes = total_size
        rf.last_scan_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Falha ao varrer: {str(e)}")

    dt = time.time() - t0
    return ScanResult(
        root_id=root_id,
        root_path=base_path,
        candidates=candidates,
        inserted=inserted,
        updated=updated,
        skipped=skipped,
        errors=errors,
        total_size_bytes=total_size,
        files_count=files_count,
        elapsed_sec=round(dt, 2),
        last_scan_at=rf.last_scan_at.isoformat() if rf.last_scan_at else ""
    )
