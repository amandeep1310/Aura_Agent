from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.poster import Poster  # only used by the type checker


class Revision(Base):
    __tablename__ = "revisions"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    poster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Feedback & plan ───────────────────────────────────────────────────────
    feedback: Mapped[str] = mapped_column(Text, nullable=False)
    # Stored as {"changes": [...]} — mirrors RevisionPlan schema
    revision_plan: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # ── Output ────────────────────────────────────────────────────────────────
    # Null until the regenerated poster is persisted
    new_poster_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posters.id", ondelete="SET NULL"),
        nullable=True,
    )

    # ── Status ────────────────────────────────────────────────────────────────
    # "regenerating" → "complete" | "failed"
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="regenerating"
    )

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    original_poster: Mapped["Poster"] = relationship(
        "Poster", foreign_keys=[poster_id], back_populates="revisions"
    )

    def __repr__(self) -> str:
        return f"<Revision id={self.id} poster={self.poster_id} status={self.status!r}>"
