from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.poster import Poster
from app.models.campaign import Campaign
from app.schemas.poster import (
    PosterGenerateRequest,
    PosterGenerateResponse,
    PosterRegenerateResponse,
    PosterResponse,
    PosterStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────────────────

_DAY_NAMES = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday"}


def _poster_to_response(poster: Poster) -> PosterResponse:
    return PosterResponse(
        poster_id=poster.id,
        campaign_id=poster.campaign_id,
        day=poster.day,
        day_name=poster.day_name,
        theme=poster.theme,
        image_url=poster.image_url or "",
        image_prompt=poster.image_prompt,
        text_overlay=poster.text_overlay,
        status=PosterStatus(poster.status),
        version=poster.version,
        created_at=poster.created_at,
    )


# ── Background tasks ───────────────────────────────────────────────────────────

def _generate_poster_image(poster_id: uuid.UUID) -> None:
    """
    Background task: run the full image pipeline for an existing poster stub.
    Updates poster.image_url and poster.status in DB on completion.
    """
    from app.database import SessionLocal
    from app.services.image_service import generate_and_upload_poster

    db: Session = SessionLocal()
    try:
        poster = db.get(Poster, poster_id)
        if not poster:
            logger.error("BG task: poster %s not found", poster_id)
            return

        logger.info(
            "BG task: generating image for poster %s (day %d)", poster_id, poster.day
        )

        image_url = generate_and_upload_poster(
            image_prompt=poster.image_prompt,
            text_overlay=poster.text_overlay,
            poster_id=str(poster_id),
        )

        poster.image_url = image_url
        poster.status = PosterStatus.pending  # ready for human review
        db.commit()
        logger.info("BG task: poster %s image ready — url=%s", poster_id, image_url)

    except Exception as exc:
        db.rollback()
        logger.error(
            "\n" + "="*60 + "\n"
            "POSTER GENERATION FAILED\n"
            "  poster_id : %s\n"
            "  reason    : %s: %s\n"
            + "="*60,
            poster_id,
            type(exc).__name__,
            exc,
        )
        logger.exception("Full traceback:")  # prints the stack trace below
        try:
            poster = db.get(Poster, poster_id)
            if poster:
                poster.status = PosterStatus.failed
                poster.image_url = None  # clear any stale URL from a previous run
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def _regenerate_poster_image(poster_id: uuid.UUID) -> None:
    """
    Background task: regenerate the image for an existing poster using the
    same prompts. Increments version on success.
    """
    from app.database import SessionLocal
    from app.services.image_service import generate_and_upload_poster

    db: Session = SessionLocal()
    try:
        poster = db.get(Poster, poster_id)
        if not poster:
            logger.error("BG regen task: poster %s not found", poster_id)
            return

        logger.info(
            "BG regen task: regenerating poster %s (day %d, version %d)",
            poster_id, poster.day, poster.version,
        )

        image_url = generate_and_upload_poster(
            image_prompt=poster.image_prompt,
            text_overlay=poster.text_overlay,
            poster_id=f"{poster_id}_v{poster.version + 1}",
        )

        poster.image_url = image_url
        poster.version += 1
        poster.status = PosterStatus.pending
        db.commit()
        logger.info(
            "BG regen task: poster %s regenerated — version=%d url=%s",
            poster_id, poster.version, image_url,
        )

    except Exception as exc:
        db.rollback()
        logger.error(
            "\n" + "="*60 + "\n"
            "POSTER REGENERATION FAILED\n"
            "  poster_id : %s\n"
            "  reason    : %s: %s\n"
            + "="*60,
            poster_id,
            type(exc).__name__,
            exc,
        )
        logger.exception("Full traceback:")
        try:
            poster = db.get(Poster, poster_id)
            if poster:
                poster.status = PosterStatus.failed
                poster.image_url = None  # clear any stale URL from a previous run
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


# ── Routes ─────────────────────────────────────────────────────────────────────

@router.post(
    "/generate/{campaign_id}",
    response_model=PosterGenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate poster image for a specific day",
    description=(
        "Triggers async background image generation for one day of an existing campaign. "
        "The campaign must already be in `ready` status (Gemini plan complete). "
        "Poll `GET /campaigns/{id}` until `days[n].poster_id` is populated and "
        "`GET /posters/{id}` until `status == 'pending'`."
    ),
)
def generate_poster(
    campaign_id: uuid.UUID,
    body: PosterGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PosterGenerateResponse:
    # ── Validate campaign ──────────────────────────────────────────────────────
    campaign = db.get(Campaign, campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found.",
        )
    if campaign.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Campaign is not ready yet (status='{campaign.status}'). "
                "Wait until Gemini finishes planning."
            ),
        )

    # ── Find the poster stub for the requested day ─────────────────────────────
    poster: Poster | None = (
        db.query(Poster)
        .filter(Poster.campaign_id == campaign_id, Poster.day == body.day)
        .first()
    )
    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No poster stub found for campaign {campaign_id} day {body.day}.",
        )

    # ── Guard: don't re-trigger if already generating or done ─────────────────
    if poster.status == PosterStatus.generating:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Poster for day {body.day} is already generating.",
        )

    # Mark as generating immediately so the frontend can start polling
    poster.status = PosterStatus.generating
    db.commit()

    background_tasks.add_task(_generate_poster_image, poster.id)
    logger.info(
        "Poster generation started: campaign=%s day=%d poster=%s",
        campaign_id, body.day, poster.id,
    )

    return PosterGenerateResponse(
        campaign_id=campaign_id,
        day=body.day,
        day_name=poster.day_name,
        status=PosterStatus.generating,
        message=f"Poster generation for Day {body.day} ({poster.day_name}) started in background.",
    )


@router.get(
    "/{poster_id}",
    response_model=PosterResponse,
    summary="Get poster detail",
    description="Returns full poster data including the Cloudinary image URL and generation status.",
)
def get_poster(
    poster_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> PosterResponse:
    poster = db.get(Poster, poster_id)
    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poster {poster_id} not found.",
        )
    return _poster_to_response(poster)


@router.post(
    "/{poster_id}/regenerate",
    response_model=PosterRegenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Regenerate poster image",
    description=(
        "Re-runs the image generation pipeline for an existing poster using the **same prompts**. "
        "Useful when the initial generation failed or produced a poor result. "
        "For content-driven changes use `POST /revisions/{poster_id}` instead."
    ),
)
def regenerate_poster(
    poster_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> PosterRegenerateResponse:
    poster = db.get(Poster, poster_id)
    if not poster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Poster {poster_id} not found.",
        )

    if poster.status == PosterStatus.generating:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This poster is already being generated. Please wait.",
        )

    # Mark as generating before kicking off the background task
    poster.status = PosterStatus.generating
    db.commit()

    background_tasks.add_task(_regenerate_poster_image, poster.id)
    logger.info("Poster regeneration queued: poster=%s", poster_id)

    return PosterRegenerateResponse(
        poster_id=poster_id,
        status=PosterStatus.generating,
        message="Poster regeneration started in background. Poll GET /posters/{id} for status.",
    )
