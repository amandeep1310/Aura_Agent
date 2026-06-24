from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.poster import PosterStatus


# ── Requests ───────────────────────────────────────────────────────────────────

class RequestChangeBody(BaseModel):
    """Request body for POST /approval/{poster_id}/request-change."""

    feedback: str = Field(..., min_length=5, max_length=1000, description="Specific change the reviewer wants")


# ── Responses ──────────────────────────────────────────────────────────────────

class ApprovalResponse(BaseModel):
    """Response for approve and reject actions (200 OK)."""

    poster_id: UUID
    status:    PosterStatus
    message:   str


class RequestChangeResponse(BaseModel):
    """202 response for request-change — revision is kicked off in background."""

    poster_id:   UUID
    status:      PosterStatus = PosterStatus.revision_requested
    revision_id: Optional[UUID] = Field(None, description="ID of the created revision record")
    message:     str
