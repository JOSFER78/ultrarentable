"""Canonical runtime paths for portable local, CI, container and production execution.

All filesystem locations must be derived from this module rather than hard-coded
absolute developer-machine paths.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repository root: services/core/runtime_paths.py -> repository root is parents[2].
REPO_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = Path(os.getenv("ULTRARENTABLE_DATA_DIR", str(REPO_ROOT / "data" / "normalized"))).resolve()
STATE_DIR = Path(
    os.getenv("ULTRARENTABLE_STATE_DIR", str(REPO_ROOT / ".runtime" / "state"))
).resolve()
DB_PATH = Path(
    os.getenv("ULTRARENTABLE_DB_PATH", str(STATE_DIR / "ultrarentable.sqlite3"))
).resolve()


def ensure_state_dir() -> Path:
    """Create and return the configured writable runtime state directory."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def resolve_dataset_dir() -> Path:
    """Return the configured normalized dataset directory."""
    return DATA_DIR


__all__ = ["REPO_ROOT", "DATA_DIR", "STATE_DIR", "DB_PATH", "ensure_state_dir", "resolve_dataset_dir"]
