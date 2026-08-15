"""Bounded, fail-safe retention for FastEngine backtest artifacts."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import shutil
from typing import Iterable

from sqlalchemy.orm import Session

from services.api.app.config import ARTIFACTS_DIR
from services.api.app.db.database import BacktestModel


@dataclass(frozen=True)
class PruneCandidate:
    path: str
    bytes: int


@dataclass
class PruneReport:
    scanned: int = 0
    protected: int = 0
    skipped_recent: int = 0
    orphan_candidates: int = 0
    candidate_bytes: int = 0
    deleted: int = 0
    reclaimed_bytes: int = 0

    def to_dict(self) -> dict[str, int]:
        return asdict(self)


def _tree_size(path: Path) -> int:
    total = 0
    for current, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = [name for name in dirs if not (Path(current) / name).is_symlink()]
        for name in files:
            item = Path(current) / name
            if not item.is_symlink():
                total += item.stat().st_size
    return total


def _resolve_reference(value: str) -> Path:
    path = Path(value).expanduser()
    return path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()


def plan_orphan_prune(
    root: Path,
    protected_paths: Iterable[Path],
    *,
    min_age: timedelta = timedelta(hours=1),
    now: datetime | None = None,
) -> tuple[list[PruneCandidate], PruneReport]:
    root = root.expanduser().resolve()
    report = PruneReport()
    if not root.is_dir():
        return [], report

    protected = {path.expanduser().resolve() for path in protected_paths}
    current_time = now or datetime.now(timezone.utc)
    cutoff = current_time.timestamp() - max(0.0, min_age.total_seconds())
    candidates: list[PruneCandidate] = []

    for child in sorted(root.iterdir()):
        if not child.is_dir() or child.is_symlink():
            continue
        resolved = child.resolve()
        if resolved.parent != root:
            continue
        report.scanned += 1
        if resolved in protected:
            report.protected += 1
            continue
        if child.stat().st_mtime > cutoff:
            report.skipped_recent += 1
            continue
        size = _tree_size(child)
        candidates.append(PruneCandidate(path=str(resolved), bytes=size))
        report.orphan_candidates += 1
        report.candidate_bytes += size
    return candidates, report


def prune_orphan_backtests(
    db: Session,
    *,
    root: Path | None = None,
    min_age: timedelta = timedelta(hours=1),
    apply: bool = False,
    now: datetime | None = None,
) -> PruneReport:
    artifact_root = (root or (Path(ARTIFACTS_DIR) / "backtests")).resolve()
    references = {
        _resolve_reference(value)
        for (value,) in db.query(BacktestModel.artifacts_path)
        .filter(BacktestModel.artifacts_path.isnot(None))
        .all()
        if value
    }
    candidates, report = plan_orphan_prune(
        artifact_root, references, min_age=min_age, now=now
    )
    if not apply:
        return report

    for candidate in candidates:
        path = Path(candidate.path)
        if path.parent != artifact_root or path.is_symlink():
            continue
        shutil.rmtree(path)
        report.deleted += 1
        report.reclaimed_bytes += candidate.bytes
    return report
