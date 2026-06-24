from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.poster import Poster  # only used by the type checker
    from app.models.poll import Poll  # only used by the type checker


class Campaign(Base):
    __tablename__ = "campaigns"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Request fields ────────────────────────────────────────────────────────
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, default=uuid.uuid4, index=True
    )
    topic: Mapped[str] = mapped_column(String(200), nullable=False)
    objective: Mapped[str] = mapped_column(String(500), nullable=False)

    # ── Status ────────────────────────────────────────────────────────────────
    # "draft" → "ready" → "failed"
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    posters: Mapped[list[Poster]] = relationship(
        "Poster", back_populates="campaign", cascade="all, delete-orphan"
    )
    polls: Mapped[list[Poll]] = relationship(
        "Poll", back_populates="campaign", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Campaign id={self.id} topic={self.topic!r} status={self.status!r}>"
