from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RUNNER = ROOT / "scripts/phase2_research_run.py"
WORKFLOW = ROOT / ".github/workflows/phase2-live-data.yml"


def test_phase2_runner_is_finite_real_only_and_manifest_driven() -> None:
    source = RUNNER.read_text(encoding="utf-8")
    required = (
        "physicalFileSha256",
        "closedRecordsOnly",
        "completeHistory",
        "candles_is = candles[:idx_is]",
        "candles_val = candles[idx_is:idx_val]",
        "candles_blind_oos = candles[idx_val:]",
        "SearchTrialRecord",
        "PHASE2_MAX_TRIALS_ULTRA",
        "PHASE2_MAX_TRIALS_FONDEO",
        "strategy_snapshot=frozen",
    )
    for marker in required:
        assert marker in source, marker
    assert "while True" not in source
    assert "synthetic" not in source.lower()


def test_phase2_workflow_is_not_on_every_push() -> None:
    source = WORKFLOW.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in source
    assert "paths:" in source
    assert ".phase2/GO_NOW" in source
    assert "cancel-in-progress: false" in source
