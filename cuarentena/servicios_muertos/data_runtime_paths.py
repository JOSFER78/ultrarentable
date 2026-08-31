"""Canonical, portable runtime paths for Ultrarentable.

Production code must not hard-code developer/runner absolute paths.  Paths are
resolved from explicit environment variables and otherwise from the repository
root.  Tests can inject temporary paths without changing production contracts.
"""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    return Path(os.getenv("ULTRARENTABLE_DATA_DIR", REPO_ROOT / "data" / "normalized"))


def state_dir() -> Path:
    return Path(os.getenv("ULTRARENTABLE_STATE_DIR", REPO_ROOT / ".runtime" / "state"))


def db_path() -> Path:
    return Path(os.getenv("ULTRARENTABLE_DB_PATH", state_dir() / "ultrarentable.sqlite3"))
