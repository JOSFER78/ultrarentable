"""Deterministic FAST Engine Interpreter & Backtest Executor."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

from services.api.app.config import DATA_DIR
from services.api.app.db.database import (
    AccountFeeSnapshotModel,
    BacktestModel,
    DatasetModel,
    InstrumentModel,
    InstrumentRuleSnapshotModel,
)
from services.api.app.dsl.engine import CompiledIR, StrategyDSL, canonical_json
from services.api.app.engine.indicator_calc import (
    compute_atr,
    compute_ema,
    compute_highest,
    compute_lowest,
    compute_roc,
    compute_rsi,
    compute_sma,
    compute_stddev,
    compute_volume_ratio,
)
from services.api.app.engine.ledger import BacktestLedger, TradeRecord
from services.api.app.engine.margin_model import (
    BingXIsolatedMarginModel,
    BingXMarketRiskRules,
    IsolatedPosition,
    MarginMode,
    MarginModelError,
    MarginPosition,
    PositionSide,
    calculate_unrealized_pnl,
    is_liquidated,
)
from services.api.app.engine.risk_rules_adapter import (
    RiskRulesUnavailable,
    load_verified_bingx_risk_rules,
)


class FastEngineException(Exception):
    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


class FastEngine:
    """Deterministic Fast Execution Engine for Compiled IR."""

    def __init__(self, db: Session, *, allow_legacy_risk: bool = False):
        self.db = db
        self.allow_legacy_risk = allow_legacy_risk
        self._dataset_cache: dict[
            str,
            tuple[str, list[dict[str, Any]]],
        ] = {}

    def _load_verified_risk_context(
        self, symbol: str, fee_multiplier: float
    ) -> tuple[BingXIsolatedMarginModel, float, float, dict[str, Any]]:
        rule_snapshot = (
            self.db.query(InstrumentRuleSnapshotModel)
            .filter(InstrumentRuleSnapshotModel.symbol == symbol)
            .order_by(InstrumentRuleSnapshotModel.captured_at.desc())
            .first()
        )
        fee_snapshot = (
            self.db.query(AccountFeeSnapshotModel)
            .filter(AccountFeeSnapshotModel.symbol == symbol)
            .order_by(AccountFeeSnapshotModel.captured_at.desc())
            .first()
        )
        try:
            rules = load_verified_bingx_risk_rules(rule_snapshot, fee_snapshot)
        except RiskRulesUnavailable as exc:
            raise FastEngineException("MISSING_VERIFIED_RISK_RULES", str(exc)) from exc
        maker_fee = float(fee_snapshot.maker_fee) * fee_multiplier
        taker_fee = float(fee_snapshot.taker_fee) * fee_multiplier
        stressed_rules = BingXMarketRiskRules(
            symbol=rules.symbol,
            max_leverage=rules.max_leverage,
            taker_fee_rate=taker_fee,
            maintenance_tiers=rules.maintenance_tiers,
        )
        return (
            BingXIsolatedMarginModel(stressed_rules),
            maker_fee,
            taker_fee,
            {
                "mode": "VERIFIED_BINGX_TIERED",
                "ruleSnapshotId": rule_snapshot.snapshot_id,
                "feeSnapshotId": fee_snapshot.snapshot_id,
                "maxLeverage": rules.max_leverage,
                "tierCount": len(rules.maintenance_tiers),
                "priceModel": "CONSERVATIVE_CANDLE_WORST_AS_MARK_AND_LAST",
            },
        )

    def run_backtest(
        self,
        strategy_input: dict[str, Any] | StrategyDSL,
        dataset_id: str | None = None,
        initial_capital: float = 10000.0,
        start_fraction: float = 0.0,
        end_fraction: float = 1.0,
        fee_multiplier: float = 1.0,
        slippage_bps: float = 0.0,
        persist_artifacts: bool = False,
    ) -> dict[str, Any]:
        """Run a deterministic backtest, optionally on a real temporal slice with stressed costs."""
        from services.api.app.dsl.engine import StrategyDSL, compile_to_ir

        if isinstance(strategy_input, dict):
            strategy_dsl = StrategyDSL.model_validate(strategy_input)
        else:
            strategy_dsl = strategy_input
        from services.api.app.dsl.engine import validate_semantics
        semantic_errors = validate_semantics(strategy_dsl)
        if semantic_errors:
            details = "; ".join(
                f"{item.path}:{item.code}" for item in semantic_errors
            )
            raise FastEngineException(
                "DSL_SEMANTIC_INVALID",
                f"Strategy failed semantic validation: {details}",
            )

        # Historical compatibility may seed approximate fees only when a caller
        # opts in explicitly. Production campaigns use verified snapshots.
        symbol = strategy_dsl.market.symbol
        timeframe = strategy_dsl.market.timeframe

        # Find approved dataset if not specified - strictly fail closed if not found
        if not dataset_id:
            ds = (
                self.db.query(DatasetModel)
                .filter(DatasetModel.symbol == symbol, DatasetModel.interval == timeframe, DatasetModel.status == "APPROVED")
                .first()
            )
            if not ds:
                raise FastEngineException(
                    "DATASET_NOT_FOUND",
                    f"No approved dataset available for symbol '{symbol}' and timeframe '{timeframe}' (ZERO-MOCKS FAIL-CLOSED)",
                )
            dataset_id = ds.dataset_id
        else:
            ds = self.db.query(DatasetModel).filter(DatasetModel.dataset_id == dataset_id, DatasetModel.status == "APPROVED").first()
            if not ds:
                raise FastEngineException(
                    "DATASET_NOT_APPROVED",
                    f"Dataset '{dataset_id}' not found or not in APPROVED state",
                )

        compiled_ir = compile_to_ir(strategy_dsl)
        res = self.execute(
            strategy_dsl=strategy_dsl,
            compiled_ir=compiled_ir,
            dataset_id=dataset_id,
            initial_capital=initial_capital,
            start_fraction=start_fraction,
            end_fraction=end_fraction,
            fee_multiplier=fee_multiplier,
            slippage_bps=slippage_bps,
            persist_artifacts=persist_artifacts,
        )
        res["finalEquity"] = res["metrics"]["final_equity"]
        res["netReturnPct"] = res["metrics"]["net_return_pct"]
        return res

    def execute(
        self,
        *,
        strategy_dsl: StrategyDSL,
        compiled_ir: CompiledIR,
        dataset_id: str,
        initial_capital: float = 10000.0,
        start_fraction: float = 0.0,
        end_fraction: float = 1.0,
        fee_multiplier: float = 1.0,
        slippage_bps: float = 0.0,
        persist_artifacts: bool = True,
    ) -> dict[str, Any]:
        # 1. Dataset Verification
        ds = self.db.query(DatasetModel).filter(DatasetModel.dataset_id == dataset_id).first()
        if not ds:
            raise FastEngineException("DATASET_NOT_FOUND", f"Dataset '{dataset_id}' not found in database")
        if ds.status != "APPROVED":
            raise FastEngineException("DATASET_NOT_APPROVED", f"Dataset '{dataset_id}' has status '{ds.status}', must be APPROVED")
        if ds.symbol != strategy_dsl.market.symbol or ds.interval != strategy_dsl.market.timeframe:
            raise FastEngineException(
                "DATASET_MARKET_MISMATCH",
                (
                    f"Dataset {ds.symbol}/{ds.interval} cannot execute strategy "
                    f"{strategy_dsl.market.symbol}/{strategy_dsl.market.timeframe}"
                ),
            )

        normalized_path = Path(ds.file_path)
        if not normalized_path.is_absolute():
            normalized_path = Path.cwd() / normalized_path
        if not normalized_path.exists():
            raise FastEngineException("NORMALIZED_FILE_MISSING", f"File '{normalized_path}' missing")

        checksum = str(ds.checksum_sha256 or "")
        cached = self._dataset_cache.get(dataset_id)
        if cached is not None and cached[0] == checksum:
            records = cached[1]
        else:
            normalized_bytes = normalized_path.read_bytes()
            if hashlib.sha256(normalized_bytes).hexdigest() != checksum:
                raise FastEngineException(
                    "CHECKSUM_MISMATCH",
                    "Dataset normalized file checksum mismatch",
                )
            records = json.loads(normalized_bytes)
            if not records:
                raise FastEngineException(
                    "EMPTY_DATASET",
                    "Dataset contains no candles",
                )
            self._dataset_cache[dataset_id] = (checksum, records)
        if not (0.0 <= start_fraction < end_fraction <= 1.0):
            raise FastEngineException("INVALID_RESEARCH_WINDOW", "Window fractions must satisfy 0 <= start < end <= 1")
        if fee_multiplier <= 0.0 or slippage_bps < 0.0:
            raise FastEngineException("INVALID_COST_STRESS", "Fee multiplier must be positive and slippage non-negative")
        source_count = len(records)
        start_index = int(source_count * start_fraction)
        end_index = min(source_count, max(start_index + 2, int(source_count * end_fraction)))
        records = records[start_index:end_index]
        if len(records) < 2:
            raise FastEngineException("RESEARCH_WINDOW_TOO_SHORT", "Selected window contains fewer than two candles")

        # 2. Load auditable exchange risk and fee rules.
        symbol = strategy_dsl.market.symbol
        risk_model: BingXIsolatedMarginModel | None = None
        if self.allow_legacy_risk:
            inst = self.db.query(InstrumentModel).filter(InstrumentModel.symbol == symbol).first()
            if not inst or inst.maker_fee_rate is None or inst.taker_fee_rate is None:
                raise FastEngineException(
                    "MISSING_FEE_SNAPSHOT",
                    f"Missing fee snapshot for symbol '{symbol}'.",
                )
            maker_fee = float(inst.maker_fee_rate) * fee_multiplier
            taker_fee = float(inst.taker_fee_rate) * fee_multiplier
            risk_context: dict[str, Any] = {"mode": "LEGACY_TEST_ONLY"}
        else:
            risk_model, maker_fee, taker_fee, risk_context = (
                self._load_verified_risk_context(symbol, fee_multiplier)
            )
        slippage_rate = slippage_bps / 10_000.0

        # 3. Check Required Series Availability
        available_series = {"OPEN", "HIGH", "LOW", "CLOSE", "VOLUME"}
        has_funding = any("funding_rate" in r for r in records)
        if has_funding:
            available_series.add("FUNDING_RATE")

        for req in compiled_ir.requiredSeries:
            if req not in available_series:
                if req == "FUNDING_RATE":
                    raise FastEngineException("MISSING_FUNDING_SERIES", "Strategy requires FUNDING_RATE series but dataset lacks funding data")
                raise FastEngineException("MISSING_REQUIRED_SERIES", f"Series '{req}' required by strategy but missing in dataset")

        # 4. Extract Price Series
        n_bars = len(records)
        times = np.array([r["time"] for r in records], dtype=np.int64)
        opens = np.array([r["open"] for r in records], dtype=np.float64)
        highs = np.array([r["high"] for r in records], dtype=np.float64)
        lows = np.array([r["low"] for r in records], dtype=np.float64)
        closes = np.array([r["close"] for r in records], dtype=np.float64)
        volumes = np.array([r["volume"] for r in records], dtype=np.float64)

        # 5. Evaluate IR Registers deterministically
        registers: dict[str, np.ndarray] = {}

        for instr in compiled_ir.instructions:
            op = instr.op
            args = instr.args
            out = instr.output

            if op == "LOAD_SERIES":
                name = args["series"]
                offset = args.get("offset", 0)
                if name == "OPEN":
                    s = opens
                elif name == "HIGH":
                    s = highs
                elif name == "LOW":
                    s = lows
                elif name == "CLOSE":
                    s = closes
                elif name == "VOLUME":
                    s = volumes
                else:
                    s = closes
                if offset > 0:
                    shifted = np.full(n_bars, np.nan, dtype=np.float64)
                    shifted[offset:] = s[:-offset]
                    registers[out] = shifted
                else:
                    registers[out] = s.copy()

            elif op == "LOAD_CONSTANT":
                registers[out] = np.full(n_bars, float(args["value"]), dtype=np.float64)

            elif op.startswith("COMPUTE_"):
                ind_name = op.replace("COMPUTE_", "")
                source_val = registers[args["source"]]
                period = int(args["period"])
                offset = int(args.get("offset", 0))

                if ind_name == "SMA":
                    res = compute_sma(source_val, period)
                elif ind_name == "EMA":
                    res = compute_ema(source_val, period)
                elif ind_name == "RSI":
                    res = compute_rsi(source_val, period)
                elif ind_name == "ATR":
                    res = compute_atr(highs, lows, closes, period)
                elif ind_name == "HIGHEST":
                    res = compute_highest(source_val, period)
                elif ind_name == "LOWEST":
                    res = compute_lowest(source_val, period)
                elif ind_name == "ROC":
                    res = compute_roc(source_val, period)
                elif ind_name == "STDDEV":
                    res = compute_stddev(source_val, period)
                elif ind_name == "VOLUME_RATIO":
                    res = compute_volume_ratio(volumes, period)
                else:
                    res = compute_sma(source_val, period)

                if offset > 0:
                    shifted = np.full(n_bars, np.nan, dtype=np.float64)
                    shifted[offset:] = res[:-offset]
                    registers[out] = shifted
                else:
                    registers[out] = res

            elif op.startswith("COMPARE_"):
                cmp_op = op.replace("COMPARE_", "")
                left = registers[args["left"]]
                right = registers[args["right"]]
                bool_res = np.zeros(n_bars, dtype=bool)

                if cmp_op == "GT":
                    bool_res = left > right
                elif cmp_op == "GTE":
                    bool_res = left >= right
                elif cmp_op == "LT":
                    bool_res = left < right
                elif cmp_op == "LTE":
                    bool_res = left <= right
                elif cmp_op == "EQ":
                    bool_res = np.isclose(left, right)
                elif cmp_op == "CROSS_ABOVE":
                    prev_left = np.roll(left, 1)
                    prev_right = np.roll(right, 1)
                    prev_left[0] = np.nan
                    bool_res = (prev_left <= prev_right) & (left > right)
                elif cmp_op == "CROSS_BELOW":
                    prev_left = np.roll(left, 1)
                    prev_right = np.roll(right, 1)
                    prev_left[0] = np.nan
                    bool_res = (prev_left >= prev_right) & (left < right)

                registers[out] = np.where(np.isnan(left) | np.isnan(right), False, bool_res)

            elif op.startswith("LOGIC_"):
                log_op = op.replace("LOGIC_", "")
                if log_op == "NOT":
                    inp = registers[args["input"]]
                    registers[out] = ~inp
                elif log_op == "ALL":
                    inputs = [registers[k] for k in args["inputs"]]
                    registers[out] = np.logical_and.reduce(inputs)
                elif log_op == "ANY":
                    inputs = [registers[k] for k in args["inputs"]]
                    registers[out] = np.logical_or.reduce(inputs)

            elif op == "ASSIGN_SIGNAL":
                sig_name = args["signal"]
                source_reg = registers[args["source"]]
                registers[sig_name] = source_reg

        # 6. Signal Execution Loop (Bar-by-Bar, t -> t+1 execution)
        ledger = BacktestLedger(initial_capital)
        leverage = strategy_dsl.position.leverage
        allocation_pct = strategy_dsl.position.allocationPct / 100.0
        compound = strategy_dsl.position.compound
        margin_mode = MarginMode(strategy_dsl.position.marginMode.value)
        if not self.allow_legacy_risk and margin_mode is MarginMode.CROSS:
            raise FastEngineException(
                "CROSS_MARGIN_MODEL_PENDING",
                "Verified cross-margin liquidation requires portfolio-wide positions and equity.",
            )
        risk_management = strategy_dsl.position.riskManagement
        entry_fee_rate = taker_fee if strategy_dsl.execution.entryOrderType.value == "MARKET" else maker_fee
        exit_fee_rate = taker_fee if strategy_dsl.execution.exitOrderType.value == "MARKET" else maker_fee

        def execution_price(raw_price: float, side: str, entering: bool) -> float:
            adverse_direction = 1.0 if (side == "LONG") == entering else -1.0
            return raw_price * (1.0 + adverse_direction * slippage_rate)

        long_entry_sig = registers.get("LONG_ENTRY", np.zeros(n_bars, dtype=bool))
        short_entry_sig = registers.get("SHORT_ENTRY", np.zeros(n_bars, dtype=bool))
        long_exit_sig = registers.get("LONG_EXIT", np.zeros(n_bars, dtype=bool))
        short_exit_sig = registers.get("SHORT_EXIT", np.zeros(n_bars, dtype=bool))

        active_position: dict[str, Any] | None = None
        pending_entry: dict[str, str] | None = None
        trade_counter = 0
        entry_rejections = 0

        def close_position(
            raw_price: float,
            exit_time: int,
            reason: str,
            *,
            liquidation: bool = False,
        ) -> None:
            nonlocal active_position, trade_counter
            if active_position is None:
                return
            side = active_position["side"]
            entry_price = active_position["entry_price"]
            quantity = active_position["quantity"]
            initial_margin = active_position["initial_margin"]
            exec_price = raw_price if liquidation else execution_price(raw_price, side, False)
            pos_side = PositionSide.LONG if side == "LONG" else PositionSide.SHORT
            gross_pnl = calculate_unrealized_pnl(
                pos_side, entry_price, exec_price, quantity
            )
            fees = (
                entry_price * quantity * entry_fee_rate
                + exec_price * quantity * exit_fee_rate
            )
            if liquidation:
                net_pnl = (
                    -ledger.current_capital
                    if margin_mode is MarginMode.CROSS
                    else -initial_margin
                )
                return_pct = -100.0
            else:
                net_pnl = gross_pnl - fees
                return_pct = (
                    (net_pnl / initial_margin) * 100.0
                    if initial_margin > 0
                    else 0.0
                )
            trade_counter += 1
            ledger.record_trade(TradeRecord(
                trade_id=f"tr_{trade_counter:04d}",
                symbol=symbol,
                side=side,
                entry_time=active_position["entry_time"],
                entry_price=entry_price,
                exit_time=exit_time,
                exit_price=exec_price,
                quantity=quantity,
                leverage=leverage,
                gross_pnl=gross_pnl,
                fees=fees,
                funding=0.0,
                net_pnl=net_pnl,
                return_pct=return_pct,
                exit_reason=reason,
            ))
            active_position = None

        for i in range(n_bars):
            current_time = int(times[i])
            current_close = float(closes[i])
            current_open = float(opens[i])

            # Orders decided on the previous close execute first at this open.
            if active_position is not None:
                pending_exit = active_position.get("pending_exit")
                max_holding_reached = bool(
                    risk_management is not None
                    and i - int(active_position["entry_index"])
                    >= risk_management.maxHoldingBars
                )
                if pending_exit:
                    close_position(current_open, current_time, str(pending_exit))
                elif max_holding_reached:
                    close_position(current_open, current_time, "MAX_HOLDING")

            if active_position is None and i > 0 and pending_entry:
                entry_side = pending_entry["side"]
                exec_price = execution_price(current_open, entry_side, True)
                sizing_capital = ledger.current_capital if compound else initial_capital
                avail_cap = min(sizing_capital, ledger.current_capital)
                alloc_margin = max(0.0, avail_cap * allocation_pct)
                position_notional = alloc_margin * leverage
                quantity = position_notional / exec_price if exec_price > 0 else 0.0
                if alloc_margin > 0 and quantity > 0:
                    entry_allowed = True
                    if risk_model is not None:
                        try:
                            entry_assessment = risk_model.assess(
                                IsolatedPosition(
                                    PositionSide.LONG
                                    if entry_side == "LONG"
                                    else PositionSide.SHORT,
                                    exec_price,
                                    quantity,
                                    leverage,
                                ),
                                mark_price=exec_price,
                                last_price=exec_price,
                            )
                            entry_allowed = entry_assessment.executable_at_entry
                        except MarginModelError:
                            entry_allowed = False
                    if entry_allowed:
                        active_position = {
                            "side": entry_side,
                            "entry_price": exec_price,
                            "entry_time": current_time,
                            "entry_index": i,
                            "best_price": exec_price,
                            "quantity": quantity,
                            "initial_margin": alloc_margin,
                            "pending_exit": None,
                        }
                    else:
                        entry_rejections += 1
                pending_entry = None

            # Intrabar risk applies after open executions, including entry-bar risk.
            if active_position is not None:
                side = active_position["side"]
                entry_price = float(active_position["entry_price"])
                quantity = float(active_position["quantity"])
                initial_margin = float(active_position["initial_margin"])
                worst_price = float(lows[i]) if side == "LONG" else float(highs[i])
                if risk_model is not None:
                    try:
                        liquidation_triggered = risk_model.assess(
                            IsolatedPosition(
                                PositionSide.LONG
                                if side == "LONG"
                                else PositionSide.SHORT,
                                entry_price,
                                quantity,
                                leverage,
                            ),
                            mark_price=worst_price,
                            last_price=worst_price,
                        ).liquidated
                    except MarginModelError:
                        liquidation_triggered = True
                else:
                    pos_obj = MarginPosition(
                        side=PositionSide.LONG
                        if side == "LONG"
                        else PositionSide.SHORT,
                        margin_mode=margin_mode,
                        leverage=leverage,
                        entry_price=entry_price,
                        quantity=quantity,
                        initial_margin=initial_margin,
                    )
                    liquidation_triggered = is_liquidated(
                        pos_obj, worst_price, ledger.current_capital
                    )
                if liquidation_triggered:
                    close_position(
                        worst_price,
                        current_time,
                        "LIQUIDATION",
                        liquidation=True,
                    )
                elif risk_management is not None:
                    stop_fraction = risk_management.stopLossPct / 100.0
                    take_fraction = risk_management.takeProfitPct / 100.0
                    trail_value = risk_management.trailingStopPct
                    if side == "LONG":
                        stop_level = entry_price * (1.0 - stop_fraction)
                        if trail_value is not None:
                            trailing_level = float(active_position["best_price"]) * (
                                1.0 - trail_value / 100.0
                            )
                            stop_level = max(stop_level, trailing_level)
                        take_level = entry_price * (1.0 + take_fraction)
                        stop_hit = float(lows[i]) <= stop_level
                        take_hit = float(highs[i]) >= take_level
                        if stop_hit:
                            close_position(
                                min(current_open, stop_level),
                                current_time,
                                "STOP_LOSS",
                            )
                        elif take_hit:
                            close_position(take_level, current_time, "TAKE_PROFIT")
                        else:
                            active_position["best_price"] = max(
                                float(active_position["best_price"]),
                                float(highs[i]),
                            )
                    else:
                        stop_level = entry_price * (1.0 + stop_fraction)
                        if trail_value is not None:
                            trailing_level = float(active_position["best_price"]) * (
                                1.0 + trail_value / 100.0
                            )
                            stop_level = min(stop_level, trailing_level)
                        take_level = entry_price * (1.0 - take_fraction)
                        stop_hit = float(highs[i]) >= stop_level
                        take_hit = float(lows[i]) <= take_level
                        if stop_hit:
                            close_position(
                                max(current_open, stop_level),
                                current_time,
                                "STOP_LOSS",
                            )
                        elif take_hit:
                            close_position(take_level, current_time, "TAKE_PROFIT")
                        else:
                            active_position["best_price"] = min(
                                float(active_position["best_price"]),
                                float(lows[i]),
                            )

            if active_position is not None:
                side = active_position["side"]
                unrealized = calculate_unrealized_pnl(
                    PositionSide.LONG if side == "LONG" else PositionSide.SHORT,
                    float(active_position["entry_price"]),
                    current_close,
                    float(active_position["quantity"]),
                )
                bar_equity = ledger.current_capital + unrealized
            else:
                bar_equity = ledger.current_capital
            ledger.record_equity(current_time, bar_equity)

            if ledger.current_capital <= 0.0:
                break

            # Current-close signals can only affect the next bar's open.
            pending_entry = None
            if active_position is None:
                if bool(long_entry_sig[i]):
                    pending_entry = {"side": "LONG"}
                elif bool(short_entry_sig[i]):
                    pending_entry = {"side": "SHORT"}
            else:
                side = active_position["side"]
                if side == "LONG" and bool(long_exit_sig[i]):
                    active_position["pending_exit"] = "SIGNAL"
                elif side == "SHORT" and bool(short_exit_sig[i]):
                    active_position["pending_exit"] = "SIGNAL"

        if active_position is not None:
            close_position(float(closes[-1]), int(times[-1]), "END_OF_DATA")
            ledger.record_equity(int(times[-1]), ledger.current_capital)

        # 7. Package Artifacts
        artifacts = ledger.to_artifacts()
        metrics = artifacts["metrics"]
        dsl_hash = compiled_ir.dslHash
        ir_hash = compiled_ir.irHash

        backtest_id = f"bt_fast_{ir_hash[:12]}_{artifacts['checksum'][:10]}"
        db_status = "COMPLETED" if metrics["final_equity"] > 0 else "LIQUIDATED"
        artifacts_dir: Path | None = None
        ledger_path: Path | None = None
        if persist_artifacts:
            artifacts_dir = Path(DATA_DIR) / "artifacts" / "backtests" / backtest_id
            artifacts_dir.mkdir(parents=True, exist_ok=True)
            ledger_path = artifacts_dir / "ledger.json"
            ledger_path.write_text(
                json.dumps(artifacts, separators=(",", ":"), ensure_ascii=False),
                encoding="utf-8",
            )
            self.db.merge(
                BacktestModel(
                    backtest_id=backtest_id,
                    strategy_id=f"strat_{dsl_hash[:16]}",
                    dataset_id=dataset_id,
                    engine_type="FAST_APPROXIMATE",
                    initial_capital=initial_capital,
                    leverage=leverage,
                    final_equity=metrics["final_equity"],
                    net_return_pct=metrics["net_return_pct"],
                    max_drawdown_pct=metrics["max_drawdown_pct"],
                    win_rate=metrics["win_rate"],
                    trades_count=metrics["trades_count"],
                    profit_factor=metrics["profit_factor"],
                    checksum=artifacts["checksum"],
                    ledger_path=str(ledger_path),
                    artifacts_path=str(artifacts_dir),
                    status=db_status,
                )
            )
            self.db.commit()

        return {
            "backtestId": backtest_id,
            "engineType": "FAST_APPROXIMATE",
            "datasetId": dataset_id,
            "metrics": metrics,
            "checksum": artifacts["checksum"],
            "artifactsPath": str(artifacts_dir) if artifacts_dir else None,
            "status": db_status,
            "liquidated": db_status == "LIQUIDATED",
            "tradesCount": metrics["trades_count"],
            "maxDrawdownPct": metrics["max_drawdown_pct"],
            "ledgerPath": str(ledger_path) if ledger_path else None,
            "trades": artifacts["trades"],
            "window": {"startFraction": start_fraction, "endFraction": end_fraction, "sourceRecords": source_count, "usedRecords": len(records)},
            "costs": {"feeMultiplier": fee_multiplier, "slippageBps": slippage_bps},
            "riskRules": {**risk_context, "entryRejections": entry_rejections},
        }
