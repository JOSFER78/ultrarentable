from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import os

from services.api.app.maintenance.artifact_retention import plan_orphan_prune


def test_prune_plan_protects_referenced_skips_recent_and_rejects_symlink(tmp_path: Path) -> None:
    root = tmp_path / "backtests"
    root.mkdir()
    old = datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp()

    protected = root / "protected"
    protected.mkdir()
    (protected / "ledger.json").write_bytes(b"keep")
    os.utime(protected, (old, old))

    orphan = root / "orphan"
    orphan.mkdir()
    (orphan / "ledger.json").write_bytes(b"delete-me")
    os.utime(orphan, (old, old))

    recent = root / "recent"
    recent.mkdir()
    (recent / "ledger.json").write_bytes(b"wait")
    symlink = root / "outside-link"
    symlink.symlink_to(tmp_path, target_is_directory=True)

    now = datetime(2026, 1, 2, tzinfo=timezone.utc)
    candidates, report = plan_orphan_prune(
        root,
        [protected],
        min_age=timedelta(hours=1),
        now=now,
    )

    assert [Path(item.path).name for item in candidates] == ["orphan"]
    assert candidates[0].bytes == len(b"delete-me")
    assert report.scanned == 3
    assert report.protected == 1
    assert report.skipped_recent == 1
    assert report.orphan_candidates == 1
