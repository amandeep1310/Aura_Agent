# ── System prompts ─────────────────────────────────────────────────────────────
# Fixed persona instructions sent as the system role on every call.

CAMPAIGN_SYSTEM_PROMPT: str = (
    "You are AURA, an expert workplace-awareness campaign planner for Tata Steel. "
    "You create structured, engaging Mon–Fri campaigns for blue-collar and white-collar "
    "employees. Each day must build on the previous day's theme to create a cohesive "
    "narrative arc across the week. "
    "Respond ONLY with valid JSON — no prose, no markdown fences."
)

POLL_SYSTEM_PROMPT: str = (
    "You are AURA, a workplace engagement specialist for Tata Steel. "
    "You write short, clear, and thought-provoking poll questions for "
    "employees — suitable for an internal communications platform. "
    "Respond ONLY with valid JSON — no prose, no markdown fences."
)

REVISION_SYSTEM_PROMPT: str = (
    "You are AURA, an AI creative director for Tata Steel's internal campaigns. "
    "You receive human feedback on a poster and produce a precise, minimal revision plan "
    "that targets only the components that need changing. "
    "Respond ONLY with valid JSON — no prose, no markdown fences."
)


# ── User prompt builders ───────────────────────────────────────────────────────
# Functions that accept runtime values and return the filled-in user prompt.


def build_campaign_prompt(topic: str, objective: str) -> str:
    """User prompt for generate_campaign_plan()."""
    return f"""
Design a 5-day awareness campaign for the following brief:

Topic:     {topic}
Objective: {objective}

Return a JSON array of exactly 5 objects. Each object must follow this schema:

{{
  "day":          <integer 1-5>,
  "day_name":     <"Monday"|"Tuesday"|"Wednesday"|"Thursday"|"Friday">,
  "theme":        <concise daily theme, 5-10 words>,
  "image_prompt": <vivid, detailed prompt for an AI image generator, 40-80 words,
                   must feature Arjun (Tata Steel's mascot — a friendly male
                   blue-collar worker in a hard hat and safety vest) prominently,
                   set inside or around a modern steel plant>,
  "text_overlay": <punchy headline for the poster, max 12 words>
}}

Rules:
- Each day's theme must feel like a natural progression (e.g. Awareness → Understanding → Skills → Action → Commitment).
- image_prompt must be photorealistic style unless the theme calls for something different.
- text_overlay must be motivational and directly related to the day's theme.
- Output raw JSON only — no explanation, no markdown.
"""


def build_poll_prompt(day: int, day_name: str, theme: str, text_overlay: str) -> str:
    """User prompt for generate_poll()."""
    return f"""
Create an employee engagement poll for Day {day} ({day_name}) of a weekly campaign.

Campaign context:
  Theme:        {theme}
  Poster text:  {text_overlay}

Return a single JSON object:

{{
  "question": <one clear question, max 20 words>,
  "options":  [<option 1>, <option 2>, <option 3>]   // 3 or 4 short answer choices
}}

Rules:
- The question must be directly tied to the theme and suitable for a workplace poll.
- Options must be distinct, concise (max 6 words each), and cover a realistic range of responses.
- Do NOT include "Other" or "None of the above" — every option must be substantive.
- Output raw JSON only.
"""


def build_revision_prompt(
    feedback: str,
    theme: str,
    image_prompt: str,
    text_overlay: str,
) -> str:
    """User prompt for generate_revision_plan()."""
    return f"""
A human reviewer has given the following feedback on a campaign poster:

Feedback:     {feedback}

Current poster details:
  Theme:          {theme}
  Image prompt:   {image_prompt}
  Text overlay:   {text_overlay}

Analyse the feedback and decide which components need to change.
Components you may reference: "image_prompt", "text_overlay".

Return a JSON object with this schema:

{{
  "changes": [
    {{
      "component": <"image_prompt" | "text_overlay">,
      "action":    <"modify" | "keep" | "remove">,
      "change":    <specific instruction for the new value — empty string if action is "keep">
    }}
  ]
}}

Rules:
- Include an entry for EVERY component (even those you keep unchanged).
- If the feedback is about visual style, colour, layout, or the mascot — target "image_prompt".
- If the feedback is about wording, message, or the headline — target "text_overlay".
- "change" must be a concrete instruction to the generation model, not a description of the problem.
- Minimise scope — only change what the human explicitly asked for.
- Output raw JSON only.
"""
