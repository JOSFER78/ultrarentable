"""services/execution/canonical_runtime_adapter.py
Adaptador y Motor de Ejecuci?n en Runtime para CanonicalStrategy (Fase 02 Rework AG2-P02-006).
ZERO-MOCKS ? REAL-ONLY ? DETERMINISTIC ? NO-LOOKAHEAD ? PROVENANCE-LOCKED ? FAIL-CLOSED ? ZERO-OPTIMISM
Cierra el contrato universal de ejecuci?n: LONG/SHORT/BOTH, SL/TP reales, sizing con microestructura, sesiones y conflicto intrabarra.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from contracts.canonical_strategy import (
    CanonicalStrategy,
    ComparisonOp,
    ExecutableRuntimeInstruction,
    IndicatorSpec,
    InvalidStrategyError,
    LogicalOp,
    SessionWindow,
    SizingAndRisk,
    SizingType,
    StopLossType,
    StrategyIntegrityError,
    TakeProfitType,
)
from services.data.dataset_registry import DatasetRegistry, MissingDatasetError, dataset_registry
from services.data.instrument_cost_registry import (
    CANONICAL_COST_REGISTRY,
    MissingCostModelError,
    get_instrument_cost_profile,
)
from services.engine_version import CURRENT_ENGINE_VERSION, CURRENT_POLICY_VERSION


@dataclass(frozen=True)
class EvaluatedTrade:
    entry_bar_index: int
    entry_time_ms: int
    entry_price: float
    direction: str
    size_contracts: float
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
    """Ejecutor determinista universal de CanonicalStrategy (Fase 02 - AG2-P02-006)."""

    def __init__(self, engine_version: str, policy_version: str):
        if not engine_version or not policy_version:
            raise ValueError("Runtime identity versions (engine_version, policy_version) are strictly required.")
        self.engine_version = engine_version
        self.policy_version = policy_version

    def compile_strategy(self, strategy: CanonicalStrategy) -> ExecutableRuntimeInstruction:
        """Punto de entrada can?nico: valida integridad y compila la estrategia."""
        if not strategy.verify_integrity():
            raise StrategyIntegrityError(
                f"Estrategia '{strategy.strategy_id}' tiene hash corrupto o no coincide con su AST sem?ntico."
            )
        return strategy.compile_to_runtime()

    def _eval_indicator(self, spec: IndicatorSpec, bars: List[Dict[str, Any]], current_idx: int) -> float:
        """Calcula el valor del indicador en el ?ndice actual con Fail-Closed (cero fallbacks a close)."""
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

        # Par?metros estrictos sin defaults
        if "period" not in spec.params:
            raise InvalidStrategyError(f"Indicador '{spec.name}' carece del par?metro obligatorio 'period'.")

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
            if eval_idx < period:
                return float("nan")
            tr_list = []
            for i in range(1, eval_idx + 1):
                h = float(bars[i]["high"])
                l = float(bars[i]["low"])
                prev_c = float(bars[i - 1]["close"])
                tr = max(h - l, abs(h - prev_c), abs(l - prev_c))
                tr_list.append(tr)
            if len(tr_list) < period:
                return float("nan")
            return sum(tr_list[-period:]) / period

        raise InvalidStrategyError(f"Indicador '{spec.name}' no est? implementado en el motor de runtime.")

    def _eval_condition(self, cond: Dict[str, Any], bars: List[Dict[str, Any]], current_idx: int) -> bool:
        """Eval?a un nodo at?mico de condici?n."""
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

        raise InvalidStrategyError(f"Operador de comparaci?n '{op}' no soportado.")

    def _invert_operator(self, op: str) -> str:
        """Inversi?n determinista de operadores de comparaci?n para sem?ntica bidireccional."""
        op_str = str(op).upper()
        if op_str in [ComparisonOp.GT.value, ">"]:
            return ComparisonOp.LT.value
        elif op_str in [ComparisonOp.LT.value, "<"]:
            return ComparisonOp.GT.value
        elif op_str in [ComparisonOp.GTE.value, ">="]:
            return ComparisonOp.LTE.value
        elif op_str in [ComparisonOp.LTE.value, "<="]:
            return ComparisonOp.GTE.value
        elif op_str in [ComparisonOp.CROSS_ABOVE.value, "CROSS_ABOVE"]:
            return ComparisonOp.CROSS_BELOW.value
        elif op_str in [ComparisonOp.CROSS_BELOW.value, "CROSS_BELOW"]:
            return ComparisonOp.CROSS_ABOVE.value
        elif op_str in [ComparisonOp.EQ.value, "=="]:
            return ComparisonOp.EQ.value
        raise InvalidStrategyError(f"Operador de comparaci?n '{op}' no soportado para inversi?n sem?ntica.")

    def _invert_condition(self, cond: Dict[str, Any]) -> Dict[str, Any]:
        """Invierte una condici?n para evaluar el sentido opuesto del mercado."""
        return {
            "left": cond["left"],
            "op": self._invert_operator(cond["op"]),
            "right": cond["right"],
        }

    def _evaluate_conditions_list(
        self,
        conditions: List[Dict[str, Any]],
        logical_operator: LogicalOp,
        bars: List[Dict[str, Any]],
        current_idx: int,
    ) -> bool:
        """Eval?a una lista de condiciones bajo el operador l?gico especificado."""
        if not conditions:
            return False

        results = [self._eval_condition(cond, bars, current_idx) for cond in conditions]

        if logical_operator == LogicalOp.AND:
            return all(results)
        elif logical_operator == LogicalOp.OR:
            return any(results)

        raise InvalidStrategyError(f"Operador l?gico '{logical_operator}' no soportado.")

    def evaluate_entry_trigger(self, instruction: ExecutableRuntimeInstruction, bars: List[Dict[str, Any]], current_idx: int) -> bool:
        """Eval?a el disparador de entrada respetando expl?citamente el operador l?gico AND / OR."""
        return self._evaluate_conditions_list(
            instruction.compiled_conditions,
            instruction.logical_operator,
            bars,
            current_idx,
        )

    def _is_within_session(self, timestamp_ms: int, session_config: Optional[Dict[str, Any]]) -> bool:
        """Comprueba si un timestamp UTC cae dentro de la ventana de sesi?n y d?as permitidos sin defaults."""
        if not session_config:
            return True

        if "allowed_days" not in session_config or not session_config["allowed_days"]:
            raise InvalidStrategyError("allowed_days es obligatorio en la configuraci?n de sesi?n.")

        dt = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
        weekday = dt.weekday()  # 0=Monday, 6=Sunday
        allowed_days = session_config["allowed_days"]
        if weekday not in allowed_days:
            return False

        start_h, start_m = map(int, session_config["start_time_utc"].split(":"))
        end_h, end_m = map(int, session_config["end_time_utc"].split(":"))

        cur_minutes = dt.hour * 60 + dt.minute
        start_minutes = start_h * 60 + start_m
        end_minutes = end_h * 60 + end_m

        if start_minutes <= end_minutes:
            return start_minutes <= cur_minutes <= end_minutes
        else:
            return cur_minutes >= start_minutes or cur_minutes <= end_minutes

    def execute_backtest(
        self,
        strategy: CanonicalStrategy,
        account_equity_usd: float,
        registry: Optional[DatasetRegistry] = None,
    ) -> RuntimeExecutionResult:
        """Ejecuta el backtest conectando la CanonicalStrategy con la cadena de custodia can?nica de DatasetRegistry.
        
        account_equity_usd es estrictamente obligatorio sin defaults silenciosos (> 0).
        """
        # Validaci?n Fail-Closed de Capital Obligatorio (P02-006 REQ-1)
        if (
            account_equity_usd is None
            or not isinstance(account_equity_usd, (int, float))
            or math.isnan(account_equity_usd)
            or account_equity_usd <= 0
        ):
            raise InvalidStrategyError(
                f"account_equity_usd es un par?metro obligatorio y debe ser un valor num?rico estrictamente positivo (> 0). "
                f"Recibido: {account_equity_usd}."
            )

        instruction = self.compile_strategy(strategy)

        # Integraci?n obligatoria de Microestructura y Costes Can?nicos (P02-006 REQ-3)
        cost_profile = get_instrument_cost_profile(strategy.symbol)

        # Validaci?n Fail-Closed de Capacidad Single-Position (P02-006 REQ-4)
        max_open = instruction.sizing_config.get("max_open_positions")
        if max_open != 1:
            raise InvalidStrategyError(
                f"El motor de ejecuci?n actual opera exclusivamente en modo single-position (max_open_positions=1). "
                f"Recibido: max_open_positions={max_open}."
            )

        reg = registry or dataset_registry

        # Resoluci?n estricta de dataset desde la cadena de custodia
        manifest = reg.resolve_dataset(strategy.symbol, strategy.timeframe)
        if not manifest:
            raise MissingDatasetError(
                f"Dataset f?sico para s?mbolo '{strategy.symbol}' y timeframe '{strategy.timeframe}' no encontrado en DatasetRegistry."
            )

        # Carga con compuerta de elegibilidad criptogr?fica
        bars = reg.load_dataset_bars(manifest.data_snapshot_id, verify_sha256=True, require_verified_provenance=True)

        direction = instruction.direction.upper()
        if direction not in ["LONG", "SHORT", "BOTH"]:
            raise InvalidStrategyError(f"Direcci?n operativa '{direction}' no soportada.")

        # Preparaci?n de condiciones para sem?ntica bidireccional verdadera (P02-006 REQ-2)
        long_conditions: List[Dict[str, Any]] = []
        short_conditions: List[Dict[str, Any]] = []

        if direction == "BOTH":
            for cond in instruction.compiled_conditions:
                op_str = str(cond["op"]).upper()
                is_bearish = op_str in [
                    ComparisonOp.LT.value,
                    "<",
                    ComparisonOp.LTE.value,
                    "<=",
                    ComparisonOp.CROSS_BELOW.value,
                    "CROSS_BELOW",
                ]
                if is_bearish:
                    long_conditions.append(self._invert_condition(cond))
                    short_conditions.append(cond)
                else:
                    long_conditions.append(cond)
                    short_conditions.append(self._invert_condition(cond))

        trades: List[EvaluatedTrade] = []
        in_pos = False
        pos_dir = ""
        entry_idx = 0
        entry_price = 0.0
        entry_time_ms = 0
        size_contracts = 1.0
        sl_distance = 0.0
        tp_distance = 0.0

        sl_type = instruction.sl_config["type"]
        sl_val = instruction.sl_config["value"]
        tp_type = instruction.tp_config["type"]
        tp_val = instruction.tp_config["value"]
        trail_after_r = instruction.sl_config.get("trail_after_r")
        time_stop_bars = instruction.sl_config.get("time_stop_bars")
        session_config = instruction.session_config

        # Sizing y Riesgo
        sizing_type = instruction.sizing_config["type"]
        risk_val = instruction.sizing_config["value"]

        for i in range(len(bars)):
            bar = bars[i]
            cur_close = float(bar["close"])
            cur_high = float(bar["high"])
            cur_low = float(bar["low"])
            cur_open = float(bar["open"])

            # Timestamp estricto sin fallbacks a 0 (FB-02)
            cur_time = bar.get("timestamp_utc_ms") or bar.get("time")
            if cur_time is None or int(cur_time) <= 0:
                raise InvalidStrategyError(f"Marca temporal f?sica ausente o inv?lida en la barra {i}.")
            cur_time = int(cur_time)

            if not in_pos:
                # Comprobar filtro de sesi?n
                if not self._is_within_session(cur_time, session_config):
                    continue

                trigger_entered = False
                candidate_dir = ""

                if direction == "LONG":
                    if self.evaluate_entry_trigger(instruction, bars, i):
                        trigger_entered = True
                        candidate_dir = "LONG"
                elif direction == "SHORT":
                    if self.evaluate_entry_trigger(instruction, bars, i):
                        trigger_entered = True
                        candidate_dir = "SHORT"
                elif direction == "BOTH":
                    long_sig = self._evaluate_conditions_list(long_conditions, instruction.logical_operator, bars, i)
                    short_sig = self._evaluate_conditions_list(short_conditions, instruction.logical_operator, bars, i)
                    if long_sig and not short_sig:
                        trigger_entered = True
                        candidate_dir = "LONG"
                    elif short_sig and not long_sig:
                        trigger_entered = True
                        candidate_dir = "SHORT"
                    elif long_sig and short_sig:
                        # Conflicto simult?neo en la misma barra: omitir entrada por indeterminaci?n
                        trigger_entered = False

                if trigger_entered:
                    in_pos = True
                    pos_dir = candidate_dir
                    entry_idx = i
                    entry_price = cur_close
                    entry_time_ms = cur_time

                    # C?lculo de distancia de SL (P02-005 STEP 2 & 3)
                    if sl_type == StopLossType.PERCENTAGE.value:
                        sl_distance = entry_price * (sl_val / 100.0)
                    elif sl_type in [StopLossType.FIXED_POINTS.value, "FIXED_POINTS"]:
                        sl_distance = sl_val
                    elif sl_type in [StopLossType.ATR_MULTIPLE.value, "ATR_MULTIPLE"]:
                        atr = self._eval_indicator(IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0), bars, i)
                        if math.isnan(atr) or atr <= 0:
                            raise InvalidStrategyError("INSUFFICIENT_BARS_FOR_ATR: ATR requiere al menos 14 barras previas para evaluaci?n.")
                        sl_distance = atr * sl_val
                    else:
                        raise InvalidStrategyError(f"Tipo de Stop Loss '{sl_type}' no soportado.")

                    if sl_distance <= 0:
                        raise InvalidStrategyError(f"Distancia de Stop Loss calculada debe ser > 0 (recibido: {sl_distance}).")

                    # C?lculo de distancia de TP (P02-005 STEP 2 & 3)
                    if tp_type == TakeProfitType.RR_MULTIPLE.value:
                        tp_distance = sl_distance * tp_val
                    elif tp_type == TakeProfitType.PERCENTAGE.value:
                        tp_distance = entry_price * (tp_val / 100.0)
                    elif tp_type in [TakeProfitType.FIXED_POINTS.value, "FIXED_POINTS"]:
                        tp_distance = tp_val
                    elif tp_type in [TakeProfitType.ATR_MULTIPLE.value, "ATR_MULTIPLE"]:
                        atr = self._eval_indicator(IndicatorSpec(name="ATR", params={"period": 14}, source_field="close", shift=0), bars, i)
                        if math.isnan(atr) or atr <= 0:
                            raise InvalidStrategyError("INSUFFICIENT_BARS_FOR_ATR: ATR requiere al menos 14 barras previas para evaluaci?n.")
                        tp_distance = atr * tp_val
                    else:
                        raise InvalidStrategyError(f"Tipo de Take Profit '{tp_type}' no soportado.")

                    if tp_distance <= 0:
                        raise InvalidStrategyError(f"Distancia de Take Profit calculada debe ser > 0 (recibido: {tp_distance}).")

                    # Sizing cuantitativo estricto integrado con microestructura y costes (P02-006 REQ-3)
                    contract_point_risk = sl_distance * cost_profile.point_value * cost_profile.contract_multiplier
                    if contract_point_risk <= 0:
                        raise InvalidStrategyError(f"El riesgo por contrato calculado debe ser > 0 (recibido: {contract_point_risk}).")

                    if sizing_type == SizingType.FIXED_CONTRACTS.value:
                        size_contracts = risk_val
                    elif sizing_type == SizingType.RISK_PCT_EQUITY.value:
                        risk_usd = account_equity_usd * (risk_val / 100.0)
                        size_contracts = risk_usd / contract_point_risk
                    elif sizing_type == SizingType.FIXED_USD.value:
                        size_contracts = risk_val / contract_point_risk
                    else:
                        raise InvalidStrategyError(f"Tipo de Sizing '{sizing_type}' no soportado.")

                    if size_contracts <= 0 or math.isnan(size_contracts):
                        raise InvalidStrategyError(f"El tama?o de posici?n calculado en contratos debe ser > 0 (recibido: {size_contracts}).")

            else:
                bars_held = i - entry_idx

                # Evaluaci?n de salidas seg?n direcci?n (LONG vs SHORT)
                if pos_dir == "LONG":
                    # Trailing Stop / Breakeven
                    if trail_after_r is not None and (cur_high - entry_price) >= (sl_distance * trail_after_r):
                        sl_target = entry_price
                    else:
                        sl_target = entry_price - sl_distance

                    tp_target = entry_price + tp_distance

                    # Pol?tica de conflicto intrabarra: si ambos niveles son tocados en la misma vela, prioridad a SL (pesimista institucional)
                    hit_sl = cur_low <= sl_target
                    hit_tp = cur_high >= tp_target

                    if hit_sl:
                        exit_p = sl_target
                        pnl_usd = (exit_p - entry_price) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (exit_p - entry_price) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="LONG",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="STOP_LOSS",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False
                    elif hit_tp:
                        exit_p = tp_target
                        pnl_usd = (exit_p - entry_price) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (exit_p - entry_price) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="LONG",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="TAKE_PROFIT",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False
                    elif time_stop_bars is not None and bars_held >= time_stop_bars:
                        exit_p = cur_close
                        pnl_usd = (exit_p - entry_price) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (exit_p - entry_price) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="LONG",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="TIME_STOP",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False
                    elif session_config and session_config.get("close_at_eod", False) and not self._is_within_session(cur_time, session_config):
                        exit_p = cur_close
                        pnl_usd = (exit_p - entry_price) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (exit_p - entry_price) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="LONG",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="SESSION_EOD",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False

                elif pos_dir == "SHORT":
                    # Trailing Stop / Breakeven para SHORT
                    if trail_after_r is not None and (entry_price - cur_low) >= (sl_distance * trail_after_r):
                        sl_target = entry_price
                    else:
                        sl_target = entry_price + sl_distance

                    tp_target = entry_price - tp_distance

                    # Intrabar conflict para SHORT: prioridad a SL si ambos niveles se tocan
                    hit_sl = cur_high >= sl_target
                    hit_tp = cur_low <= tp_target

                    if hit_sl:
                        exit_p = sl_target
                        pnl_usd = (entry_price - exit_p) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (entry_price - exit_p) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="SHORT",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="STOP_LOSS",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False
                    elif hit_tp:
                        exit_p = tp_target
                        pnl_usd = (entry_price - exit_p) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (entry_price - exit_p) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="SHORT",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="TAKE_PROFIT",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False
                    elif time_stop_bars is not None and bars_held >= time_stop_bars:
                        exit_p = cur_close
                        pnl_usd = (entry_price - exit_p) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (entry_price - exit_p) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="SHORT",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="TIME_STOP",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False
                    elif session_config and session_config.get("close_at_eod", False) and not self._is_within_session(cur_time, session_config):
                        exit_p = cur_close
                        pnl_usd = (entry_price - exit_p) * cost_profile.point_value * cost_profile.contract_multiplier * size_contracts
                        pnl_r = (entry_price - exit_p) / sl_distance
                        trades.append(
                            EvaluatedTrade(
                                entry_bar_index=entry_idx,
                                entry_time_ms=entry_time_ms,
                                entry_price=entry_price,
                                direction="SHORT",
                                size_contracts=size_contracts,
                                exit_bar_index=i,
                                exit_time_ms=cur_time,
                                exit_price=exit_p,
                                exit_reason="SESSION_EOD",
                                pnl_r=pnl_r,
                                pnl_usd=pnl_usd,
                            )
                        )
                        in_pos = False

        # Hash determinista SHA-256 de la ejecuci?n (ligado a microestructura, capital y linaje)
        trade_data = [t.__dict__ for t in trades]
        exec_payload = {
            "strategy_hash": instruction.strategy_hash,
            "dataset_sha256": manifest.data_sha256,
            "engine_version": self.engine_version,
            "policy_version": self.policy_version,
            "account_equity_usd": account_equity_usd,
            "cost_profile_symbol": cost_profile.symbol,
            "trade_count": len(trades),
            "trades": trade_data,
        }
        exec_hash = hashlib.sha256(
            json.dumps(exec_payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        ).hexdigest()

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

