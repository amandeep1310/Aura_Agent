from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    # pool_pre_ping keeps idle connections healthy across restarts
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Shared declarative base — every model inherits from this."""
    pass


# ── FastAPI dependency ─────────────────────────────────────────────────────────

def get_db():
    """
    Yield a SQLAlchemy session for the duration of a request,
    then close it automatically (used with Depends).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
