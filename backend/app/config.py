from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path


class Settings(BaseSettings):
    """
    Application settings loaded from the .env file.
    All fields are validated by Pydantic on startup — the app will
    refuse to start if a required variable is missing or malformed.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent / ".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",          # Silently ignore unknown env vars
    )

    # ── LLM ───────────────────────────────────────────────────────────────
    GEMINI_API_KEY:    str = ""
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash"       # Override in .env to switch models

    # ── Image Generation ───────────────────────────────────────────────────
    IMAGE_MODEL_API_KEY: str = ""
    IMAGE_MODEL_NAME:    str = "imagen-3.0-generate-002"  # Override in .env

    # ── Cloudinary ────────────────────────────────────────────────────────────
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = ""


# Single instance — import `settings` everywhere instead of re-instantiating
settings = Settings()
