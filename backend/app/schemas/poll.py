from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


# ── Responses ──────────────────────────────────────────────────────────────────

class PollResponse(BaseModel):
    """Full poll detail for POST /polls/generate/{poster_id} and GET /polls/{id}."""

    poll_id:     UUID
    poster_id:   UUID
    campaign_id: UUID
    day:         int  = Field(..., ge=1, le=5)
    day_name:    str
    question:    str
    options:     list[str] = Field(..., min_length=2, description="2–4 answer choices")
    created_at:  datetime

    model_config = {"from_attributes": True}
