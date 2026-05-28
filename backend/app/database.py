from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings


settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    ensure_schema_migrations()


def ensure_schema_migrations() -> None:
    if not settings.database_url.startswith("sqlite"):
        return

    inspector = inspect(engine)
    if "transcript_segments" not in inspector.get_table_names():
        return

    columns = {
        column["name"] for column in inspector.get_columns("transcript_segments")
    }

    with engine.begin() as connection:
        if "source" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE transcript_segments "
                    "ADD COLUMN source VARCHAR(50) NOT NULL DEFAULT 'mock'"
                )
            )
        if "is_edited" not in columns:
            connection.execute(
                text(
                    "ALTER TABLE transcript_segments "
                    "ADD COLUMN is_edited BOOLEAN NOT NULL DEFAULT 0"
                )
            )
        if "updated_at" not in columns:
            connection.execute(
                text("ALTER TABLE transcript_segments ADD COLUMN updated_at DATETIME")
            )
            connection.execute(
                text(
                    "UPDATE transcript_segments "
                    "SET updated_at = created_at "
                    "WHERE updated_at IS NULL"
                )
            )


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
