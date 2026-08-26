"""services/engine/rule_evaluator.py
Dynamic Rule & Condition Evaluator (v3.0.0).

DOCTRINA ZERO-HARDCODED STRATEGIES:
- Evaluates arbitrary AST rules and condition trees dynamically on each bar.
- Evaluates cross-overs, thresholds, multi-indicator relationships and logical operators.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import numpy as np

from contracts.canonical_strategy import ComparisonOperator
from contracts.universal_strategy import (
    ConditionNode,
    DynamicEntryRules,
    DynamicValueNode,
    IndicatorType,
    LogicalOperator,
    RuleGroup,
    ValueSource,
)
from services.engine.indicator_engine import DynamicIndicatorEngine


class DynamicRuleEvaluator:
    """Evaluador dinámico de condiciones y árboles de reglas sobre series temporales."""

    def __init__(self, indicator_engine: DynamicIndicatorEngine) -> None:
        self.engine = indicator_engine
        self._series_cache: Dict[str, np.ndarray] = {}

    def resolve_value_series(self, node: DynamicValueNode) -> np.ndarray:
        """Resuelve el vector completo de valores para un nodo dado."""
        if node.source_type == ValueSource.CONSTANT:
            return np.full(self.engine.n, node.constant_value or 0.0, dtype=np.float64)

        cache_key = f"{node.source_type}_{node.indicator_type}_{node.period}_{node.parameters}_{node.offset_bars}"
        if cache_key in self._series_cache:
            return self._series_cache[cache_key]

        if node.source_type == ValueSource.INDICATOR:
            if node.indicator_type is None:
                raise ValueError(f"INVALID_VALUE_NODE: Node of source '{node.source_type}' requires an explicit indicator_type (received None)")
            raw = self.engine.get_series(node.indicator_type, node.period, node.parameters)
        elif node.source_type == ValueSource.SERIES:
            target_ind = node.indicator_type or IndicatorType.PRICE_CLOSE
            raw = self.engine.get_series(target_ind, node.period, node.parameters)
        else:
            raise ValueError(f"UNSUPPORTED_VALUE_SOURCE: ValueSource '{node.source_type}' is not supported")

        if node.offset_bars > 0:
            shifted = np.empty_like(raw)
            shifted[:node.offset_bars] = raw[0]
            shifted[node.offset_bars:] = raw[:-node.offset_bars]
            res = shifted
        else:
            res = raw

        self._series_cache[cache_key] = res
        return res

    def evaluate_condition_at_bar(self, cond: ConditionNode, bar_idx: int) -> bool:
        """Evalúa una condición atómica en una barra específica."""
        left_series = self.resolve_value_series(cond.left)
        right_series = self.resolve_value_series(cond.right)

        curr_left = left_series[bar_idx]
        curr_right = right_series[bar_idx]

        op_val = cond.operator.value if hasattr(cond.operator, "value") else str(cond.operator)
        op_name = {"GREATER_THAN": "GT", "GREATER_EQUAL": "GTE", "LESS_THAN": "LT",
                   "LESS_EQUAL": "LTE", "EQUALS": "EQ", "CROSSES_ABOVE": "CROSS_ABOVE",
                   "CROSSES_BELOW": "CROSS_BELOW"}.get(op_val, op_val)
        if op_name == "GT":
            return bool(curr_left > curr_right)
        elif op_name == "GTE":
            return bool(curr_left >= curr_right)
        elif op_name == "LT":
            return bool(curr_left < curr_right)
        elif op_name == "LTE":
            return bool(curr_left <= curr_right)
        elif op_name == "EQ":
            return bool(abs(curr_left - curr_right) < 1e-6)
        elif op_name == "CROSS_ABOVE":
            if bar_idx == 0:
                return False
            prev_left = left_series[bar_idx - 1]
            prev_right = right_series[bar_idx - 1]
            return bool(prev_left <= prev_right and curr_left > curr_right)
        elif op_name == "CROSS_BELOW":
            if bar_idx == 0:
                return False
            prev_left = left_series[bar_idx - 1]
            prev_right = right_series[bar_idx - 1]
            return bool(prev_left >= prev_right and curr_left < curr_right)

        return False

    def evaluate_group_at_bar(self, group: RuleGroup, bar_idx: int) -> bool:
        """Evalúa un grupo lógico de condiciones."""
        if not group.conditions:
            return False

        if group.logical_operator == LogicalOperator.ALL:
            return all(self.evaluate_condition_at_bar(c, bar_idx) for c in group.conditions)
        else:
            return any(self.evaluate_condition_at_bar(c, bar_idx) for c in group.conditions)

    def evaluate_signals_at_bar(self, rules: DynamicEntryRules, bar_idx: int) -> tuple[bool, bool]:
        """Evalúa si hay señal de entrada Long o Short en la barra actual."""
        long_signal = False
        short_signal = False

        if rules.allow_long and rules.long_rules.conditions:
            long_signal = self.evaluate_group_at_bar(rules.long_rules, bar_idx)

        if rules.allow_short and rules.short_rules.conditions:
            short_signal = self.evaluate_group_at_bar(rules.short_rules, bar_idx)

        return long_signal, short_signal
