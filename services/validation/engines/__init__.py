"""services/validation/engines/__init__.py
Módulo de 11 Motores de Validación Desacoplados para Ultrarentable V2.
Cada fase es un motor individual, configurable, testable y auditable de forma aislada.
"""

from services.validation.engines.gate_01_ingest_sanity import IngestSanityEngine
from services.validation.engines.gate_02_deterministic_backtest import DeterministicBacktestEngine
from services.validation.engines.gate_03_trade_significance import TradeSignificanceEngine
from services.validation.engines.gate_04_walk_forward_efficiency import WalkForwardEfficiencyEngine
from services.validation.engines.gate_05_monte_carlo_stress import MonteCarloStressEngine
from services.validation.engines.gate_06_friction_stress import FrictionStressEngine
from services.validation.engines.gate_07_market_regime_coverage import MarketRegimeCoverageEngine
from services.validation.engines.gate_08_deflated_sharpe import DeflatedSharpeEngine
from services.validation.engines.gate_09_novelty_antioverfit import NoveltyAntiOverfitEngine
from services.validation.engines.gate_10_semantic_ai_debate import SemanticAIDebateEngine
from services.validation.engines.gate_11_ensemble_synergy import EnsembleSynergyEngine
from services.validation.engines.pipeline_orchestrator import ModularValidationPipeline

__all__ = [
    "IngestSanityEngine",
    "DeterministicBacktestEngine",
    "TradeSignificanceEngine",
    "WalkForwardEfficiencyEngine",
    "MonteCarloStressEngine",
    "FrictionStressEngine",
    "MarketRegimeCoverageEngine",
    "DeflatedSharpeEngine",
    "NoveltyAntiOverfitEngine",
    "SemanticAIDebateEngine",
    "EnsembleSynergyEngine",
    "ModularValidationPipeline",
]
