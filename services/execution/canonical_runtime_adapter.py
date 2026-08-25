"""services/execution/canonical_runtime_adapter.py
Adaptador y Motor de Ejecución en Runtime para CanonicalStrategy (Fase 02 Rework AG2-P02-003).
ZERO-MOCKS · REAL-ONLY · DETERMINISTIC · NO-LOOKAHEAD · PROVENANCE-LOCKED
Demuestra la traza física de consumo y equivalencia semántica de CanonicalStrategy.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ExecutableRuntimeInstruction,
    IndicatorSpec,
    LogicalOp,
)


@dataclass(frozen=True)
class EvaluatedTrade:
    entry_bar_index: int
    entry_time_ms: int
    entry_price: float
    direction: str
    exit_bar_index: int
    exit_time_ms: int
    exit_price: float
    exit_reason: str
    pnl_r: float
    pnl_usd: float


@dataclass(frozen=True)
class RuntimeExecutionResult:
    strategy_id: str
    strategy_version: str
    strategy_hash: str
    engine_version: str
    policy_version: str
    dataset_id: str
    dataset_sha256: str
    total_trades: int
    trades: List[EvaluatedTrade]
    execution_hash: str


class CanonicalRuntimeAdapter:
    """Ejecutor determinista de CanonicalStrategy que consume exclusivamente ExecutableRuntimeInstruction."""

    def __init__(self, engine_version: str = "5.4.0", policy_version: str = "5.4.0"):
        self.engine_version = engine_version
        self.policy_version = policy_version

    def compile_strategy(self, strategy: CanonicalStrategy) -> ExecutableRuntimeInstruction:
        """Punto de entrada canónico: compila y valida la estrategia."""
        return strategy.compile_to_runtime()

    def _eval_indicator(self, spec: IndicatorSpec, bars: List[Dict[str, Any]], current_idx: int) -> float:
        """Calcula el valor del indicador en el índice actual respetando el shift exacto."""
        eval_idx = current_idx - spec.shift
        if eval_idx < 0 or eval_idx >= len(bars):
            return float("nan")

        source = spec.source_field.lower()
        if spec.name in ["CLOSE", "PRICE_CLOSE", "PRICE"]:
            return float(bars[eval_idx].get(source, bars[eval_idx].get("close", 0.0)))
        if spec.name in ["OPEN", "PRICE_OPEN"]:
            return float(bars[eval_idx].get("open", 0.0))
        if spec.name in ["HIGH", "PRICE_HIGH"]:
            return float(bars[eval_idx].get("high", 0.0))
        if spec.name in ["LOW", "PRICE_LOW"]:
            return float(bars[eval_idx].get("low", 0.0))

        # Indicadores técnicos (EMA, SMA, etc.)
        period = int(spec.params.get("period", 14))
        if eval_idx < period - 1:
            return float("nan")

        if spec.name == "SMA":
            vals = [float(bars[i].get(source, bars[i].get("close", 0.0))) for i in range(eval_idx - period + 1, eval_idx + 1)]
            return sum(vals) / len(vals)

        if spec.name == "EMA":
            k = 2.0 / (period + 1)
            ema = float(bars[0].get(source, bars[0].get("close", 0.0)))
            for i in range(1, eval_idx + 1):
                val = float(bars[i].get(source, bars[i].get("close", 0.0)))
                ema = (val * k) + (ema * (1.0 - k))
            return ema

        # Fallback a close si indicador no paramétrico
        return float(bars[eval_idx].get(source, bars[eval_idx].get("close", 0.0)))

    def _eval_condition(self, cond: Dict[str, Any], bars: List[Dict[str, Any]], current_idx: int) -> bool:
        """Evalúa un nodo atómico de condición."""
        left = cond["left"]
        right = cond["right"]
        op = cond["op"]

        left_val = self._eval_indicator(IndicatorSpec(**left), bars, current_idx) if isinstance(left, dict) else float(left)
        right_val = self._eval_indicator(IndicatorSpec(**right), bars, current_idx) if isinstance(right, dict) else float(right)

        if left_val != left_val or right_val != right_val:  # NaN check
            return False

        if op in [ComparisonOp.GT.value, ">"]:
            return left_val > right_val
        if op in [ComparisonOp.GTE.value, ">="]:
            return left_val >= right_val
        if op in [ComparisonOp.LT.value, "<"]:
            return left_val < right_val
        if op in [ComparisonOp.LTE.value, "<="]:
            return left_val <= right_val
        if op in [ComparisonOp.EQ.value, "=="]:
            return left_val == right_val
        if op in [ComparisonOp.CROSS_ABOVE.value, "CROSS_ABOVE"]:
            if current_idx < 1:
                return False
            prev_left = self._eval_indicator(IndicatorSpec(**left), bars, current_idx - 1) if isinstance(left, dict) else float(left)
            prev_right = self._eval_indicator(IndicatorSpec(**right), bars, current_idx - 1) if isinstance(right, dict) else float(right)
            return (prev_left <= prev_right) and (left_val > right_val)
        if op in [ComparisonOp.CROSS_BELOW.value, "CROSS_BELOW"]:
            if current_idx < 1:
                return False
            prev_left = self._eval_indicator(IndicatorSpec(**left), bars, current_idx - 1) if isinstance(left, dict) else float(left)
            prev_right = self._eval_indicator(IndicatorSpec(**right), bars, current_idx - 1) if isinstance(right, dict) else float(right)
            return (prev_left >= prev_right) and (left_val < right_val)

        return False

    def evaluate_entry_trigger(self, instruction: ExecutableRuntimeInstruction, bars: List[Dict[str, Any]], current_idx: int) -> bool:
        """Evalúa el disparador de entrada respetando explícitamente el operador lógico AND / OR (P02-003-02)."""
        if not instruction.compiled_conditions:
            return False

        results = [self._eval_condition(cond, bars, current_idx) for cond in instruction.compiled_conditions]

        if instruction.logical_operator == LogicalOp.AND:
            return all(results)
        elif instruction.logical_operator == LogicalOp.OR:
            return any(results)
        return False

    def execute_backtest(
        self,
        strategy: CanonicalStrategy,
        bars: List[Dict[str, Any]],
        dataset_id: str,
        dataset_sha256: str,
    ) -> RuntimeExecutionResult:
        """Ejecuta el backtest completo consumiendo la CanonicalStrategy y preservando linaje estricto (P02-003-03)."""
        instruction = self.compile_strategy(strategy)
        trades: List[EvaluatedTrade] = []

        in_pos = False
        entry_idx = 0
        entry_price = 0.0
        entry_time_ms = 0

        sl_val = instruction.sl_config["value"]
        tp_val = instruction.tp_config["value"]

        for i in range(len(bars)):
            bar = bars[i]
            cur_close = float(bar.get("close", 0.0))
            cur_time = int(bar.get("timestamp_utc_ms", bar.get("time", 0)))

            if not in_pos:
                if self.evaluate_entry_trigger(instruction, bars, i):
                    in_pos = True
                    entry_idx = i
                    entry_price = cur_close
                    entry_time_ms = cur_time
            else:
                # Simulación determinista de SL y TP
                price_change_pct = (cur_close - entry_price) / entry_price
                if price_change_pct <= -(sl_val / 100.0):
                    trades.append(EvaluatedTrade(
                        entry_bar_index=entry_idx,
                        entry_time_ms=entry_time_ms,
                        entry_price=entry_price,
                        direction=instruction.direction,
                        exit_bar_index=i,
                        exit_time_ms=cur_time,
                        exit_price=cur_close,
                        exit_reason="STOP_LOSS",
                        pnl_r=-1.0,
                        pnl_usd=-entry_price * (sl_val / 100.0),
                    ))
                    in_pos = False
                elif price_change_pct >= (tp_val / 100.0):
                    trades.append(EvaluatedTrade(
                        entry_bar_index=entry_idx,
                        entry_time_ms=entry_time_ms,
                        entry_price=entry_price,
                        direction=instruction.direction,
                        exit_bar_index=i,
                        exit_time_ms=cur_time,
                        exit_price=cur_close,
                        exit_reason="TAKE_PROFIT",
                        pnl_r=tp_val / sl_val,
                        pnl_usd=entry_price * (tp_val / 100.0),
                    ))
                    in_pos = False

        # Hash determinista de la ejecución
        trade_data = [t.__dict__ for t in trades]
        exec_payload = {
            "strategy_hash": instruction.strategy_hash,
            "dataset_sha256": dataset_sha256,
            "trade_count": len(trades),
            "trades": trade_data,
        }
        exec_hash = hashlib.sha256(json.dumps(exec_payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

        return RuntimeExecutionResult(
            strategy_id=instruction.strategy_id,
            strategy_version=instruction.strategy_version,
            strategy_hash=instruction.strategy_hash,
            engine_version=instruction.engine_version,
            policy_version=instruction.policy_version,
            dataset_id=dataset_id,
            dataset_sha256=dataset_sha256,
            total_trades=len(trades),
            trades=trades,
            execution_hash=exec_hash,
        )


canonical_runtime_adapter = CanonicalRuntimeAdapter()
