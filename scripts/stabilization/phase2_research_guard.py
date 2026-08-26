from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "services/discovery/discovery_validation_pipeline.py"
REGISTRY = ROOT / "services/discovery/strategy_search_registry.py"
CONFIG = ROOT / "services/api/app/config.py"


def fail(message: str) -> None:
    raise SystemExit(f"PHASE2_RESEARCH_GUARD: FAIL — {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"required file missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def assert_no_machine_local_paths(source: str, label: str) -> None:
    forbidden = (
        "/home/ubuntu/",
        "/workspace/pro/trading/",
        "C:\\\\Users\\\\",
    )
    hits = [token for token in forbidden if token in source]
    if hits:
        fail(f"{label} contains machine-local path(s): {hits}")


def assert_partition_isolation(source: str) -> None:
    required = (
        "idx_is = int(total_bars * 0.60)",
        "idx_val = int(total_bars * 0.80)",
        "candles_is = candles[:idx_is]",
        "candles_val = candles[idx_is:idx_val]",
        "candles_blind_oos = candles[idx_val:]",
    )
    for marker in required:
        if marker not in source:
            fail(f"missing chronological partition invariant: {marker}")

    discovery_pos = source.find("# 4. Discovery Combinatorio")
    blind_pos = source.find("candles_blind_oos = candles[idx_val:]")
    if discovery_pos < 0 or blind_pos < 0 or blind_pos > discovery_pos:
        fail("blind OOS partition is not established before discovery")

    final_oos_pos = source.find("oos_bt = self.backtest_engine.run_backtest")
    if final_oos_pos < 0:
        fail("final blind OOS backtest not found")

    selection_start = source.find("# 6. Evaluación Ciega en Validation")
    if selection_start < 0:
        fail("validation selection block not found")
    selection_end = source.find("# 7. Generar Snapshot", selection_start)
    if selection_end < 0:
        fail("strategy freeze boundary not found")

    selection_block = source[selection_start:selection_end]
    if "candles_blind_oos" in selection_block:
        fail("blind OOS is referenced inside the champion-selection block")


def assert_no_forced_fallback_selection(source: str) -> None:
    forbidden_snippets = (
        '"sl_atr_mult": 2.0',
        '"tp_atr_mult": 6.0',
        '"ema_fast": 20, "ema_slow": 50',
        "best_params = top_is_candidates[0][1] if top_is_candidates else",
    )
    hits = [snippet for snippet in forbidden_snippets if snippet in source]
    if hits:
        fail(f"forced strategy fallback/default detected: {hits}")


def assert_trial_accounting(source: str, registry: str) -> None:
    for marker in (
        "StrategySearchRegistry",
        "SearchTrialRecord",
        "dataset_sha256=real_file_sha256",
        "run_id=run_id",
        "trial_id=trial_strat_id",
        "self.search_registry.record_trial(trial_rec)",
    ):
        if marker not in source:
            fail(f"trial accounting invariant missing: {marker}")

    for marker in (
        "dataset_sha256: str",
        "run_id: str",
        "trial_id: str",
        "INSERT OR REPLACE INTO discovery_search_trials",
    ):
        if marker not in registry:
            fail(f"registry custody field missing: {marker}")


def assert_config_authority(pipeline: str, registry: str, config: str) -> None:
    if "from services.api.app.config import" not in pipeline:
        fail("discovery pipeline does not import central config authority")
    if "from services.api.app.config import STATE_DB_PATH" not in registry:
        fail("search registry does not use central STATE_DB_PATH authority")
    for marker in ("DATA_DIR = resolve_local_path", "STATE_DB_PATH = resolve_local_path"):
        if marker not in config:
            fail(f"central config invariant missing: {marker}")


def assert_syntax(path: Path) -> None:
    try:
        ast.parse(read(path))
    except SyntaxError as exc:
        fail(f"syntax error in {path.relative_to(ROOT)}: {exc}")


def main() -> int:
    pipeline = read(PIPELINE)
    registry = read(REGISTRY)
    config = read(CONFIG)

    assert_syntax(PIPELINE)
    assert_syntax(REGISTRY)
    assert_syntax(CONFIG)
    assert_no_machine_local_paths(pipeline, "discovery pipeline")
    assert_no_machine_local_paths(registry, "search registry")
    assert_partition_isolation(pipeline)
    assert_no_forced_fallback_selection(pipeline)
    assert_trial_accounting(pipeline, registry)
    assert_config_authority(pipeline, registry, config)

    print("PHASE2_RESEARCH_GUARD: PASS — discovery boundaries, trial custody and config authority are statically enforced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
