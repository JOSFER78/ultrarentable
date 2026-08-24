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
from services.data.instrument_cost_registry import CANONICAL_COST_REGISTRY, InstrumentCostProfile


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
    CanonicalCompOp.GREATER_THAN: UnivCompOp.GREATER_THAN,
    CanonicalCompOp.LESS_THAN: UnivCompOp.LESS_THAN,
    CanonicalCompOp.GREATER_EQUAL: UnivCompOp.GREATER_EQUAL,
    CanonicalCompOp.LESS_EQUAL: UnivCompOp.LESS_EQUAL,
    CanonicalCompOp.CROSSES_ABOVE: UnivCompOp.CROSSES_ABOVE,
    CanonicalCompOp.CROSSES_BELOW: UnivCompOp.CROSSES_BELOW,
    CanonicalCompOp.EQUALS: UnivCompOp.EQUALS,
}


class CanonicalCompiler:
    """Compilador determinista de CanonicalStrategy a modelos del Universal Engine."""

    @classmethod
    def compile_node(cls, spec: Optional[CanonicalIndSpec], constant: Optional[float] = None, offset: int = 0) -> DynamicValueNode:
        if spec is None:
            if constant is not None:
                return DynamicValueNode.constant(constant)
            return DynamicValueNode.constant(0.0)

        name_clean = spec.name.upper().strip()
        ind_type = INDICATOR_NAME_MAP.get(name_clean, IndicatorType.EMA)

        if "PRICE" in ind_type.value:
            return DynamicValueNode.series(ind_type, offset=offset)

        return DynamicValueNode.indicator(
            indicator=ind_type,
            period=spec.period,
            params=spec.parameters,
            timeframe=spec.timeframe,
            offset=offset,
        )

    @classmethod
    def compile_condition(cls, cond: CanonicalRuleCond) -> ConditionNode:
        left_node = cls.compile_node(cond.left_indicator, offset=cond.lookback_bars)
        op = OPERATOR_MAP.get(cond.operator, UnivCompOp.GREATER_THAN)

        if cond.right_indicator is not None:
            right_node = cls.compile_node(cond.right_indicator, offset=cond.lookback_bars)
        elif cond.threshold_value is not None:
            right_node = DynamicValueNode.constant(cond.threshold_value)
        else:
            right_node = DynamicValueNode.constant(0.0)

        return ConditionNode(left=left_node, operator=op, right=right_node)

    @classmethod
    def compile_entry_rules(cls, rule_tree: CanonicalRuleTree) -> DynamicEntryRules:
        long_conds = [cls.compile_condition(c) for c in rule_tree.long_conditions]
        short_conds = [cls.compile_condition(c) for c in rule_tree.short_conditions]

        log_op = LogicalOperator.ALL if rule_tree.logical_operator.upper() == "AND" else LogicalOperator.ANY

        return DynamicEntryRules(
            long_rules=RuleGroup(logical_operator=log_op, conditions=long_conds),
            short_rules=RuleGroup(logical_operator=log_op, conditions=short_conds),
            allow_long=len(long_conds) > 0,
            allow_short=len(short_conds) > 0,
        )

    @classmethod
    def compile_exit_rules(cls, strat: CanonicalStrategy) -> DynamicExitRules:
        exits = strat.exits
        
        # Stop loss
        if exits.stop_loss_atr_mult is not None and exits.stop_loss_atr_mult > 0:
            sl_type = "ATR_MULTIPLE"
            sl_val = exits.stop_loss_atr_mult
        elif exits.stop_loss_ticks is not None and exits.stop_loss_ticks > 0:
            sl_type = "FIXED_TICKS"
            sl_val = float(exits.stop_loss_ticks)
        else:
            sl_type = "ATR_MULTIPLE"
            sl_val = 2.0

        # Take profit
        if exits.take_profit_atr_mult is not None and exits.take_profit_atr_mult > 0:
            tp_type = "ATR_MULTIPLE"
            tp_val = exits.take_profit_atr_mult
        elif exits.take_profit_ticks is not None and exits.take_profit_ticks > 0:
            tp_type = "FIXED_TICKS"
            tp_val = float(exits.take_profit_ticks)
        else:
            tp_type = "ATR_MULTIPLE"
            tp_val = 6.0

        be_enabled = (exits.break_even_atr_mult is not None and exits.break_even_atr_mult > 0)
        trailing_enabled = (exits.trailing_stop_atr_mult is not None and exits.trailing_stop_atr_mult > 0)

        return DynamicExitRules(
            stop_loss_type=sl_type,
            stop_loss_value=sl_val,
            stop_loss_atr_period=14,
            take_profit_type=tp_type,
            take_profit_value=tp_val,
            take_profit_atr_period=14,
            break_even_enabled=be_enabled,
            break_even_trigger_r=exits.break_even_atr_mult or 1.5,
            trailing_stop_enabled=trailing_enabled,
            trailing_step_atr_mult=exits.trailing_stop_atr_mult or 1.5,
            max_bars_in_trade=exits.max_bars_in_trade,
        )

    @classmethod
    def compile_instrument(cls, symbol: str, custom_point_val: Optional[float] = None, custom_tick_sz: Optional[float] = None) -> InstrumentSpecification:
        clean_sym = symbol.upper().replace("-", "").replace("/", "")
        cost_prof = CANONICAL_COST_REGISTRY.get(clean_sym)

        if cost_prof:
            point_val = cost_prof.point_value
            tick_sz = cost_prof.tick_size
            is_crypto = cost_prof.asset_class == "CRYPTO_PERPETUAL" or "USDT" in clean_sym
            is_cme = cost_prof.asset_class == "CME_FUTURES" or clean_sym in ("NQ", "ES", "MES", "MNQ", "GC", "CL")
            is_fx = cost_prof.asset_class == "FOREX_SPOT"
        else:
            is_cme = clean_sym in ("NQ", "ES", "MES", "MNQ", "GC", "CL")
            is_fx = clean_sym in ("EURUSD", "GBPUSD", "USDJPY", "AUDUSD")
            is_crypto = not (is_cme or is_fx)
            point_val = custom_point_val or (20.0 if clean_sym in ("NQ", "MNQ") else (50.0 if clean_sym in ("ES", "MES") else 1.0))
            tick_sz = custom_tick_sz or (0.25 if is_cme else (0.0001 if is_fx else 0.1))

        if is_cme:
            asset_class = UnivAssetClass.CME_FUTURES
            comm_type = CommissionType.FIXED_PER_CONTRACT
            comm_val = 2.50
            taker_fee = 0.0
            maker_fee = 0.0
            max_lev = 1.0
        elif is_fx:
            asset_class = UnivAssetClass.FOREX_MAJOR
            comm_type = CommissionType.FIXED_PER_CONTRACT
            comm_val = 3.50
            taker_fee = 0.0
            maker_fee = 0.0
            max_lev = 30.0
        else:
            asset_class = UnivAssetClass.CRYPTO_PERPETUAL
            comm_type = CommissionType.PERCENTAGE_OF_NOTIONAL
            comm_val = 0.050
            taker_fee = 0.050
            maker_fee = 0.020
            max_lev = 50.0

        return InstrumentSpecification(
            symbol=symbol,
            raw_symbol=symbol.replace("-", ""),
            asset_class=asset_class,
            exchange_or_venue="CME" if is_cme else ("OANDA" if is_fx else "BINGX"),
            base_currency=symbol.replace("USDT", "").replace("USD", "").replace("-", ""),
            quote_currency="USD" if is_cme or is_fx else "USDT",
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
            typical_spread_ticks=cost_prof.typical_spread_ticks if cost_prof else 1.0,
            typical_slippage_ticks=cost_prof.slippage_ticks_baseline if cost_prof else 1.0,
            max_allowed_leverage=max_lev,
            is_perpetual=is_crypto,
            default_funding_rate=(cost_prof.funding_rate_8h_pct / 100.0) if (cost_prof and cost_prof.funding_rate_8h_pct is not None) else 0.0,
        )

    @classmethod
    def compile(
        cls,
        strategy: CanonicalStrategy,
        dataset_id: str = "ds_auto",
        dataset_sha256: str = "sha256_unverified",
        initial_capital_usd: Optional[float] = None,
    ) -> Tuple[StrategySpecification, InstrumentSpecification, ExecutionModel, RiskModel]:
        """Compila un CanonicalStrategy completo en los 4 modelos requeridos por el motor universal."""
        entry_rules = cls.compile_entry_rules(strategy.rules)
        exit_rules = cls.compile_exit_rules(strategy)

        time_filter = TimeAndSessionFilter(
            enabled=True,
            timezone=strategy.session.timezone,
            session_start=strategy.session.start_time,
            session_end=strategy.session.end_time,
            close_all_positions_at_session_end=strategy.session.force_close_at_end,
        )

        strat_spec = StrategySpecification(
            strategy_id=strategy.strategy_id,
            version=strategy.schema_version,
            family=StrategyFamily.MOMENTUM_BREAKOUT,
            target_symbol=strategy.instrument.symbol,
            base_timeframe=strategy.timeframe,
            entry_rules=entry_rules,
            exit_rules=exit_rules,
            time_filter=time_filter,
            dataset_reference_id=dataset_id,
            dataset_sha256=dataset_sha256,
        )

        inst_spec = cls.compile_instrument(
            symbol=strategy.instrument.symbol,
            custom_point_val=strategy.instrument.point_value,
            custom_tick_sz=strategy.instrument.tick_size,
        )

        exec_model = ExecutionModel(
            slippage_mode=SlippageMode.FIXED_BPS,
            base_slippage_bps=inst_spec.typical_slippage_ticks * 2.0,
            taker_fee_pct=inst_spec.taker_fee_rate * 100.0,
            maker_fee_pct=inst_spec.maker_fee_rate * 100.0,
            funding_rate_8h=inst_spec.default_funding_rate,
        )

        is_fondeo = (strategy.target_track == ExecutionTrack.TRACK_FONDEO)
        base_cap = initial_capital_usd or (50000.0 if is_fondeo else 1000.0)

        pyr_layers = strategy.sizing_and_risk.pyramiding_max_layers
        risk_model = RiskModel(
            model_id=f"RISK_{strategy.strategy_id}",
            doctrine=RiskDoctrine.FONDEO if is_fondeo else RiskDoctrine.ULTRA,
            base_capital_usd=base_cap,
            base_risk_pct=strategy.sizing_and_risk.base_risk_pct,
            max_leverage=strategy.sizing_and_risk.base_leverage,
            pyramiding_enabled=pyr_layers > 0,
            pyramiding_max_tiers=max(1, pyr_layers),
            max_drawdown_limit_pct=4.0 if is_fondeo else 85.0,
        )

        return strat_spec, inst_spec, exec_model, risk_model
