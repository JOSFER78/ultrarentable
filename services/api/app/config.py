from __future__ import annotations

import os
from pathlib import Path


def repo_root() -> Path:
    try:
        current = Path(__file__).resolve()
    except OSError:
        current = Path(__file__).absolute()
    for parent in [current, *current.parents]:
        if (parent / "REAL_ONLY_START_HERE.md").exists() or (parent / "pyproject.toml").exists():
            return parent
    return Path.cwd()


def resolve_local_path(env_name: str, default: str) -> Path:
    value = os.getenv(env_name, default)
    path = Path(value).expanduser()
    if path.is_absolute():
        return path
    base = repo_root() / path
    try:
        return base.resolve()
    except OSError:
        return base.absolute()


DATA_DIR = resolve_local_path("DATA_DIR", "data")
# Runtime state must be portable across local machines, CI and production.
_canonical_user_db = Path.home() / ".local/state/ultrarentable/ultrarentable.sqlite3"
_default_state_db = str(_canonical_user_db) if _canonical_user_db.exists() else "data/state/ultrarentable.sqlite3"
# ULTRARENTABLE_DB_PATH es un alias legacy: prioridad STATE_DB_PATH > ULTRARENTABLE_DB_PATH > default.
_state_db_default = os.getenv("ULTRARENTABLE_DB_PATH", _default_state_db)
STATE_DB_PATH = resolve_local_path("STATE_DB_PATH", _state_db_default)
LEARNING_DB_PATH = resolve_local_path(
    "LEARNING_DB_PATH", "~/.local/state/ultrarentable/learning_store.sqlite"
)
ARTIFACTS_DIR = resolve_local_path("ARTIFACTS_DIR", "data/artifacts")
LOCAL_WEB_ORIGINS = [
    value.strip()
    for value in os.getenv(
        "LOCAL_WEB_ORIGINS",
        "http://127.0.0.1:3000,http://localhost:3000,http://127.0.0.1:5000,http://localhost:5000,http://127.0.0.1:3001,http://localhost:3001,http://127.0.0.1:3002,http://localhost:3002,http://127.0.0.1:3003,http://localhost:3003,http://127.0.0.1:3004,http://localhost:3004,http://127.0.0.1:3005,http://localhost:3005",
    ).split(",")
    if value.strip()
]
