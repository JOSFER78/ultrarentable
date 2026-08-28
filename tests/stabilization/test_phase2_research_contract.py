"""Regression tests for the real Phase-2 research contract."""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts" / "phase2_research_run.py"
WORKFLOW = ROOT / ".github" / "workflows" / "phase2-live-data.yml"
BLIND = ROOT / "scripts" / "phase2_blind_oos.py"


def test_phase2_runner_is_finite_real_only_and_manifest_driven() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    required = (
        "physicalFileSha256",
        "closedRecordsOnly",
        "completeHistory",
        "candles_is = candles[:idx_is]",
        "candles_val = candles[idx_is:idx_val]",
        "strategy_snapshot_hash",
        '"phase2-frozen-champion-v1"',
        '"FROZEN_VALIDATION_CHAMPION"',
        '"NOT_CONSUMED"',
        "SearchTrialRecord",
        "PHASE2_MAX_TRIALS_ULTRA",
        "PHASE2_MAX_TRIALS_FONDEO",
    )
    for marker in required:
        assert marker in source, marker
    assert "while True" not in source
    assert "synthetic" not in source.lower()


def test_phase2_research_is_manual_only() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "push:" not in source
    assert "pull_request:" not in source
    assert "cancel-in-progress: false" in source


def test_blind_oos_is_separate_from_research_runner() -> None:
    source = BLIND.read_text(encoding="utf-8")
    required = (
        "phase2-frozen-champion-v1",
        "CHAMPION_NOT_FROZEN",
        "BLIND_OOS_ALREADY_CONSUMED",
        "STRATEGY_HASH_MISMATCH",
        "DATASET_HASH_MATCH_COUNT",
        "DATASET_ID_MISMATCH",
        "PHYSICAL_HASH_MISMATCH",
    )
    for marker in required:
        assert marker in source, marker
