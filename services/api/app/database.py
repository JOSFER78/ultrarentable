from __future__ import annotations

import sqlite3
from pathlib import Path

from sqlalchemy import create_engine, event

from services.api.app.config import STATE_DB_PATH
from services.api.app.db.database import Base


def _engine_for(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )

    @event.listens_for(engine, "connect")
    def _set_pragmas(dbapi_connection, _connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    return engine


def initialize_database(path: Path = STATE_DB_PATH) -> None:
    engine = _engine_for(path)
    Base.metadata.create_all(bind=engine)
    engine.dispose()


def database_health(path: Path = STATE_DB_PATH) -> dict[str, object]:
    try:
        initialize_database(path)
        with sqlite3.connect(path) as connection:
            journal_mode = connection.execute("PRAGMA journal_mode;").fetchone()[0]
            foreign_keys = connection.execute("PRAGMA foreign_keys;").fetchone()[0]
            connection.execute("SELECT 1").fetchone()
        return {
            "status": "ONLINE",
            "path": str(path),
            "journal_mode": str(journal_mode).upper(),
            "foreign_keys": bool(foreign_keys),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "ERROR", "path": str(path), "error": str(exc)}
