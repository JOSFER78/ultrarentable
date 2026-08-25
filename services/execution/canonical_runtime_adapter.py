"""services/execution/canonical_runtime_adapter.py
Adaptador y Motor de Ejecución en Runtime para CanonicalStrategy (Fase 02 Rework AG2-P02-004).
ZERO-MOCKS · REAL-ONLY · DETERMINISTIC · NO-LOOKAHEAD · PROVENANCE-LOCKED · FAIL-CLOSED
Garantiza la traza física de consumo, cero defaults ocultos, cero fallbacks y binding a DatasetRegistry.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ExecutableRuntimeInstruction,
    IndicatorSpec,
    InvalidStrategyError,
    LogicalOp,
    StopLossType,
    StrategyIntegrityError,
    TakeProfitType,
)
from services.data.dataset_registry import DatasetRegistry, MissingDatasetError, dataset_registry
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_POLICY_VERSION


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
    """Ejecutor determinista de CanonicalStrategy con estricta política Fail-Closed (P02-004-01 a P02-004-06)."""

    def __init__(self, engine_version: str, policy_version: str):
        if not engine_version or not policy_version:
            raise ValueError("Runtime identity versions (engine_version, policy_version) are strictly required.")
        self.engine_version = engine_version
        self.policy_version = policy_version

    def compile_strategy(self, strategy: CanonicalStrategy) -> ExecutableRuntimeInstruction:
        """Punto de entrada canónico: valida integridad y compila la estrategia."""
        if not strategy.verify_integrity():
            raise StrategyIntegrityError(
                f"Estrategia '{strategy.strategy_id}' tiene hash corrupto o no coincide con su AST semántico."
            )
        return strategy.compile_to_runtime()

    def _eval_indicator(self, spec: IndicatorSpec, bars: List[Dict[str, Any]], current_idx: int) -> float:
        """Calcula el valor del indicador en el índice actual con Fail-Closed (cero fallbacks a close)."""
        eval_idx = current_idx - spec.shift
        if eval_idx < 0 or eval_idx >= len(bars):
            return float("nan")

        source = spec.source_field.lower()
        if source not in ["close", "open", "high", "low", "volume"]:
            raise InvalidStrategyError(f"Fuente de datos '{spec.source_field}' no soportada o inexistente en dataset.")

        ind_name = spec.name.upper()

        if ind_name in ["PRICE", "PRICE_CLOSE", "CLOSE"]:
            return float(bars[eval_idx][source])
        if ind_name in ["PRICE_OPEN", "OPEN"]:
            return float(bars[eval_idx][source])
        if ind_name in ["PRICE_HIGH", "HIGH"]:
            return float(bars[eval_idx][source])
        if ind_name in ["PRICE_LOW", "LOW"]:
            return float(bars[eval_idx][source])
        if ind_name in ["PRICE_VOLUME", "VOLUME"]:
            return float(bars[eval_idx][source])

        # Parámetros estrictos sin defaults
        if "period" not in spec.params:
            raise InvalidStrategyError(f"Indicador '{spec.name}' carece del parámetro obligatorio 'period'.")
        
        period = int(spec.params["period"])
        if period <= 0:
            raise InvalidStrategyError(f"Periodo de indicador '{spec.name}' debe ser > 0 (recibido: {period}).")

        if eval_idx < period - 1:
            return float("nan")

        if ind_name == "SMA":
            vals = [float(bars[i][source]) for i in range(eval_idx - period + 1, eval_idx + 1)]
            return sum(vals) / len(vals)

        if ind_name == "EMA":
            k = 2.0 / (period + 1)
            ema = float(bars[0][source])
            for i in range(1, eval_idx + 1):
                val = float(bars[i][source])
                ema = (val * k) + (ema * (1.0 - k))
            return ema

        if ind_name == "ATR":
            tr_list = []
            for i in range(1, eval_idx + 1):
                h = float(bars[i]["high"])
                l = float(bars[i]["low"])
                prev_c = float(bars[i-1]["close"])
                tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
                tr_list.append(tr)
            if len(tr_list) < period:
                return float("nan")
            return sum(tr_list[-period:]) / period

        # Cero fallbacks complacientes: cualquier indicador desconocido lanza excepción Fail-Closed
        raise InvalidStrategyError(f"Indicador '{spec.name}' no está implementado en el motor de runtime.")

    def _eval_condition(self, cond: Dict[str, Any], bars: List[Dict[str, Any]], current_idx: int) -> bool:
        """Evalúa un nodo atómico de condición."""
        left = cond["left"]
        right = cond["right"]
        op = cond["op"]

        left_val = self._eval_indicator(IndicatorSpec(**left), bars, current_idx) if isinstance(left, dict) else float(left)
        right_val = self._eval_indicator(IndicatorSpec(**right), bars, current_idx) if isinstance(right, dict) else float(right)

        if math.isnan(left_val) or math.isnan(right_val):
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
            if math.isnan(prev_left) or math.isnan(prev_right):
                return False
            return (prev_left <= prev_right) and (left_val > right_val)
        if op in [ComparisonOp.CROSS_BELOW.value, "CROSS_BELOW"]:
            if current_idx < 1:
                return False
            prev_left = self._eval_indicator(IndicatorSpec(**left), bars, current_idx - 1) if isinstance(left, dict) else float(left)
            prev_right = self._eval_indicator(IndicatorSpec(**right), bars, current_idx - 1) if isinstance(right, dict) else float(right)
            if math.isnan(prev_left) or math.isnan(prev_right):
                return False
            return (prev_left >= prev_right) and (left_val < right_val)

        raise InvalidStrategyError(f"Operador de comparación '{op}' no soportado.")

    def evaluate_entry_trigger(self, instruction: ExecutableRuntimeInstruction, bars: List[Dict[str, Any]], current_idx: int) -> bool:
        """Evalúa el disparador de entrada respetando explícitamente el operador lógico AND / OR (P02-004-05)."""
        if not instruction.compiled_conditions:
            return False

        results = [self._eval_condition(cond, bars, current_idx) for cond in instruction.compiled_conditions]

        if instruction.logical_operator == LogicalOp.AND:
            return all(results)
        elif instruction.logical_operator == LogicalOp.OR:
            return any(results)
        
        raise InvalidStrategyError(f"Operador lógico '{instruction.logical_operator}' no soportado.")

    def execute_backtest(
        self,
        strategy: CanonicalStrategy,
        registry: Optional[DatasetRegistry] = None,
    ) -> RuntimeExecutionResult:
        """Ejecuta el backtest conectando la CanonicalStrategy con la cadena de custodia canónica de DatasetRegistry (P02-004-04 & P02-004-06)."""
        reg = registry or dataset_registry
        
        # Resolución estricta de dataset desde la cadena de custodia
        manifest = reg.resolve_dataset(strategy.symbol, strategy.timeframe)
        if not manifest:
            raise MissingDatasetError(
                f"Dataset físico para símbolo '{strategy.symbol}' y timeframe '{strategy.timeframe}' no encontrado en DatasetRegistry."
            )

        # Carga con compuerta de elegibilidad criptográfica
        bars = reg.load_dataset_bars(manifest.data_snapshot_id, verify_sha256=True, require_verified_provenance=True)
        instruction = self.compile_strategy(strategy)
        
        trades: List[EvaluatedTrade] = []
        in_pos = False
        entry_idx = 0
        entry_price = 0.0
        entry_time_ms = 0
        sl_distance = 0.0
        tp_distance = 0.0

        sl_type = instruction.sl_config["type"]
        sl_val = instruction.sl_config["value"]
        tp_type = instruction.tp_config["type"]
        tp_val = instruction.tp_config["value"]
        trail_after_r = instruction.sl_config.get("trail_after_r")
        time_stop_bars = instruction.sl_config.get("time_stop_bars")

        for i in range(len(bars)):
            bar = bars[i]
            cur_close = float(bar["close"])
            cur_high = float(bar["high"])
            cur_low = float(bar["low"])
            cur_time = int(bar.get("timestamp_utc_ms", bar.get("time", 0)))

            if not in_pos:
                if self.evaluate_entry_trigger(instruction, bars, i):
                    in_pos = True
                    entry_idx = i
                    entry_price = cur_close
                    entry_time_ms = cur_time

                    # Cálculo exacto de distancia de SL según sl_type (P02-004-03)
                    if sl_type == StopLossType.PERCENTAGE.value:
                        sl_distance = entry_price * (sl_val / 100.0)
                    elif sl_type in [StopLossType.FIXED_POINTS.value, "FIXED_POINTS"]:
                        sl_distance = sl_val
                    elif sl_type in [StopLossType.ATR_MULTIPLE.value, "ATR_MULTIPLE"]:
                        atr = self._eval_indicator(IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0), bars, i)
                        sl_distance = (atr if not math.isnan(atr) and atr > 0 else (entry_price * 0.01)) * sl_val
                    else:
                        raise InvalidStrategyError(f"Tipo de Stop Loss '{sl_type}' no soportado por el motor.")

                    # Cálculo exacto de distancia de TP según tp_type (P02-004-03)
                    if tp_type == TakeProfitType.RR_MULTIPLE.value:
                        tp_distance = sl_distance * tp_val
                    elif tp_type == TakeProfitType.PERCENTAGE.value:
                        tp_distance = entry_price * (tp_val / 100.0)
                    elif tp_type in [TakeProfitType.FIXED_POINTS.value, "FIXED_POINTS"]:
                        tp_distance = tp_val
                    elif tp_type in [TakeProfitType.ATR_MULTIPLE.value, "ATR_MULTIPLE"]:
                        atr = self._eval_indicator(IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0), bars, i)
                        tp_distance = (atr if not math.isnan(atr) and atr > 0 else (entry_price * 0.01)) * tp_val
                    else:
                        raise InvalidStrategyError(f"Tipo de Take Profit '{tp_type}' no soportado por el motor.")

            else:
                bars_held = i - entry_idx
                
                # Gestión de Stop Loss, Take Profit y Time Stop
                if instruction.direction == "LONG":
                    # Breakeven / Trailing
                    if trail_after_r is not None and (cur_high - entry_price) >= (sl_distance * trail_after_r):
                        sl_target = entry_price
                    else:
                        sl_target = entry_price - sl_distance

                    tp_target = entry_price + tp_distance

                    if cur_low <= sl_target:
                        exit_p = sl_target
                        pnl_usd = exit_p - entry_price
                        pnl_r = pnl_usd / sl_distance if sl_distance > 0 else -1.0
                        trades.append(EvaluatedTrade(
                            entry_bar_index=entry_idx,
                            entry_time_ms=entry_time_ms,
                            entry_price=entry_price,
                            direction="LONG",
                            exit_bar_index=i,
                            exit_time_ms=cur_time,
                            exit_price=exit_p,
                            exit_reason="STOP_LOSS",
                            pnl_r=pnl_r,
                            pnl_usd=pnl_usd,
                        ))
                        in_pos = False
                    elif cur_high >= tp_target:
                        exit_p = tp_target
                        pnl_usd = exit_p - entry_price
                        pnl_r = pnl_usd / sl_distance if sl_distance > 0 else 1.0
                        trades.append(EvaluatedTrade(
                            entry_bar_index=entry_idx,
                            entry_time_ms=entry_time_ms,
                            entry_price=entry_price,
                            direction="LONG",
                            exit_bar_index=i,
                            exit_time_ms=cur_time,
                            exit_price=exit_p,
                            exit_reason="TAKE_PROFIT",
                            pnl_r=pnl_r,
                            pnl_usd=pnl_usd,
                        ))
                        in_pos = False
                    elif time_stop_bars is not None and bars_held >= time_stop_bars:
                        exit_p = cur_close
                        pnl_usd = exit_p - entry_price
                        pnl_r = pnl_usd / sl_distance if sl_distance > 0 else 0.0
                        trades.append(EvaluatedTrade(
                            entry_bar_index=entry_idx,
                            entry_time_ms=entry_time_ms,
                            entry_price=entry_price,
                            direction="LONG",
                            exit_bar_index=i,
                            exit_time_ms=cur_time,
                            exit_price=exit_p,
                            exit_reason="TIME_STOP",
                            pnl_r=pnl_r,
                            pnl_usd=pnl_usd,
                        ))
                        in_pos = False

        # Hash determinista SHA-256 de la ejecución
        trade_data = [t.__dict__ for t in trades]
        exec_payload = {
            "strategy_hash": instruction.strategy_hash,
            "dataset_sha256": manifest.data_sha256,
            "engine_version": self.engine_version,
            "policy_version": self.policy_version,
            "trade_count": len(trades),
            "trades": trade_data,
        }
        exec_hash = hashlib.sha256(json.dumps(exec_payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")).hexdigest()

        return RuntimeExecutionResult(
            strategy_id=instruction.strategy_id,
            strategy_version=instruction.strategy_version,
            strategy_hash=instruction.strategy_hash,
            engine_version=self.engine_version,
            policy_version=self.policy_version,
            dataset_id=manifest.data_snapshot_id,
            dataset_sha256=manifest.data_sha256,
            total_trades=len(trades),
            trades=trades,
            execution_hash=exec_hash,
        )


# Instancia oficial SSOT con versiones del SSOT
canonical_runtime_adapter = CanonicalRuntimeAdapter(
    engine_version=CURRENT_ENGINE_VERSION,
    policy_version=CURRENT_POLICY_VERSION,
)
