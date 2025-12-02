import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class IdTimestampedEntity:
    __abstract__ = True

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, index=True, default=uuid.uuid4
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now(timezone.utc), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
        nullable=False,
    )


# pylint: disable=unsubscriptable-object


class User(IdTimestampedEntity, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(254), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    files: Mapped[List["FileAsset"]] = relationship(
        "FileAsset", back_populates="owner", cascade="all, delete"
    )
    sessions: Mapped[List["UserSession"]] = relationship(
        "UserSession", back_populates="user", cascade="all, delete"
    )


class FileAsset(IdTimestampedEntity, Base):
    __tablename__ = "file_assets"
    __table_args__ = (Index("ix_file_assets_owner_id_created_at", "owner_id", "created_at"),)

    display_name: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(537), nullable=False, unique=True)
    thumbnail_name: Mapped[Optional[str]] = mapped_column(String(600), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    owner: Mapped["User"] = relationship("User", back_populates="files")


class UserSession(IdTimestampedEntity, Base):
    __tablename__ = "user_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True
    )
    jti: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="sessions")
