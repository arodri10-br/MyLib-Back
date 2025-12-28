# -*- coding: utf-8 -*-
"""
app/db/init_db.py
- Cria tabelas ORM
- Garante FTS5 (docs) e tabela map (compatível com seu projeto atual)
- Seed do usuário admin (env)
"""

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import hash_password
from app.db.database import engine, Base, SessionLocal
from app.models.models import User

def init_db() -> None:
    Base.metadata.create_all(bind=engine)

    # FTS5 + map (mantém o que já existia)
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON;"))
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                content,
                filename,
                ext,
                tokenize='unicode61'
            );
        """))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS map (
                file_id INTEGER UNIQUE,
                doc_rowid INTEGER,
                fingerprint TEXT,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
            );
        """))
        conn.commit()

    _seed_admin()

def _seed_admin() -> None:
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.username == settings.ADMIN_USERNAME).first()
        if not user:
            user = User(
                username=settings.ADMIN_USERNAME,
                email=settings.ADMIN_EMAIL,
                password_hash=hash_password(settings.ADMIN_PASSWORD),
                is_active=1,
                is_superuser=1,
            )
            db.add(user)
            db.commit()
        else:
            # garante que é superuser (sem resetar senha automaticamente)
            if user.is_superuser != 1:
                user.is_superuser = 1
                db.commit()
    finally:
        db.close()
