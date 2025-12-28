
# -*- coding: utf-8 -*-
"""
api_busca.py
- Pesquisa full-text (FTS5) em 'docs' unindo 'files' via 'map'.
- Retorna metadados, snippet e links 'file://' e '/download'.
"""

from typing import Optional, List
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.models import RootFolder, File, RootFolderPermission
from app.db.database import get_db
from app.core.deps import get_current_user, require_root_access

router = APIRouter(prefix="/search", tags=["Busca"], dependencies=[Depends(get_current_user)])

class SearchResult(BaseModel):
    name: str
    ext: str
    path: str
    file_uri: str
    download_url: str
    size: int
    mtime: str
    score: float
    snippet: str

def to_file_uri(windows_path: str) -> str:
    # \\server\share\dir\file.docx -> file://///server/share/dir/file.docx
    p = windows_path.replace("\\", "/")
    p = p.lstrip("/")  # remove barras iniciais extras
    return f"file://///{p}"

@router.get("", response_model=List[SearchResult])
def search(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
    q: str = Query(..., description="Consulta FTS5 (use aspas para frase, AND/OR, NEAR)"),
    ext: Optional[str] = Query(None, description="Filtro por extensões: ex 'pdf,docx,txt'"),
    root_id: Optional[int] = Query(None, description="Filtrar por uma raiz específica"),
    since: Optional[str] = Query(None, description="YYYY-MM-DD"),
    until: Optional[str] = Query(None, description="YYYY-MM-DD"),
    min_size: Optional[int] = Query(None, ge=0),
    max_size: Optional[int] = Query(None, ge=0),
    project: Optional[str] = Query(None, description="Código do projeto para boost"),
    limit: int = Query(50, ge=1, le=500)
):
    # Segurança: se root_id foi informado, exige permissão mínima (reader)
    if root_id is not None and current_user.is_superuser != 1:
        perm = (
            db.query(RootFolderPermission)
            .filter(RootFolderPermission.root_id == root_id, RootFolderPermission.user_id == current_user.id)
            .first()
        )
        if not perm:
            from fastapi import HTTPException, status
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para este diretório raiz")
    # Monta SQL com MATCH + filtros + snippet
    sql_parts = []
    sql_parts.append("""
        SELECT f.id as file_id, f.path, f.name, f.ext, f.size, f.mtime,
               snippet(docs, 0, '[', ']', ' ... ', 8) AS snip,
               CASE 
                 WHEN :project IS NOT NULL AND f.name LIKE '%'||:project||'%' THEN 10.0
                 ELSE 0.0
               END AS boost
        FROM docs
        JOIN map ON docs.rowid = map.rowid_docs
        JOIN files f ON f.id = map.file_id
        WHERE docs MATCH :q
    """)

    params = {"q": q, "project": project}

    # Filtro por extensão
    if ext:
        ext_list = [("." + e.strip().lower()) if not e.strip().startswith(".") else e.strip().lower()
                    for e in ext.split(",") if e.strip()]
        if ext_list:
            # cria IN (?, ?, ?)
            placeholders = ",".join([f":ext{i}" for i in range(len(ext_list))])
            sql_parts.append(f"AND f.ext IN ({placeholders})")
            for i, e in enumerate(ext_list):
                params[f"ext{i}"] = e

    # Filtro por raiz
    if root_id is not None:
        sql_parts.append("AND f.root_id = :root_id")
        params["root_id"] = root_id

    # Datas
    if since:
        since_dt = datetime.strptime(since, "%Y-%m-%d")
        sql_parts.append("AND f.mtime >= :since_epoch")
        params["since_epoch"] = int(since_dt.timestamp())
    if until:
        until_dt = datetime.strptime(until, "%Y-%m-%d")
        sql_parts.append("AND f.mtime <= :until_epoch")
        params["until_epoch"] = int(until_dt.timestamp())

    # Tamanho
    if min_size is not None:
        sql_parts.append("AND f.size >= :min_size")
        params["min_size"] = int(min_size)
    if max_size is not None:
        sql_parts.append("AND f.size <= :max_size")
        params["max_size"] = int(max_size)

    # Ordenação: boost por nome + mtime (estável)
    sql_parts.append("ORDER BY boost DESC, f.mtime DESC")
    sql_parts.append("LIMIT :limit")
    params["limit"] = limit

    final_sql = "\n".join(sql_parts)
    rows = db.execute(text(final_sql), params).fetchall()

    results = []
    for file_id, path, name, extn, size, mtime, snip, boost in rows:
        file_uri = to_file_uri(path)
        download_url = f"/download/{file_id}"
        mtime_iso = datetime.fromtimestamp(mtime).isoformat()
        score = float(boost or 0.0)
        snippet = snip or ""
        results.append(SearchResult(
            name=name, ext=extn or "", path=path, file_uri=file_uri,
            download_url=download_url, size=size or 0, mtime=mtime_iso,
            score=score, snippet=snippet
        ))
    return results