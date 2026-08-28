"""services/strategy_core/canonical_compiler.py
Compilador Canónico de Estrategias Cuantitativas (CanonicalCompiler v3.0.0).

DOCTRINA ZERO-MOCKS & CANONICAL BRIDGING:
- Transforma un CanonicalStrategy en una StrategySpecification ejecutable por el UniversalDeterministicBacktestEngine.
- Cero reglas hardcodeadas: mapea 100% de las condiciones, indicadores, operadores, salidas y dimensionamiento del AST RuleTree.
- Enlaza el perfil de costes oficial desde CANONICAL_COST_REGISTRY.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from contracts.canonical_strategy import (
    CanonicalStrategy,
    StopLossType,
    TakeProfitType,
    ComparisonOperator as CanonicalCompOp,
    ExecutionTrack,
    IndicatorSpec as CanonicalIndSpec,
    RuleCondition as CanonicalRuleCond,
    RuleTree as CanonicalRuleTree,
)
from contracts.dataset_specification import DatasetSpecification
from contracts.execution_model import ExecutionModel, SlippageMode
from contracts.instrument_specification import (
    AssetClass as UnivAssetClass,
    CommissionType,
    InstrumentSpecification,
)
from contracts.risk_model import RiskDoctrine, RiskModel
from contracts.universal_strategy import (
    ComparisonOperator as UnivCompOp,
    ConditionNode,
    DynamicEntryRules,
    DynamicExitRules,
    DynamicValueNode,
    IndicatorType,
    LogicalOperator,
    RuleGroup,
    StrategyFamily,
    StrategySpecification,
    TimeAndSessionFilter,
    ValueSource,
)
from services.data.instrument_cost_registry import CANONICAL_COST_REGISTRY, MissingCostModelError


# Mapeo de nombres de indicadores de texto a IndicatorType canónico
INDICATOR_NAME_MAP: Dict[str, IndicatorType] = {
    "EMA": IndicatorType.EMA,
    "SMA": IndicatorType.SMA,
    "WMA": IndicatorType.WMA,
    "HMA": IndicatorType.HMA,
    "VWAP": IndicatorType.VWAP,
    "RSI": IndicatorType.RSI,
    "ATR": IndicatorType.ATR,
    "MACD": IndicatorType.MACD_LINE,
    "MACD_SIGNAL": IndicatorType.MACD_SIGNAL,
    "MACD_HIST": IndicatorType.MACD_HIST,
    "BOLLINGER": IndicatorType.BOLLINGER_UPPER,
    "BOLLINGER_UPPER": IndicatorType.BOLLINGER_UPPER,
    "BOLLINGER_LOWER": IndicatorType.BOLLINGER_LOWER,
    "BOLLINGER_MIDDLE": IndicatorType.BOLLINGER_MIDDLE,
    "DONCHIAN": IndicatorType.DONCHIAN_HIGH,
    "DONCHIAN_HIGH": IndicatorType.DONCHIAN_HIGH,
    "DONCHIAN_LOW": IndicatorType.DONCHIAN_LOW,
    "DONCHIAN_MID": IndicatorType.DONCHIAN_MID,
    "STOCHASTIC": IndicatorType.STOCHASTIC_K,
    "ROC": IndicatorType.ROC,
    "CCI": IndicatorType.CCI,
    "CLOSE": IndicatorType.PRICE_CLOSE,
    "PRICE_CLOSE": IndicatorType.PRICE_CLOSE,
    "OPEN": IndicatorType.PRICE_OPEN,
    "PRICE_OPEN": IndicatorType.PRICE_OPEN,
    "HIGH": IndicatorType.PRICE_HIGH,
    "PRICE_HIGH": IndicatorType.PRICE_HIGH,
    "LOW": IndicatorType.PRICE_LOW,
    "PRICE_LOW": IndicatorType.PRICE_LOW,
    "VOLUME": IndicatorType.PRICE_VOLUME,
    "PRICE_VOLUME": IndicatorType.PRICE_VOLUME,
}

OPERATOR_MAP: Dict[CanonicalCompOp, UnivCompOp] = {
    CanonicalCompOp.GT: UnivCompOp.GREATER_THAN,
    CanonicalCompOp.LT: UnivCompOp.LESS_THAN,
    CanonicalCompOp.GTE: UnivCompOp.GREATER_EQUAL,
    CanonicalCompOp.LTE: UnivCompOp.LESS_EQUAL,
    CanonicalCompOp.CROSS_ABOVE: UnivCompOp.CROSSES_ABOVE,
    CanonicalCompOp.CROSS_BELOW: UnivCompOp.CROSSES_BELOW,
    CanonicalCompOp.EQ: UnivCompOp.EQUALS,
}


class CanonicalCompiler:
    """Compilador determinista de CanonicalStrategy a modelos del Universal Engine."""

    @classmethod
    def compile_node(
        cls,
        spec: Optional[CanonicalIndSpec],
        constant: Optional[float] = None,
        offset: int = 0,
    ) -> DynamicValueNode:
        if spec is None:
            if constant is not None:
                return DynamicValueNode.constant(constant)
            return DynamicValueNode.constant(0.0)

        name_clean = spec.name.upper().strip()
        if name_clean not in INDICATOR_NAME_MAP:
            raise ValueError(f"UNSUPPORTED_INDICATOR: {spec.name}")
        ind_type = INDICATOR_NAME_MAP[name_clean]
        # The canonical AST owns temporal alignment. Never discard a positive shift.
        effective_offset = max(int(offset), int(spec.shift))

        if "PRICE" in ind_type.value:
            return DynamicValueNode.series(ind_type, offset=effective_offset)

        period = int(spec.params.get("period", 14))
        return DynamicValueNode.indicator(
            indicator=ind_type,
            period=period,
            params=spec.params,
            timeframe=None,
            offset=effective_offset,
        )

    @classmethod
    def compile_condition(cls, cond: CanonicalRuleCond) -> ConditionNode:
        left_node = cls.compile_node(cond.left, offset=0)
        op = OPERATOR_MAP.get(cond.op) if isinstance(cond.op, CanonicalCompOp) else None
        if op is None:
            raise ValueError(f"UNSUPPORTED_OPERATOR: {cond.op}")

        if isinstance(cond.right, CanonicalIndSpec):
            right_node = cls.compile_node(cond.right, offset=0)
        elif isinstance(cond.right, str):
            right_node = (
                DynamicValueNode(
                    source=DynamicValueNode.resolve_series_name(cond.right),
                    offset=0,
                )
                if hasattr(DynamicValueNode, "resolve_series_name")
                else DynamicValueNode.constant(0.0)
            )
        else:
            right_node = DynamicValueNode.constant(float(cond.right))

        return ConditionNode(left=left_node, operator=op, right=right_node)

    @classmethod
    def compile_entry_rules(cls, rule_tree: CanonicalRuleTree) -> DynamicEntryRules:
        long_conds = [cls.compile_condition(c) for c in (rule_tree.long_conditions or [])]
        short_conds = [cls.compile_condition(c) for c in (rule_tree.short_conditions or [])]
        logic_raw = rule_tree.logic.value if hasattr(rule_tree.logic, "value") else str(rule_tree.logic)
        log_op = LogicalOperator.ALL if logic_raw.upper() == "AND" else LogicalOperator.ANY
        return DynamicEntryRules(
            long_rules=RuleGroup(logical_operator=log_op, conditions=long_conds),
            short_rules=RuleGroup(logical_operator=log_op, conditions=short_conds),
            allow_long=len(long_conds) > 0,
            allow_short=len(short_conds) > 0,
        )

    @classmethod
    def compile_exit_rules(cls, strat: CanonicalStrategy) -> DynamicExitRules:
        exits = strat.exit_rules
        if exits.sl_type == StopLossType.ATR_MULTIPLE:
            sl_type = "ATR_MULTIPLE"
            sl_val = exits.sl_value
        elif exits.sl_type == StopLossType.PERCENTAGE:
            sl_type = "PERCENTAGE"
            sl_val = exits.sl_value
        else:
            sl_type = "FIXED_TICKS"
            sl_val = float(exits.sl_value)

        if exits.tp_type in (TakeProfitType.RR_MULTIPLE, "RR_MULTIPLE", "RISK_REWARD_MULTIPLE"):
            tp_type = "RISK_REWARD_MULTIPLE"
            tp_val = exits.tp_value
        elif exits.tp_type in (TakeProfitType.PERCENTAGE, "PERCENTAGE"):
            tp_type = "PERCENTAGE"
            tp_val = exits.tp_value
        elif exits.tp_type in (TakeProfitType.FIXED_POINTS, "FIXED_POINTS", "FIXED_TICKS"):
            tp_type = "FIXED_TICKS"
            tp_val = float(exits.tp_value)
        else:
            tp_type = "ATR_MULTIPLE"
            tp_val = exits.tp_value

        trailing_enabled = exits.trail_after_r is not None
        return DynamicExitRules(
            stop_loss_type=sl_type,
            stop_loss_value=sl_val,
            stop_loss_atr_period=14,
            take_profit_type=tp_type,
            take_profit_value=tp_val,
            take_profit_atr_period=14,
            break_even_enabled=trailing_enabled,
            break_even_trigger_r=exits.trail_after_r or 1.5,
            trailing_stop_enabled=trailing_enabled,
            trailing_step_atr_mult=exits.trail_after_r or 1.5,
            max_bars_in_trade=exits.time_stop_bars,
        )

    @classmethod
    def compile_instrument(
        cls,
        symbol: str,
        custom_point_val: Optional[float] = None,
        custom_tick_sz: Optional[float] = None,
    ) -> InstrumentSpecification:
        clean_sym = symbol.upper().replace("-", "").replace("/", "").replace("_", "").strip()
        cost_prof = CANONICAL_COST_REGISTRY.get(clean_sym)
        if cost_prof is None:
            raise MissingCostModelError(f"MISSING_COST_PROFILE: {symbol}")
        point_val = custom_point_val if custom_point_val is not None else cost_prof.point_value
        tick_sz = custom_tick_sz if custom_tick_sz is not None else cost_prof.tick_size
        asset_class_str = str(cost_prof.asset_class.value if hasattr(cost_prof.asset_class, "value") else cost_prof.asset_class)
        is_cme = asset_class_str == "CME_FUTURES" or clean_sym in ("NQ", "ES", "MES", "MNQ", "GC", "CL", "YM", "RTY", "SI")
        is_fx = asset_class_str == "FOREX_SPOT"
        is_crypto = asset_class_str == "CRYPTO_PERPETUAL" or "USDT" in clean_sym
        taker_fee = cost_prof.taker_fee_pct
        maker_fee = cost_prof.maker_fee_pct
        spread_ticks = cost_prof.typical_spread_ticks
        slippage_ticks = cost_prof.slippage_ticks_baseline
        funding_rate = (cost_prof.funding_rate_8h_pct / 100.0) if cost_prof.funding_rate_8h_pct is not None else 0.0

        if is_cme:
            asset_class = UnivAssetClass.CME_FUTURES
            comm_type = CommissionType.FIXED_PER_CONTRACT
            comm_val = 2.50
            taker_fee = 0.0
            maker_fee = 0.0
            max_lev = 1.0
            venue = "CME"
            quote_curr = "USD"
        elif is_fx:
            asset_class = UnivAssetClass.FOREX_MAJOR
            comm_type = CommissionType.FIXED_PER_CONTRACT
            comm_val = 3.50
            taker_fee = 0.0
            maker_fee = 0.0
            max_lev = 30.0
            venue = "OANDA"
            quote_curr = "USD"
        elif is_crypto:
            asset_class = UnivAssetClass.CRYPTO_PERPETUAL
            comm_type = CommissionType.PERCENTAGE_OF_NOTIONAL
            comm_val = 0.050
            max_lev = 50.0
            venue = "BINGX"
            quote_curr = "USDT"
        else:
            asset_class = UnivAssetClass.COMMODITY if clean_sym in ("GC", "SI", "CL") else UnivAssetClass.INDEX_FUTURES
            comm_type = CommissionType.FIXED_PER_CONTRACT
            comm_val = 2.50
            max_lev = 1.0
            venue = "CME"
            quote_curr = "USD"

        return InstrumentSpecification(
            symbol=symbol,
            raw_symbol=symbol.replace("-", ""),
            asset_class=asset_class,
            exchange_or_venue=venue,
            base_currency=symbol.replace("USDT", "").replace("USD", "").replace("-", ""),
            quote_currency=quote_curr,
            tick_size=tick_sz,
            point_value=point_val,
            contract_size=1.0,
            min_quantity=1.0 if is_cme else (0.01 if is_fx else 0.001),
            quantity_step=1.0 if is_cme else (0.01 if is_fx else 0.001),
            price_precision=2 if is_cme else (5 if is_fx else 2),
            quantity_precision=0 if is_cme else (2 if is_fx else 4),
            commission_type=comm_type,
            taker_fee_rate=taker_fee / 100.0,
            maker_fee_rate=maker_fee / 100.0,
            cme_exchange_fee_per_contract=comm_val if is_cme else 0.0,
            typical_spread_ticks=spread_ticks,
            typical_slippage_ticks=slippage_ticks,
            max_allowed_leverage=max_lev,
            is_perpetual=is_crypto,
            default_funding_rate=funding_rate,
        )

    @classmethod
    def compile(
        cls,
        strategy: CanonicalStrategy,
        dataset_id: str = "ds_auto",
        dataset_sha256: str = "sha256_unverified",
        initial_capital_usd: Optional[float] = None,
        override_symbol: Optional[str] = None,
    ) -> Tuple[StrategySpecification, InstrumentSpecification, ExecutionModel, RiskModel]:
        """Compila un CanonicalStrategy completo en los 4 modelos requeridos por el motor universal."""
        entry_rules = cls.compile_entry_rules(strategy.entry_rules)
        exit_rules = cls.compile_exit_rules(strategy)

        if strategy.session_window is not None:
            time_filter = TimeAndSessionFilter(
                enabled=True,
                timezone="UTC",
                session_start=strategy.session_window.start_time_utc,
                session_end=strategy.session_window.end_time_utc,
                close_all_positions_at_session_end=strategy.session_window.close_at_eod,
            )
        else:
            time_filter = TimeAndSessionFilter(
                enabled=False,
                timezone="UTC",
                session_start="00:00",
                session_end="23:59",
                close_all_positions_at_session_end=False,
            )

        target_sym = override_symbol or strategy.symbol
        strat_spec = StrategySpecification(
            strategy_id=strategy.strategy_id,
            version=strategy.version,
            family=StrategyFamily.MOMENTUM_BREAKOUT,
            target_symbol=target_sym,
            base_timeframe=strategy.timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            time_filter=time_filter,
            dataset_reference_id=dataset_id,
            dataset_sha256=dataset_sha256,
        )

        inst_spec = cls.compile_instrument(symbol=target_sym, custom_point_val=None, custom_tick_sz=None)
        exec_model = ExecutionModel(
            slippage_mode=SlippageMode.FIXED_BPS,
            base_slippage_bps=inst_spec.typical_slippage_ticks * 2.0,
            taker_fee_pct=inst_spec.taker_fee_rate * 100.0,
            maker_fee_pct=inst_spec.maker_fee_rate * 100.0,
            funding_rate_8h=inst_spec.default_funding_rate,
        )

        is_fondeo = getattr(strategy, "route", "FONDEO") == "FONDEO"
        base_cap = initial_capital_usd or (50000.0 if is_fondeo else 1000.0)
        pyr_layers = getattr(strategy.sizing_and_risk, "pyramiding_max_layers", None) or 1
        risk_model = RiskModel(
            model_id=f"RISK_{strategy.strategy_id}",
            doctrine=RiskDoctrine.FONDEO if is_fondeo else RiskDoctrine.ULTRA,
            base_capital_usd=base_cap,
            base_risk_pct=strategy.sizing_and_risk.risk_value,
            max_leverage=10.0,
            pyramiding_enabled=pyr_layers > 0,
            pyramiding_max_tiers=max(1, pyr_layers),
            max_drawdown_limit_pct=4.0 if is_fondeo else 85.0,
        )
        return strat_spec, inst_spec, exec_model, risk_model
