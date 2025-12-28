from __future__ import annotations

from typing import Callable, Optional

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.db.database import get_db
from app.models.models import User, RootFolderPermission

bearer_scheme = HTTPBearer(auto_error=True)

_ACCESS_ORDER = {"reader": 1, "editor": 2, "admin": 3}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = decode_token(token)
        username = payload.get("sub")
        if not username:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado")

    user = db.query(User).filter(User.username == username).first()
    if not user or user.is_active != 1:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário inativo ou inexistente")
    return user


def require_superuser(current_user: User = Depends(get_current_user)) -> User:
    if current_user.is_superuser != 1:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Acesso restrito (superuser)")
    return current_user


def require_root_access(min_level: str) -> Callable:
    if min_level not in _ACCESS_ORDER:
        raise ValueError(f"Nível inválido: {min_level}")

    def _dep(
        root_id: int = Path(..., ge=1),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db),
    ) -> int:
        if current_user.is_superuser == 1:
            return root_id

        perm = (
            db.query(RootFolderPermission)
            .filter(
                RootFolderPermission.root_folder_id == root_id,
                RootFolderPermission.user_id == current_user.id,
            )
            .first()
        )
        if not perm:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sem permissão para este diretório raiz")

        have = perm.access_level
        if _ACCESS_ORDER.get(have, 0) < _ACCESS_ORDER[min_level]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Nível de acesso insuficiente")
        return root_id

    return _dep
