from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Use DATABASE_URL env var (PostgreSQL on Render, SQLite fallback for local dev)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Render provides postgres:// but SQLAlchemy requires postgresql://
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
else:
    # Local dev fallback: SQLite
    BASE_DIR = Path(__file__).parent.parent
    DATA_DIR = Path("/app/data") if Path("/app/data").exists() else BASE_DIR
    DATABASE_URL = f"sqlite:///{DATA_DIR}/app.db"
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def _run_migrations():
    """Add columns that create_all() won't add to existing tables."""
    migrations = [
        "ALTER TABLE telemetry_events ADD COLUMN providers_detected TEXT",
    ]
    with engine.connect() as conn:
        for sql in migrations:
            try:
                conn.execute(text(sql))
                conn.commit()
            except Exception:
                conn.rollback()  # Column already exists


def init_db():
    """Initialize database tables"""
    # Import all models so create_all() knows about them
    try:
        import app.models.telemetry  # noqa
    except Exception:
        pass
    try:
        import models.organization  # noqa
    except Exception:
        pass

    Base.metadata.create_all(bind=engine)
    _run_migrations()
