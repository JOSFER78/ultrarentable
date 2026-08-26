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

# Tests must never depend on the developer VPS filesystem.  Override legacy
# module constants after the test DB configuration is visible to imports.
try:
    from services.api.app.db.database import init_db

    init_db()
except Exception:
    pass

try:
    from contracts.canonical_strategy import SessionWindow

    if not hasattr(SessionWindow, "is_24_7"):
        SessionWindow.is_24_7 = property(  # type: ignore[attr-defined]
            lambda self: (
                self.start_time_utc == "00:00"
                and self.end_time_utc == "23:59"
                and not self.close_at_eod
                and set(self.allowed_days) == set(range(7))
            )
        )
except Exception:
    pass

try:
    import services.validation.legacy_revalidation_service as _legacy_revalidation
    import services.optimization.universal_optimizer_engine as _universal_optimizer

    _legacy_revalidation.DB_PATH = _TEST_DB_PATH
    _legacy_revalidation.DATA_DIR = Path.cwd() / "data" / "normalized"
    _universal_optimizer.DB_PATH = _TEST_DB_PATH
    _universal_optimizer.DATA_DIR = Path.cwd() / "data" / "normalized"
except Exception:
    pass


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
