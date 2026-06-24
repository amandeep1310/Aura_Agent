from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class PosterStatus(str, Enum):
    generating         = "generating"          # Background task in progress
    pending            = "pending"             # Ready for human review
    approved           = "approved"            # Human approved
    rejected           = "rejected"            # Human permanently rejected
    revision_requested = "revision_requested"  # Human requested a change
    failed             = "failed"              # Image generation/upload failed


# ── Requests ───────────────────────────────────────────────────────────────────

class PosterGenerateRequest(BaseModel):
    """Request body for POST /posters/generate/{campaign_id}."""

    day: int = Field(..., ge=1, le=5, description="Day to generate (1 = Monday … 5 = Friday)")


# ── Responses ──────────────────────────────────────────────────────────────────

class PosterResponse(BaseModel):
    """Full poster detail for GET /posters/{id}."""

    poster_id:     UUID
    campaign_id:   UUID
    day:           int
    day_name:      str
    theme:         str
    image_url:     str  = Field(..., description="Cloudinary URL of the composited poster")
    image_prompt:  str  = Field(..., description="The prompt used to generate the base image")
    text_overlay:  str  = Field(..., description="Headline text overlaid by Pillow")
    status:        PosterStatus
    version:       int  = Field(..., description="Increments on every regeneration / revision")
    created_at:    datetime

    model_config = {"from_attributes": True}


class PosterGenerateResponse(BaseModel):
    """202 response for POST /posters/generate/{campaign_id}."""

    campaign_id: UUID
    day:         int
    day_name:    str
    status:      PosterStatus = PosterStatus.generating
    message:     str


class PosterRegenerateResponse(BaseModel):
    """202 response for POST /posters/{id}/regenerate."""

    poster_id: UUID
    status:    PosterStatus = PosterStatus.generating
    message:   str
