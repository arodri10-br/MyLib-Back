
# -*- coding: utf-8 -*-
"""
database.py
- Modelos ORM (RootFolder, File)
- Engine, Session e init_db (sem lógica de aplicação)
- Criação das tabelas FTS5 (docs) e tabela auxiliar 'map' via SQL bruto.
"""

import os
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, BigInteger, func,
    UniqueConstraint, ForeignKey, Index, text
)
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship

# ===================== Configuração do SQLite (ABSOLUTE PATH) =====================
# Garante que sempre será usado o MESMO doc_index.db (na pasta do projeto),
# evitando criar/levar a outro DB ao rodar o uvicorn a partir de outro diretório.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "doc_index.db")
DB_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False},  # necessário para SQLite com threads
    future=True,
)

# Opcional: PRAGMAs de performance seguros (apenas após conectar)
def _apply_sqlite_pragmas(conn):
    try:
        conn.exec_driver_sql("PRAGMA journal_mode=WAL;")       # melhor concorrência de leitura
        conn.exec_driver_sql("PRAGMA synchronous=NORMAL;")     # bom equilíbrio desempenho/segurança
        conn.exec_driver_sql("PRAGMA temp_store=MEMORY;")
        conn.exec_driver_sql("PRAGMA mmap_size=134217728;")    # 128MB
    except Exception:
        # Ignora em ambientes onde o driver não suportar
        pass

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()

# ===================== Modelos =====================
class RootFolder(Base):
    __tablename__ = "root_folders"
    __table_args__ = (
        UniqueConstraint("path", name="uq_root_path"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    path = Column(String(1024), nullable=False)  # UNC \\server\share ou local
    last_scan_at = Column(DateTime, nullable=True)
    files_count = Column(Integer, nullable=True)
    total_size_bytes = Column(BigInteger, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    files = relationship("File", back_populates="root", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        UniqueConstraint("path", name="uq_file_path"),
        Index("ix_files_root_ext", "root_id", "ext"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    root_id = Column(Integer, ForeignKey("root_folders.id", ondelete="CASCADE"), nullable=False)
    path = Column(String(2048), nullable=False)
    name = Column(String(512), nullable=False)
    ext = Column(String(32), nullable=True)
    size = Column(BigInteger, nullable=True)
    mtime = Column(BigInteger, nullable=True)  # epoch seconds
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    root = relationship("RootFolder", back_populates="files")

# ===================== Init DB + FTS5 =====================
def init_db() -> None:
    """Cria tabelas ORM e garante FTS5 (docs) + map."""
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        # Aplica PRAGMAs (opcional)
        _apply_sqlite_pragmas(conn)

        # docs: conteúdo textual + colunas auxiliares para ranking leve
        conn.execute(text("""
            CREATE VIRTUAL TABLE IF NOT EXISTS docs USING fts5(
                content,
                filename,
                ext,
                tokenize='unicode61'
            );
        """))

        # map: liga file_id ao rowid do FTS5 e guarda fingerprint para incremental
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS map (
                file_id INTEGER UNIQUE,
                rowid_docs INTEGER,
                fingerprint TEXT,
                FOREIGN KEY(file_id) REFERENCES files(id) ON DELETE CASCADE
            );
        """))
        conn.commit()

# ===================== Session dependency =====================
def get_session() -> Session:
    """Dependency para FastAPI — retorna uma sessão do SQLAlchemy."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
