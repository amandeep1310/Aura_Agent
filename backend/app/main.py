from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import campaigns, posters, polls, revisions, approval
from app.database import Base, engine
import app.models.campaign   # noqa: F401 — register models with Base
import app.models.poster     # noqa: F401
import app.models.poll       # noqa: F401
import app.models.revision   # noqa: F401

# ── App ────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="Agent AURA API",
    description=(
        "AI-Powered Campaign Generator for Tata Steel AURA. "
        "Generates Mon–Fri awareness campaigns — posters, polls, and content — "
        "from a single weekly topic using Gemini 2.5 Flash."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Create DB tables on startup (dev only — use Alembic for production)
Base.metadata.create_all(bind=engine)

# ── CORS ───────────────────────────────────────────────────────────────────────
# Allow the Streamlit frontend (localhost:8501) to call the API during development.
# Restrict `allow_origins` to specific domains before deploying to production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────────────────
app.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(posters.router,   prefix="/posters",   tags=["Posters"])
app.include_router(polls.router,     prefix="/polls",     tags=["Polls"])
app.include_router(revisions.router, prefix="/revisions", tags=["Revisions"])
app.include_router(approval.router,  prefix="/approval",  tags=["Approval"])

# ── System ─────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"], summary="Health check")
def health_check():
    """Returns API status. Used by monitoring and the Streamlit status panel."""
    return {
        "status": "ok",
        "version": "1.0.0",
    }