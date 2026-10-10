"""SQLModel database engine & session factory."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.config.config import settings


def _ensure_sqlite_dir(url: str) -> None:
    if not url.startswith("sqlite:///"):
        return
    db_path = url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


_ensure_sqlite_dir(settings.database_url)

engine = create_engine(
    settings.database_url,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)


def init_db() -> None:
    """Create all tables. Idempotent."""
    from app.db import models  # noqa: F401  -- ensure models are registered

    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    """FastAPI dependency: yields a SQLModel session."""
    with Session(engine) as session:
        yield session


@contextmanager
def session_scope() -> Session:
    """Plain context-manager session for background tasks."""
    with Session(engine) as session:
        yield session