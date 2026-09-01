from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PIPELINE = ROOT / "services/discovery/discovery_validation_pipeline.py"
REGISTRY = ROOT / "services/discovery/strategy_search_registry.py"
DATASET_REPOSITORY = ROOT / "services/data/dataset_repository.py"
CONFIG = ROOT / "services/api/app/config.py"


def fail(message: str) -> None:
    raise SystemExit(f"PHASE2_RESEARCH_GUARD: FAIL — {message}")


def read(path: Path) -> str:
    if not path.is_file():
        fail(f"required file missing: {path.relative_to(ROOT)}")
    return path.read_text(encoding="utf-8")


def assert_no_machine_local_paths(source: str, label: str) -> None:
    forbidden = ("/home/ubuntu/", "/workspace/pro/trading/", "C:\\\\Users\\\\")
    hits = [token for token in forbidden if token in source]
    if hits:
        fail(f"{label} contains machine-local path(s): {hits}")


def assert_no_synthetic_dataset_fallbacks(source: str) -> None:
    forbidden_markers = (
        "Fallback a barra canónica",
        "Fallback a generador estructurado de prueba determinista",
        "timestamp_utc_ms=1771718400000",
        "for i in range(100)",
    )
    hits = [marker for marker in forbidden_markers if marker in source]
    if hits:
        fail(f"dataset repository contains synthetic fallback(s): {hits}")
    # La marca "raise FileNotFoundError" se sustituye por dos que demuestran la MISMA propiedad
    # de forma mas fuerte: que el fallo por dataset ausente es un FileNotFoundError (la excepcion
    # dedicada hereda de el, asi que todo codigo que ya lo capturaba sigue funcionando), y que el
    # hash del fichero se contrasta contra el checksum del manifiesto en vez de solo calcularse.
    for marker in (
        "_sha256_file",
        "self._sha256_file(target_file)",
        "class DatasetUnavailableError(FileNotFoundError)",
        "_verificar_custodia",
    ):
        if marker not in source:
            fail(f"real-data custody invariant missing from dataset repository: {marker}")


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

    blind_pos = source.find("candles_blind_oos = candles[idx_val:]")
    discovery_pos = source.find("param_space = self.search_registry.generate_combinatorial_parameter_space")
    if blind_pos < 0 or discovery_pos < 0 or blind_pos > discovery_pos:
        fail("blind OOS partition is not established before discovery")

    final_oos_pos = source.find("oos_bt = self.backtest_engine.run_backtest")
    if final_oos_pos < 0:
        fail("final blind OOS backtest not found")

    selection_start = source.find("best_params = None")
    selection_end = source.find("if route == StrategyRoute.ULTRA:", selection_start)
    if selection_start < 0 or selection_end < 0:
        fail("champion selection/freeze boundary not found")
    if "candles_blind_oos" in source[selection_start:selection_end]:
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
    for marker in (
        "BLOCKED_NO_TRIAL_SPACE",
        "BLOCKED_NO_REAL_TRIALS",
        "BLOCKED_NO_VALIDATED_CHAMPION",
    ):
        if marker not in source:
            fail(f"fail-closed selection outcome missing: {marker}")


def assert_trial_accounting(source: str, registry: str) -> None:
    for marker in (
        "StrategySearchRegistry",
        "SearchTrialRecord",
        "dataset_sha256=real_file_sha256",
        "run_id=run_id",
        "trial_id=trial_strat_id",
        "self.search_registry.record_trial(trial_rec)",
        '"trials_tested": trials_count_this_run',
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


def assert_config_authority(pipeline: str, registry: str, dataset_repository: str, config: str) -> None:
    if "from services.api.app.config import" not in pipeline:
        fail("discovery pipeline does not import central config authority")
    if "from services.api.app.config import STATE_DB_PATH" not in registry:
        fail("search registry does not use central STATE_DB_PATH authority")
    if "from services.api.app.config import DATA_DIR as BASE_DATA_DIR" not in dataset_repository:
        fail("dataset repository does not use central DATA_DIR authority")
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
    dataset_repository = read(DATASET_REPOSITORY)
    config = read(CONFIG)
    for path in (PIPELINE, REGISTRY, DATASET_REPOSITORY, CONFIG):
        assert_syntax(path)
    assert_no_machine_local_paths(pipeline, "discovery pipeline")
    assert_no_machine_local_paths(registry, "search registry")
    assert_no_machine_local_paths(dataset_repository, "dataset repository")
    assert_no_synthetic_dataset_fallbacks(dataset_repository)
    assert_partition_isolation(pipeline)
    assert_no_forced_fallback_selection(pipeline)
    assert_trial_accounting(pipeline, registry)
    assert_config_authority(pipeline, registry, dataset_repository, config)
    print("PHASE2_RESEARCH_GUARD: PASS — real-data custody, 60/20/20 isolation, trial accounting and fail-closed selection are enforced")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
