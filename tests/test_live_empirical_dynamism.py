"""tests/test_live_empirical_dynamism.py
Verificación Empírica del Comportamiento Dinámico y Agnóstico del Motor Universal.
Demuestra que un único motor Python procesa cualquier activo, temporalidad y ruta sin hardcodes.
"""

from pathlib import Path
import pytest
from services.optimization.universal_optimizer_engine import UniversalStrategyOptimizer
from services.optimization.quantitative_arsenal import MicrostructureProfiler
from services.portfolio.meta_ensemble_service import MetaEnsembleService


def test_empirical_dynamism_across_different_asset_classes():
    """Demuestra que el MicrostructureProfiler y el Optimizer adaptan sus cálculos a cada activo dinámicamente."""
    opt = UniversalStrategyOptimizer()

    # 1. Resolver 3 datasets de clases de activos totalmente distintas
    btc_file = opt.resolve_dataset_file("BTC-USDT", "15m")
    nq_file = opt.resolve_dataset_file("NQ", "15m")
    eur_file = opt.resolve_dataset_file("EURUSD", "1h")

    assert btc_file is not None and btc_file.exists(), "Dataset BTC 15m debe existir"
    assert nq_file is not None and nq_file.exists(), "Dataset NQ 15m debe existir"
    assert eur_file is not None and eur_file.exists(), "Dataset EURUSD 1h debe existir"

    candles_btc = opt.load_real_candles(btc_file)
    candles_nq = opt.load_real_candles(nq_file)
    candles_eur = opt.load_real_candles(eur_file)

    # 2. Computar perfiles microestructurales
    prof_btc = MicrostructureProfiler.compute_profile(candles_btc[:500])
    prof_nq = MicrostructureProfiler.compute_profile(candles_nq[:500])
    prof_eur = MicrostructureProfiler.compute_profile(candles_eur[:500])

    print(f"\n[PERFIL BTC 15m] Hurst={prof_btc.hurst_exponent:.3f}, ParkinsonVol={prof_btc.parkinson_volatility:.5f}, ATR_P25={prof_btc.atr_p25:.4f}, SL_ATR_Mult={prof_btc.optimal_sl_atr_mult:.2f}")
    print(f"[PERFIL NQ 15m]  Hurst={prof_nq.hurst_exponent:.3f}, ParkinsonVol={prof_nq.parkinson_volatility:.5f}, ATR_P25={prof_nq.atr_p25:.4f}, SL_ATR_Mult={prof_nq.optimal_sl_atr_mult:.2f}")
    print(f"[PERFIL EUR 1h]  Hurst={prof_eur.hurst_exponent:.3f}, ParkinsonVol={prof_eur.parkinson_volatility:.5f}, ATR_P25={prof_eur.atr_p25:.4f}, SL_ATR_Mult={prof_eur.optimal_sl_atr_mult:.2f}")

    # Verificar que los valores NO son iguales (no hay hardcode estático)
    assert prof_btc.parkinson_volatility != prof_nq.parkinson_volatility
    assert prof_btc.parkinson_volatility != prof_eur.parkinson_volatility
    assert prof_btc.atr_mean != prof_eur.atr_mean


def test_meta_ensemble_strategy_of_strategies_generation():
    """Demuestra la capacidad de generar Meta-Estrategias ensamblando estrategias de distintas fuentes."""
    service = MetaEnsembleService()
    candidate_ids = ["UR_ULTRA_ETH_USDT_1H", "UR_ULTRA_SOL_USDT_4H", "UR_ULTRA_BNB_USDT_4H"]
    ensemble = service.assemble_meta_strategy(
        candidate_ids=candidate_ids,
        ensemble_name="Meta-Ensemble Ultra Multi-Asset 24/7",
        target_route="ULTRA",
    )
    assert ensemble is not None
    assert ensemble.ensemble_id is not None
    assert len(ensemble.components) == 3
    assert ensemble.combined_profit_factor > 0.0
    print(f"\n[META-ESTRATEGIA ENSAMBLADA] ID={ensemble.ensemble_id}, Sharpe={ensemble.combined_sharpe_ratio:.2f}, DD_Max={ensemble.combined_max_dd_pct:.2f}%, PF={ensemble.combined_profit_factor:.2f}")
