from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Enums ──────────────────────────────────────────────────────────────────────

class RevisionStatus(str, Enum):
    regenerating = "regenerating"  # Background task in progress
    complete     = "complete"      # New poster is ready
    failed       = "failed"        # Regeneration failed


# ── Nested ─────────────────────────────────────────────────────────────────────

class RevisionChange(BaseModel):
    """A single targeted change within the revision plan."""

    component: str = Field(..., description="e.g. image_prompt, text_overlay, mascot_pose")
    action:    str = Field(..., description="modify | keep | remove")
    change:    str = Field("", description="Description of what to change — empty when action is keep/remove")


class RevisionPlan(BaseModel):
    """The structured plan produced by Gemini from the human's feedback."""

    changes: list[RevisionChange]


# ── Requests ───────────────────────────────────────────────────────────────────

class RevisionCreate(BaseModel):
    """Request body for POST /revisions/{poster_id}."""

    feedback: str = Field(..., min_length=5, max_length=1000, description="Human feedback on the poster")


# ── Responses ──────────────────────────────────────────────────────────────────

class RevisionResponse(BaseModel):
    """202 response for POST /revisions/{poster_id} and GET /revisions/{id}."""

    revision_id:   UUID
    poster_id:     UUID
    campaign_id:   UUID
    feedback:      str
    revision_plan: RevisionPlan
    new_poster_id: Optional[UUID] = Field(None, description="Populated once regeneration completes")
    status:        RevisionStatus
    created_at:    datetime

    model_config = {"from_attributes": True}


class RevisionListItem(BaseModel):
    """Lightweight entry for GET /campaigns/{id}/revisions."""

    revision_id: UUID
    poster_id:   UUID
    day:         int
    feedback:    str
    status:      RevisionStatus
    created_at:  datetime

    model_config = {"from_attributes": True}
