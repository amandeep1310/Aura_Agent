from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.campaign import Campaign   # only used by the type checker
    from app.models.revision import Revision   # only used by the type checker


class Poster(Base):
    __tablename__ = "posters"

    # ── Primary key ───────────────────────────────────────────────────────────
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )

    # ── Foreign key ───────────────────────────────────────────────────────────
    campaign_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ── Day info ──────────────────────────────────────────────────────────────
    day: Mapped[int] = mapped_column(Integer, nullable=False)  # 1-5
    day_name: Mapped[str] = mapped_column(String(10), nullable=False)  # "Monday" …
    theme: Mapped[str] = mapped_column(String(300), nullable=False)

    # ── Generated content ─────────────────────────────────────────────────────
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    image_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    text_overlay: Mapped[str] = mapped_column(String(200), nullable=False)

    # ── Status & versioning ───────────────────────────────────────────────────
    # "generating" → "pending" → "approved" | "rejected" | "revision_requested" | "failed"
    status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="generating"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # ── Timestamps ────────────────────────────────────────────────────────────
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # ── Relationships ─────────────────────────────────────────────────────────
    campaign: Mapped["Campaign"] = relationship(
        "Campaign", back_populates="posters"
    )  # noqa: F821
    revisions: Mapped[list["Revision"]] = relationship(
        "Revision",
        foreign_keys="Revision.poster_id",
        back_populates="original_poster",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Poster id={self.id} campaign={self.campaign_id} day={self.day} status={self.status!r}>"
