from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

import google.generativeai as genai

from app.config import settings
from app.services.prompts import (
    CAMPAIGN_SYSTEM_PROMPT,
    POLL_SYSTEM_PROMPT,
    REVISION_SYSTEM_PROMPT,
    build_campaign_prompt,
    build_poll_prompt,
    build_revision_prompt,
)

logger = logging.getLogger(__name__)
genai.configure(api_key=settings.GEMINI_API_KEY)

_MODEL_NAME = settings.GEMINI_MODEL_NAME

# ── Return-type dataclasses ───────────────────────────────────────────────────
# Plain dataclasses keep the service decoupled from SQLAlchemy models and
# Pydantic schemas; callers map these into whatever they need.


@dataclass
class DayPlanData:
    """One day's Gemini-generated content for a 5-day campaign."""

    day: int  # 1 – 5
    day_name: str  # "Monday" … "Friday"
    theme: str  # Daily theme / focus
    image_prompt: str  # Detailed prompt for the image-generation model
    text_overlay: str  # Short headline to print on the poster


@dataclass
class PollData:
    """Engagement poll for a single poster day."""

    question: str
    options: list[str] = field(default_factory=list)


@dataclass
class RevisionChangeData:
    component: str  # e.g. "image_prompt", "text_overlay"
    action: str  # "modify" | "keep" | "remove"
    change: str = ""  # Description of the change; empty when action != "modify"


@dataclass
class RevisionPlanData:
    """Structured revision plan produced from human feedback."""

    changes: list[RevisionChangeData] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────


def _build_model(system_instruction: str) -> genai.GenerativeModel:
    """Construct a GenerativeModel instance with a given system prompt."""
    return genai.GenerativeModel(
        model_name=_MODEL_NAME,
        system_instruction=system_instruction,
    )


def _parse_json_response(raw: str, context: str) -> Any:
    """
    Strip markdown fences if present and parse JSON.
    Raises ValueError with a helpful message on failure.
    """
    # Gemini sometimes wraps the response in ```json … ```
    text = raw.strip()
    if text.startswith("```"):
        # Remove opening fence (```json or ```)
        text = text.split("\n", 1)[-1]
        # Remove closing fence
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

    try:
        return json.loads(text.strip())
    except json.JSONDecodeError as exc:
        logger.error("JSON parse failure in %s. Raw response:\n%s", context, raw)
        raise ValueError(
            f"Gemini returned invalid JSON for {context}. " f"Parse error: {exc}"
        ) from exc


# ── Day names lookup ──────────────────────────────────────────────────────────

_DAY_NAMES = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday"}


# ── Public functions ──────────────────────────────────────────────────────────


def generate_campaign_plan(topic: str, objective: str) -> list[DayPlanData]:
    user_prompt = build_campaign_prompt(topic, objective)

    logger.info("Generating campaign plan | topic=%r | objective=%r", topic, objective)

    model = _build_model(CAMPAIGN_SYSTEM_PROMPT)
    response = model.generate_content(user_prompt)
    raw = response.text

    data = _parse_json_response(raw, context="generate_campaign_plan")

    if not isinstance(data, list) or len(data) != 5:
        raise ValueError(
            f"Expected a JSON array of 5 days; got {type(data).__name__} "
            f"with {len(data) if isinstance(data, list) else '?'} items."
        )

    days: list[DayPlanData] = []
    for item in data:
        day_num = int(item["day"])
        days.append(
            DayPlanData(
                day=day_num,
                day_name=item.get(
                    "day_name", _DAY_NAMES.get(day_num, f"Day {day_num}")
                ),
                theme=item["theme"],
                image_prompt=item["image_prompt"],
                text_overlay=item["text_overlay"],
            )
        )

    # Ensure days are sorted 1-5 regardless of model output order
    days.sort(key=lambda d: d.day)
    logger.info("Campaign plan generated successfully — %d days", len(days))
    return days


# ─────────────────────────────────────────────────────────────────────────────


def generate_poll(
    day: int,
    day_name: str,
    theme: str,
    text_overlay: str,
) -> PollData:
    user_prompt = build_poll_prompt(day, day_name, theme, text_overlay)

    logger.info("Generating poll | day=%d | theme=%r", day, theme)

    model = _build_model(POLL_SYSTEM_PROMPT)
    response = model.generate_content(user_prompt)
    raw = response.text

    data = _parse_json_response(raw, context="generate_poll")

    options = data.get("options", [])
    if len(options) < 2:
        raise ValueError(
            f"Poll must have at least 2 options; Gemini returned {len(options)}."
        )

    poll = PollData(
        question=data["question"],
        options=options,
    )
    logger.info(
        "Poll generated | question=%r | options=%d", poll.question, len(poll.options)
    )
    return poll


# ─────────────────────────────────────────────────────────────────────────────


def generate_revision_plan(
    feedback: str,
    poster_context: dict[str, str],
) -> RevisionPlanData:
    theme = poster_context.get("theme", "")
    image_prompt = poster_context.get("image_prompt", "")
    text_overlay = poster_context.get("text_overlay", "")

    user_prompt = build_revision_prompt(feedback, theme, image_prompt, text_overlay)

    logger.info("Generating revision plan | feedback=%r", feedback[:80])

    model = _build_model(REVISION_SYSTEM_PROMPT)
    response = model.generate_content(user_prompt)
    raw = response.text

    data = _parse_json_response(raw, context="generate_revision_plan")

    changes: list[RevisionChangeData] = []
    for item in data.get("changes", []):
        changes.append(
            RevisionChangeData(
                component=item["component"],
                action=item["action"],
                change=item.get("change", ""),
            )
        )

    plan = RevisionPlanData(changes=changes)
    logger.info(
        "Revision plan generated | components=%s",
        [c.component for c in changes],
    )
    return plan
