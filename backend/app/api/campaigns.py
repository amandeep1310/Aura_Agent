from __future__ import annotations

import logging
import uuid
from typing import List

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.campaign import Campaign
from app.models.poster import Poster
from app.models.poll import Poll
from app.schemas.campaign import (
    CampaignCreate,
    CampaignListItem,
    CampaignResponse,
    CampaignStatus,
    DayPlan,
)
from app.services.gemini_service import generate_campaign_plan

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Background task ────────────────────────────────────────────────────────────

def _run_campaign_plan(campaign_id: uuid.UUID, topic: str, objective: str) -> None:

    print("BACKGROUND TASK STARTED")

    from app.database import SessionLocal

    db: Session = SessionLocal()

    try:

        campaign = db.get(Campaign, campaign_id)

        if not campaign:
            print("CAMPAIGN NOT FOUND")
            return

        print("CALLING GEMINI...")

        day_plans = generate_campaign_plan(topic, objective)

        print("GEMINI RETURNED:", len(day_plans), "DAYS")

        for plan in day_plans:

            poster = Poster(
                campaign_id=campaign_id,
                day=plan.day,
                day_name=plan.day_name,
                theme=plan.theme,
                image_prompt=plan.image_prompt,
                text_overlay=plan.text_overlay,
                status="pending_image",
            )

            db.add(poster)

        campaign.status = CampaignStatus.ready

        db.commit()

        print("CAMPAIGN READY")

    except Exception as exc:

        print("ERROR OCCURRED:", exc)

        db.rollback()

    finally:

        db.close()


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/create",
    response_model=CampaignResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Create a new campaign",
    description=(
        "Creates a campaign record immediately, then calls Gemini in the background "
        "to produce a 5-day content plan. Poll GET /campaigns/{id} until "
        "`status == 'ready'`."
    ),
)
def create_campaign(
    body: CampaignCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CampaignResponse:
    session_id = body.session_id or uuid.uuid4()

    campaign = Campaign(
        session_id=session_id,
        topic=body.topic,
        objective=body.objective,
        status=CampaignStatus.draft,
    )
    db.add(campaign)
    db.commit()
    db.refresh(campaign)

    background_tasks.add_task(
        _run_campaign_plan,
        campaign.id,
        body.topic,
        body.objective,
    )

    logger.info("Campaign %s created — background plan started", campaign.id)

    return _to_campaign_response(campaign, posters=[], polls=[])


@router.get(
    "",
    response_model=List[CampaignListItem],
    summary="List all campaigns",
    description="Returns a lightweight list of all campaigns, newest first.",
)
def list_campaigns(db: Session = Depends(get_db)) -> List[CampaignListItem]:
    campaigns = (
        db.query(Campaign)
        .order_by(Campaign.created_at.desc())
        .all()
    )
    return [
        CampaignListItem(
            campaign_id=c.id,
            topic=c.topic,
            objective=c.objective,
            status=c.status,
            created_at=c.created_at,
        )
        for c in campaigns
    ]


@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get campaign detail",
    description=(
        "Full campaign detail including per-day poster and poll IDs. "
        "Poll this endpoint until `status == 'ready'`."
    ),
)
def get_campaign(
    campaign_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> CampaignResponse:
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found.",
        )

    posters = (
        db.query(Poster)
        .filter(Poster.campaign_id == campaign_id)
        .order_by(Poster.day)
        .all()
    )
    polls = (
        db.query(Poll)
        .filter(Poll.campaign_id == campaign_id)
        .all()
    )

    return _to_campaign_response(campaign, posters, polls)


# ── Response builder ───────────────────────────────────────────────────────────

def _to_campaign_response(
    campaign: Campaign,
    posters: list[Poster],
    polls: list[Poll],
) -> CampaignResponse:
    """Map ORM objects to the CampaignResponse schema."""

    # Build a quick lookup: day → poll_id
    poll_by_day: dict[int, uuid.UUID] = {p.day: p.id for p in polls}

    days = [
        DayPlan(
            day=poster.day,
            day_name=poster.day_name,
            theme=poster.theme,
            poster_id=poster.id,
            poll_id=poll_by_day.get(poster.day),
        )
        for poster in posters
    ]

    return CampaignResponse(
        campaign_id=campaign.id,
        session_id=campaign.session_id,
        topic=campaign.topic,
        objective=campaign.objective,
        status=campaign.status,
        days=days,
        created_at=campaign.created_at,
    )
