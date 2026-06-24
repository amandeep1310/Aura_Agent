from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign  # only used by the type checker


class Poll(Base):
    __tablename__ = "polls"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign keys ──────────────────────────────────────────────────────────
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    poster_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("posters.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    # ── Day info ──────────────────────────────────────────────────────────────
    day: Mapped[int] = mapped_column(Integer, nullable=False)
    day_name: Mapped[str] = mapped_column(String(10), nullable=False)

    # ── Poll content ──────────────────────────────────────────────────────────
    question: Mapped[str] = mapped_column(String(300), nullable=False)
    options: Mapped[list] = mapped_column(JSON, nullable=False)  # list[str]

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="polls"
    )  # noqa: F821

    def __repr__(self) -> str:
        return f"<Poll id={self.id} day={self.day} question={self.question[:40]!r}>"
