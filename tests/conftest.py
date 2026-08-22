"""Pytest isolation for root test suite: never read or mutate the operational SQLite database."""
from __future__ import annotations

import os
import sqlite3
import tempfile
from pathlib import Path


_TEST_DB_PATH = (
    Path(tempfile.gettempdir())
    / f"ultrarentable-root-pytest-{os.getpid()}.sqlite3"
)
_OPERATIONAL_DB_PATH = Path(
    os.getenv(
        "ULTRARENTABLE_OPERATIONAL_DB",
        "~/.local/state/ultrarentable/ultrarentable.sqlite3",
    )
).expanduser()

if _OPERATIONAL_DB_PATH.is_file():
    source = sqlite3.connect(f"file:{_OPERATIONAL_DB_PATH}?mode=ro", uri=True)
    destination = sqlite3.connect(_TEST_DB_PATH)
    try:
        source.backup(destination)
    finally:
        destination.close()
        source.close()

os.environ["STATE_DB_PATH"] = str(_TEST_DB_PATH)


def pytest_sessionfinish(session, exitstatus) -> None:
    """Close SQLAlchemy and remove the complete temporary SQLite set."""
    try:
        from services.api.app.db.database import engine

        engine.dispose()
    except Exception:
        pass

    for suffix in ("", "-wal", "-shm", "-journal"):
        path = Path(f"{_TEST_DB_PATH}{suffix}")
        try:
            path.unlink()
        except FileNotFoundError:
            pass
