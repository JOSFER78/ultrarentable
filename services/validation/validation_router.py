"""services/validation/validation_router.py
Router FastAPI para Quant Validation Fabric (QVF) y Candidate Registry FSM.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from contracts.canonical_strategy import CanonicalStrategy, StrategyLifecycleStatus
from contracts.validation_contracts import (
    BalaExecutionRecord,
    EvidenceGateDecision,
    ValidationTrack,
)
from services.core.event_bus import CandidatePromotedEvent, ValidationCompletedEvent, event_bus
from services.validation.candidate_registry import (
    CandidateRegistry,
    InvalidStateTransitionError,
    StateTransitionRecord,
)
from services.validation.quant_validation_fabric import QuantValidationFabric

router = APIRouter()

fabric_instance = QuantValidationFabric()
registry_instance = CandidateRegistry()


class ValidationEvaluationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_id: str
    track: ValidationTrack
    # Payload Fondeo
    is_trades: Optional[List[float]] = None
    oos_trades: Optional[List[float]] = None
    daily_pnls: Optional[List[float]] = None
    dsr_score: float = 2.5
    mc_ruin_pct: float = 0.0
    # Payload Ultra
    is_balas: Optional[List[BalaExecutionRecord]] = None
    oos_balas: Optional[List[BalaExecutionRecord]] = None


from contracts.evidence_bundle import EvidenceBundle


class TransitionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    strategy_id: str
    to_status: StrategyLifecycleStatus
    reason: str = Field(..., min_length=3)
    evidence_bundle: Optional[EvidenceBundle] = None


@router.post("/evaluate", response_model=EvidenceGateDecision)
async def evaluate_strategy_gate(req: ValidationEvaluationRequest) -> EvidenceGateDecision:
    """Evalúa un candidato a través del Evidence Gate según su Execution Track."""
    payload: Dict[str, Any] = {}
    if req.track == ValidationTrack.TRACK_FONDEO:
        if req.is_trades is None or req.oos_trades is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_FONDEO requiere 'is_trades' y 'oos_trades'.",
            )
        payload = {
            "is_trades": req.is_trades,
            "oos_trades": req.oos_trades,
            "daily_pnls": req.daily_pnls or [],
            "dsr_score": req.dsr_score,
            "mc_ruin_pct": req.mc_ruin_pct,
        }
    elif req.track == ValidationTrack.TRACK_ULTRA:
        if req.is_balas is None or req.oos_balas is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="TRACK_ULTRA requiere 'is_balas' y 'oos_balas'.",
            )
        payload = {
            "is_balas": req.is_balas,
            "oos_balas": req.oos_balas,
        }

    decision = fabric_instance.validate(req.strategy_id, req.track, payload)
    await event_bus.publish(ValidationCompletedEvent(decision=decision))
    return decision


@router.post("/registry/register", status_code=status.HTTP_201_CREATED)
async def register_candidate(strategy: CanonicalStrategy) -> Dict[str, Any]:
    """Registra una nueva estrategia canónica en la FSM."""
    try:
        registry_instance.register(strategy)
        return {
            "status": "REGISTERED",
            "strategy_id": strategy.strategy_id,
            "lifecycle_status": strategy.status.value,
            "sha256": strategy.compute_sha256(),
        }
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(err))


@router.post("/registry/transition", response_model=StateTransitionRecord)
async def transition_candidate_status(req: TransitionRequest) -> StateTransitionRecord:
    """Aplica una transición de estado discreto en la FSM."""
    try:
        record = registry_instance.transition(
            strategy_id=req.strategy_id,
            to_status=req.to_status,
            reason=req.reason,
            evidence_bundle=req.evidence_bundle,
        )
        await event_bus.publish(
            CandidatePromotedEvent(
                strategy_id=req.strategy_id,
                new_status=req.to_status.value,
                track="DUAL",
            )
        )
        return record
    except (KeyError, InvalidStateTransitionError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))


@router.get("/registry/status/{strategy_id}")
async def get_candidate_status(strategy_id: str) -> Dict[str, str]:
    """Obtiene el estado actual en la FSM para una estrategia."""
    try:
        current_status = registry_instance.get_status(strategy_id)
        return {"strategy_id": strategy_id, "status": current_status.value}
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err))


@router.get("/registry/history/{strategy_id}", response_model=List[StateTransitionRecord])
async def get_candidate_history(strategy_id: str) -> List[StateTransitionRecord]:
    """Historial inmutable de transiciones de una estrategia."""
    return registry_instance.get_history(strategy_id)


@router.get("/registry/list")
async def list_candidates(status_filter: Optional[StrategyLifecycleStatus] = None) -> Dict[str, Any]:
    """Lista estrategias registradas, opcionalmente filtradas por estado."""
    if status_filter:
        ids = registry_instance.list_by_status(status_filter)
        return {"status": status_filter.value, "count": len(ids), "strategy_ids": ids}
    return {
        status_enum.value: registry_instance.list_by_status(status_enum)
        for status_enum in StrategyLifecycleStatus
    }


# ----------------------------------------------------------------------------
# 11 MODULAR VALIDATION ENGINES ENDPOINTS
# ----------------------------------------------------------------------------
from services.validation.registry.adaptadores import ModularValidationPipeline

modular_pipeline = ModularValidationPipeline()


class Validate11GatesRequest(BaseModel):
    strategy_id: str = Field(..., description="Unique Strategy ID")
    name: str = Field(..., description="Strategy name")
    symbol: str = Field("BTC-USDT", description="Trading asset symbol")
    timeframe: str = Field("1h", description="Timeframe")
    route: str = Field("ULTRA", description="ULTRA or FONDEO")
    raw_trades_is: List[float] = Field(default_factory=list, description="In-sample trade PnLs in USD")
    raw_trades_oos: List[float] = Field(default_factory=list, description="Out-of-sample trade PnLs in USD")
    rules_text: Optional[str] = Field("", description="Strategy rules signature")
    regime_pnls: Optional[Dict[str, float]] = Field(None, description="PnL breakdown by market regime")


@router.get("/engines")
async def list_modular_validation_engines() -> Dict[str, Any]:
    """Retorna el catálogo oficial de los 11 motores desacoplados de validación."""
    return {
        "total_engines": 11,
        "mode": "REAL_ONLY_MODULAR",
        "engines": [
            {
                "gate_id": 1,
                "engine_name": "Gate01_IngestSanityEngine",
                "purpose": "Integridad física de OHLCV, ticks, gaps temporales y ausencia de NaNs",
                "module_path": "services/validation/engines/gate_01_ingest_sanity.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 2,
                "engine_name": "Gate02_DeterministicBacktestEngine",
                "purpose": "Simulación determinista con comisiones reales BingX (0.05%) y slippage (3 ticks)",
                "module_path": "services/validation/engines/gate_02_deterministic_backtest.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 3,
                "engine_name": "Gate03_TradeSignificanceEngine",
                "purpose": "Mínimo de trades estadísticamente significativo (>= 20 OOS, >= 40 total)",
                "module_path": "services/validation/engines/gate_03_trade_significance.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 4,
                "engine_name": "Gate04_WalkForwardEfficiencyEngine",
                "purpose": "Walk-Forward Efficiency IS/OOS (WFE >= 0.50, Profit Factor OOS >= 1.20)",
                "module_path": "services/validation/engines/gate_04_walk_forward_efficiency.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 5,
                "engine_name": "Gate05_MonteCarloStressEngine",
                "purpose": "1.000 simulaciones de permutación y reordenamiento, riesgo de ruina <= 1.0%",
                "module_path": "services/validation/engines/gate_05_monte_carlo_stress.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 6,
                "engine_name": "Gate06_FrictionStressEngine",
                "purpose": "Estrés a fricción duplicada (+5 bps + 2x slippage) y retención de rentabilidad",
                "module_path": "services/validation/engines/gate_06_friction_stress.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 7,
                "engine_name": "Gate07_MarketRegimeCoverageEngine",
                "purpose": "Verificación de comportamiento en regímenes alcista, bajista y lateral",
                "module_path": "services/validation/engines/gate_07_market_regime_coverage.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 8,
                "engine_name": "Gate08_DeflatedSharpeEngine",
                "purpose": "Deflated Sharpe Ratio (DSR de Bailey & López de Prado) penalizando múltiples ensayos",
                "module_path": "services/validation/engines/gate_08_deflated_sharpe.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 9,
                "engine_name": "Gate09_NoveltyAntiOverfitEngine",
                "purpose": "Auditoría contra FailureKnowledgeDB para descartar clones y sobreajustes conocidos",
                "module_path": "services/validation/engines/gate_09_novelty_antioverfit.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 10,
                "engine_name": "Gate10_SemanticAIDebateEngine",
                "purpose": "Deliberación cualitativa de 5 agentes IA (Interpreter, Critic, Improver, Regime, Adversarial)",
                "module_path": "services/validation/engines/gate_10_semantic_ai_debate.py",
                "isolated_testable": True,
            },
            {
                "gate_id": 11,
                "engine_name": "Gate11_EnsembleSynergyEngine",
                "purpose": "Sinergia multi-activo, correlación cruzada (< 0.35) y ponderación inversa por volatilidad",
                "module_path": "services/validation/engines/gate_11_ensemble_synergy.py",
                "isolated_testable": True,
            },
        ],
    }


@router.post("/validate-11-gates")
async def validate_strategy_11_gates(req: Validate11GatesRequest) -> Dict[str, Any]:
    """Ejecuta el pipeline secuencial completo de los 11 motores desacoplados."""
    report = modular_pipeline.validate_candidate(
        strategy_id=req.strategy_id,
        name=req.name,
        symbol=req.symbol,
        timeframe=req.timeframe,
        route=req.route,
        raw_trades_is=req.raw_trades_is,
        raw_trades_oos=req.raw_trades_oos,
        rules_text=req.rules_text or "",
        regime_pnls=req.regime_pnls,
    )
    return {
        "strategy_id": report.strategy_id,
        "name": report.name,
        "route": report.route,
        "all_passed": report.all_passed,
        "failed_at_gate": report.failed_at_gate,
        "total_execution_time_ms": report.total_execution_time_ms,
        "gate_reports": [
            {
                "gate_id": g.gate_id,
                "gate_name": g.gate_name,
                "passed": g.passed,
                "execution_time_ms": g.execution_time_ms,
                "details": g.details,
                "rejection_reasons": g.rejection_reasons,
            }
            for g in report.gate_reports
        ],
    }
