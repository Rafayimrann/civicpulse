"""
ORM models. This is the source of truth that Alembic autogenerate diffs
against - but the migration files in alembic/versions/ are what actually
runs against the database. Never call Base.metadata.create_all() in app
startup code.
"""
from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import CHAR, DateTime, Enum, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.db import Base


class GUID(TypeDecorator):
    """
    Platform-independent UUID type.

    Uses Postgres' native UUID type when running against Postgres (prod/dev),
    and falls back to CHAR(36) on SQLite (the pytest/CI engine), so the same
    ORM model works unmodified in both. This is the one deliberate departure
    from "no SQL outside repositories, no cleverness in models" - it exists
    purely to keep the test suite fast (SQLite, no container) without forking
    the schema.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class Category(str, enum.Enum):
    water = "water"
    electricity = "electricity"
    sanitation = "sanitation"
    roads = "roads"
    streetlights = "streetlights"
    other = "other"


class Priority(str, enum.Enum):
    high = "high"
    normal = "normal"
    low = "low"


class Status(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    rejected = "rejected"


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        Index("ix_complaints_status_priority", "status", "priority"),
        Index("ix_complaints_created_at", "created_at"),
    )

    # Client-side UUID generation (not server_default=gen_random_uuid()) so the
    # same model works against Postgres in prod and SQLite in the test suite.
    id: Mapped[uuid.UUID] = mapped_column(GUID(), primary_key=True, default=uuid.uuid4)

    text: Mapped[str] = mapped_column(String(2000), nullable=False)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    reporter_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)

    category: Mapped[Category] = mapped_column(
        Enum(Category, name="category_enum", native_enum=True), nullable=False
    )
    priority: Mapped[Priority] = mapped_column(
        Enum(Priority, name="priority_enum", native_enum=True), nullable=False
    )
    status: Mapped[Status] = mapped_column(
        Enum(Status, name="status_enum", native_enum=True), nullable=False, default=Status.open
    )

    ai_summary: Mapped[str | None] = mapped_column(String(140), nullable=True)
    triaged_by: Mapped[str] = mapped_column(String(50), nullable=False)
    triage_latency_ms: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )
