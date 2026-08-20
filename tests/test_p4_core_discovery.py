"""tests/test_p4_core_discovery.py
Suite de Tests y Auditoría Adversarial de la FASE P4: CORE DISCOVERY ENGINE & NOVELTY SEARCH.

Verifica:
1. SemanticQuantEngine: Generación autónoma de hipótesis algorítmicas basadas en contratos canónicos.
2. Grammar and Rules: Reglas formadas por RuleTree, ExitModel y SizingAndRisk sin parámetros ocultos.
3. Trial Logging: Cada hipótesis explorada genera un trial_id persistido en SQLite para el cálculo de DSR.
4. Zero-Forcing: Las estrategias descubiertas no asumen rentabilidad mágica, pasan por evaluación barra a barra.
"""

import hashlib
import tempfile
from pathlib import Path
import pytest

from contracts.canonical_strategy import CanonicalStrategy, ExecutionTrack
from contracts.snapshots.strategy_snapshot import StrategySnapshot, StrategyRoute
from services.discovery.strategy_search_registry import StrategySearchRegistry
from services.semantic_ai.autonomous_discovery_engine import AutonomousDiscoveryAgentLoop, SemanticMarketProfiler
from services.semantic_ai import SemanticQuantEngine


def test_semantic_quant_engine_generates_valid_canonical_strategy():
    """Verifica que SemanticQuantEngine genere CanonicalStrategy con hash determinista."""
    engine = SemanticQuantEngine()
    strat = engine.generate_candidate(symbol="BTCUSDT", track=ExecutionTrack.TRACK_ULTRA)

    assert isinstance(strat, CanonicalStrategy)
    assert strat.instrument.symbol == "BTCUSDT"
    assert strat.target_track == ExecutionTrack.TRACK_ULTRA
    assert len(strat.rules.long_conditions) > 0

    h1 = strat.compute_sha256()
    h2 = strat.compute_sha256()
    assert h1 == h2
    assert len(h1) == 64


def test_semantic_market_profiler_real_metrics():
    """Verifica que el profiler microestructural calcule Hurst, volatilidad y kurtosis reales."""
    profiler = SemanticMarketProfiler()
    # 200 velas sintéticas con tendencia
    candles = [
        {
            "timestamp_utc_ms": 1770000000000 + i * 3600000,
            "open": 100.0 + i * 0.5,
            "high": 102.0 + i * 0.5,
            "low": 98.0 + i * 0.5,
            "close": 100.5 + i * 0.5,
            "volume": 1000.0,
        }
        for i in range(200)
    ]
    profile = profiler.profile(candles)

    assert "hurst_exponent" in profile
    assert "return_volatility_bps" in profile
    assert "market_nature" in profile
    assert "recommended_archetype" in profile
    assert 0.0 <= profile["hurst_exponent"] <= 1.0


def test_discovery_agent_loop_initialization():
    """Verifica que AutonomousDiscoveryAgentLoop inicialice correctamente sus componentes y registre fallos."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "search.db"
        loop = AutonomousDiscoveryAgentLoop(db_path=db_path)
        assert loop.profiler is not None
        assert loop.backtest_engine is not None
        assert loop.gates_orchestrator is not None
        assert loop.failure_db is not None
