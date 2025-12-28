from __future__ import annotations

from sqlalchemy import (
    Column, Integer, String, DateTime, BigInteger, func,
    UniqueConstraint, ForeignKey, Index
)
from sqlalchemy.orm import relationship

from app.db.database import Base

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
    permissions = relationship("RootFolderPermission", back_populates="root", cascade="all, delete-orphan")

class File(Base):
    __tablename__ = "files"
    __table_args__ = (
        UniqueConstraint("root_id", "path", name="uq_file_root_path"),
        Index("ix_files_root_id", "root_id"),
        Index("ix_files_name", "name"),
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

# ---------------- Auth ----------------

class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("username", name="uq_users_username"),
        UniqueConstraint("email", name="uq_users_email"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(64), nullable=False)
    email = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    is_active = Column(Integer, nullable=False, default=1)  # 1/0 pra SQLite
    is_superuser = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    permissions = relationship("RootFolderPermission", back_populates="user", cascade="all, delete-orphan")

class RootFolderPermission(Base):
    __tablename__ = "root_folder_permissions"
    __table_args__ = (
        UniqueConstraint("root_id", "user_id", name="uq_root_user"),
        Index("ix_perm_root", "root_id"),
        Index("ix_perm_user", "user_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    root_id = Column(Integer, ForeignKey("root_folders.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # reader | editor | admin
    access_level = Column(String(16), nullable=False, default="reader")

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    root = relationship("RootFolder", back_populates="permissions")
    user = relationship("User", back_populates="permissions")
