"""
image_service.py
────────────────
Handles AI image generation, Pillow poster compositing, and Cloudinary upload.

Pipeline per poster:
  1. generate_image()           → raw PIL Image via Gemini image model
  2. composite_poster()         → adds text overlay + logo using Pillow
  3. upload_to_cloudinary()     → returns a public CDN URL

Errors are NOT swallowed here — they propagate to the background task in
posters.py which sets poster.status = "failed" and logs the traceback.
"""
from __future__ import annotations

import io
import logging
import textwrap
from pathlib import Path

from app.config import settings

logger = logging.getLogger(__name__)

# ── Asset paths ────────────────────────────────────────────────────────────────
_ASSETS_DIR = Path(__file__).resolve().parents[3] / "assets"
_LOGO_PATH  = _ASSETS_DIR / "logo.png"
_FONT_PATH  = _ASSETS_DIR / "font.ttf"

# Poster canvas size
POSTER_W, POSTER_H = 1080, 1080


# ── Lazy imports (heavy libs only when needed) ────────────────────────────────

def _get_pil():
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
    return Image, ImageDraw, ImageFont


def _get_cloudinary_uploader():
    import cloudinary                  # type: ignore
    import cloudinary.uploader         # type: ignore
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True,
    )
    return cloudinary.uploader


# ── 1. Image generation ───────────────────────────────────────────────────────

def generate_image(image_prompt: str) -> "PIL.Image.Image":  # type: ignore[name-defined]
    """
    Generate a 1080×1080 poster background using the configured Gemini image
    model (IMAGE_MODEL_NAME from .env, e.g. gemini-2.5-flash-image).

    Uses the new google-genai SDK (from google import genai).
    Raises on failure — callers must handle and set poster.status = "failed".
    """
    from google import genai                  # type: ignore  (google-genai package)
    from google.genai import types            # type: ignore

    Image, _, _ = _get_pil()

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    logger.info(
        "Calling Gemini image model '%s' for prompt: %s…",
        settings.IMAGE_MODEL_NAME,
        image_prompt[:80],
    )

    response = client.models.generate_content(
        model=settings.IMAGE_MODEL_NAME,
        contents=image_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    # Extract the inline image bytes from the first candidate's parts
    img_bytes: bytes | None = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            img_bytes = part.inline_data.data
            break

    if img_bytes is None:
        raise RuntimeError(
            f"Gemini model '{settings.IMAGE_MODEL_NAME}' returned no image data. "
            f"Check that the model supports image output and the prompt is valid. "
            f"Response text: {getattr(response.candidates[0].content.parts[0], 'text', 'N/A')}"
        )

    img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    img = img.resize((POSTER_W, POSTER_H))
    logger.info("Image generated successfully — size %s", img.size)
    return img


# ── 2. Poster compositing ─────────────────────────────────────────────────────

def composite_poster(
    base_image: "PIL.Image.Image",  # type: ignore[name-defined]
    text_overlay: str,
    *,
    add_logo: bool = True,
) -> "PIL.Image.Image":  # type: ignore[name-defined]
    """
    Overlay the text headline (and optionally the Tata Steel logo) onto the
    base image using Pillow. Raises on unrecoverable errors.
    """
    Image, ImageDraw, ImageFont = _get_pil()

    img = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(img)

    # ── Semi-transparent bottom banner ────────────────────────────────────────
    banner_h = int(POSTER_H * 0.22)
    banner = Image.new("RGBA", (POSTER_W, banner_h), (0, 0, 0, 170))
    img.paste(banner, (0, POSTER_H - banner_h), banner)

    # ── Font loading ──────────────────────────────────────────────────────────
    font_size = 56
    font = None

    if _FONT_PATH.exists():
        try:
            font = ImageFont.truetype(str(_FONT_PATH), font_size)
            logger.debug("Using custom font: %s", _FONT_PATH)
        except Exception as exc:
            logger.warning("Could not load custom font (%s) — using default", exc)

    if font is None:
        # Pillow's built-in font is tiny; use size param only available on newer Pillow
        try:
            font = ImageFont.load_default(size=font_size)  # Pillow >= 10.1
        except TypeError:
            font = ImageFont.load_default()  # older Pillow — will render small
        logger.warning(
            "assets/font.ttf not found at %s — text may render small. "
            "Add a TTF font file to fix this.",
            _FONT_PATH,
        )

    # ── Text overlay ──────────────────────────────────────────────────────────
    wrapped = textwrap.fill(text_overlay, width=28)
    lines = wrapped.splitlines()
    line_h = font_size + 10
    total_text_h = line_h * len(lines)
    y_start = POSTER_H - banner_h + (banner_h - total_text_h) // 2

    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        x = (POSTER_W - text_w) // 2
        y = y_start + i * line_h
        # Drop shadow
        draw.text((x + 2, y + 2), line, font=font, fill=(0, 0, 0, 200))
        # Main white text
        draw.text((x, y), line, font=font, fill=(255, 255, 255, 255))

    # ── Logo overlay ──────────────────────────────────────────────────────────
    if add_logo:
        if _LOGO_PATH.exists():
            try:
                logo_img = Image.open(_LOGO_PATH).convert("RGBA")
                max_logo_w = 200
                ratio = max_logo_w / logo_img.width
                logo_img = logo_img.resize(
                    (max_logo_w, int(logo_img.height * ratio)), Image.LANCZOS
                )
                margin = 20
                img.paste(
                    logo_img,
                    (POSTER_W - logo_img.width - margin, margin),
                    logo_img,
                )
                logger.debug("Logo overlaid from %s", _LOGO_PATH)
            except Exception as exc:
                # Logo is non-critical — log and continue
                logger.warning("Logo overlay failed (%s) — poster will render without logo", exc)
        else:
            logger.warning(
                "assets/logo.png not found at %s — poster will render without logo. "
                "Add your logo PNG to fix this.",
                _LOGO_PATH,
            )

    return img.convert("RGB")


# ── 3. Cloudinary upload ──────────────────────────────────────────────────────

def upload_to_cloudinary(img: "PIL.Image.Image", public_id: str) -> str:  # type: ignore[name-defined]
    """
    Encode the PIL Image as JPEG in-memory and upload to Cloudinary.
    Returns the secure CDN URL. Raises on failure.
    """
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    buf.seek(0)

    uploader = _get_cloudinary_uploader()
    result = uploader.upload(
        buf,
        public_id=f"aura/posters/{public_id}",
        overwrite=True,
        resource_type="image",
    )
    url: str = result["secure_url"]
    logger.info("Poster uploaded to Cloudinary — url=%s", url)
    return url


# ── Convenience: full pipeline ────────────────────────────────────────────────

def generate_and_upload_poster(
    image_prompt: str,
    text_overlay: str,
    poster_id: str,
) -> str:
    """
    Run the full pipeline:
      generate_image → composite_poster → upload_to_cloudinary

    Returns the Cloudinary secure URL.
    Any exception propagates — the background task in posters.py will catch it
    and set poster.status = "failed" with image_url = None.
    """
    logger.info("[%s] Starting poster pipeline", poster_id)

    try:
        raw_image = generate_image(image_prompt)
    except Exception as exc:
        logger.error(
            "[%s] STEP 1 FAILED — image generation\n  model   : %s\n  reason  : %s: %s",
            poster_id, settings.IMAGE_MODEL_NAME, type(exc).__name__, exc,
        )
        raise

    try:
        composited = composite_poster(raw_image, text_overlay)
    except Exception as exc:
        logger.error(
            "[%s] STEP 2 FAILED — Pillow compositing\n  reason  : %s: %s",
            poster_id, type(exc).__name__, exc,
        )
        raise

    try:
        cloudinary_url = upload_to_cloudinary(composited, public_id=poster_id)
    except Exception as exc:
        logger.error(
            "[%s] STEP 3 FAILED — Cloudinary upload\n  reason  : %s: %s",
            poster_id, type(exc).__name__, exc,
        )
        raise

    logger.info("[%s] Poster pipeline complete — url=%s", poster_id, cloudinary_url)
    return cloudinary_url
