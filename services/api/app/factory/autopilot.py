from __future__ import annotations

import json
import hashlib
import math
import os
import random
import time
import uuid
from pathlib import Path
from statistics import median
from typing import Any, Dict, Iterator, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from services.api.app.db.database import (
    SessionLocal,
    AutopilotRunModel,
    AutopilotDecisionModel,
    OpportunityMatrixModel,
    LeverageTrialModel,
    NoveltyArchiveModel,
    CampaignTrialModel,
    StrategyModel,
    DatasetModel,
    BacktestModel,
    InstrumentRuleSnapshotModel,
    AccountFeeSnapshotModel,
)
from services.api.app.dsl.engine import StrategyDSL, validate_semantics, compile_to_ir, canonical_hash
from services.api.app.factory.grammar import TypedGrammar
from services.api.app.factory.seed_factory import SeedFactory
from services.api.app.factory.genetic import GeneticOperators
from services.api.app.factory.optimizer import OptunaOptimizer
from services.api.app.factory.repairer import DirectedRepairer
from services.api.app.engine.fast_engine import FastEngine
from services.api.app.factory.strategy_evidence import (
    EvidenceStatus,
    StrategyEvidenceJudge,
    load_trade_evidence,
)
from services.api.app.factory.campaign_planner import AutomaticCampaignPlanner
from services.api.app.factory.fast_engine_campaign import FastEngineCampaignRunner
from services.api.app.factory.campaign_suite import FastEngineCampaignSuite


class UniverseScanner:
    """Rank only verifiable datasets from the configured research universe.

    The previous implementation fabricated approved ETH/BTC opportunities and fixed
    liquidity/volatility scores when no data existed. This scanner fails closed: every
    candidate must have an APPROVED database row, a valid manifest, a matching RAW and
    normalized checksum, closed/gap-free candles, and enough history for the configured
    random-window research horizon.
    """

    _INTERVAL_MS = {"1m": 60_000, "5m": 300_000, "15m": 900_000}

    def __init__(
        self,
        symbols: Optional[List[str]] = None,
        intervals: Optional[List[str]] = None,
        minimum_history_days: Optional[int] = None,
        require_complete_universe: bool = True,
    ) -> None:
        self.symbols = symbols or self._csv_env("UNIVERSE_SYMBOLS", ["ETH-USDT"])
        self.intervals = intervals or self._csv_env(
            "UNIVERSE_INTERVALS", ["1m", "5m", "15m"]
        )
        self.minimum_history_days = (
            minimum_history_days
            if minimum_history_days is not None
            else int(os.getenv("UNIVERSE_MIN_HISTORY_DAYS", "159"))
        )
        self.require_complete_universe = require_complete_universe
        self.rejections: List[Dict[str, Any]] = []

        unsupported = sorted(set(self.intervals) - set(self._INTERVAL_MS))
        if unsupported:
            raise ValueError(f"UNSUPPORTED_UNIVERSE_INTERVALS: {','.join(unsupported)}")

    @staticmethod
    def _csv_env(name: str, default: List[str]) -> List[str]:
        raw = os.getenv(name)
        return [item.strip() for item in raw.split(",") if item.strip()] if raw else default

    @staticmethod
    def _sha256(path: Path) -> str:
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    @staticmethod
    def _resolve_path(value: str, manifest_path: Optional[Path] = None) -> Path:
        path = Path(value)
        if path.is_absolute():
            return path
        candidates = [Path.cwd() / path]
        if manifest_path is not None:
            candidates.extend(
                [manifest_path.parent / path, manifest_path.parent.parent / path]
            )
        return next((candidate.resolve() for candidate in candidates if candidate.exists()), candidates[0].resolve())

    @staticmethod
    def _minmax_scores(values: List[float]) -> List[float]:
        if not values:
            return []
        low, high = min(values), max(values)
        if math.isclose(low, high):
            return [100.0 for _ in values]
        return [round(100.0 * ((value - low) / (high - low)), 8) for value in values]

    @staticmethod
    def _iter_json_array(path: Path, chunk_size: int = 1024 * 1024) -> Iterator[Any]:
        """Stream a compact JSON array without loading a multi-year dataset into RAM."""
        decoder = json.JSONDecoder()
        buffer = ""
        position = 0
        started = False
        eof = False

        with path.open("r", encoding="utf-8") as handle:
            while True:
                while position < len(buffer) and buffer[position].isspace():
                    position += 1

                if not started:
                    if position >= len(buffer):
                        chunk = handle.read(chunk_size)
                        if not chunk:
                            raise ValueError("NORMALIZED_JSON_EMPTY")
                        buffer = chunk
                        position = 0
                        continue
                    if buffer[position] != "[":
                        raise ValueError("NORMALIZED_JSON_NOT_ARRAY")
                    started = True
                    position += 1
                    continue

                while position < len(buffer) and (
                    buffer[position].isspace() or buffer[position] == ","
                ):
                    position += 1

                if position < len(buffer) and buffer[position] == "]":
                    return

                if position >= len(buffer):
                    chunk = handle.read(chunk_size)
                    if not chunk:
                        if eof:
                            raise ValueError("NORMALIZED_JSON_UNTERMINATED")
                        eof = True
                    buffer = buffer[position:] + chunk
                    position = 0
                    continue

                try:
                    record, end = decoder.raw_decode(buffer, position)
                except json.JSONDecodeError as exc:
                    chunk = handle.read(chunk_size)
                    if not chunk:
                        raise ValueError("NORMALIZED_JSON_INVALID") from exc
                    buffer = buffer[position:] + chunk
                    position = 0
                    continue
                yield record
                position = end

                if position > chunk_size:
                    buffer = buffer[position:]
                    position = 0

    def _dataset_metrics(self, dataset: DatasetModel) -> tuple[Optional[Dict[str, Any]], List[str]]:
        errors: List[str] = []
        interval = dataset.interval or ""
        step_ms = self._INTERVAL_MS.get(interval)
        if step_ms is None:
            return None, ["UNSUPPORTED_INTERVAL"]

        if not dataset.file_path or not dataset.manifest_path:
            return None, ["DATASET_ARTIFACT_PATH_MISSING"]
        normalized_path = self._resolve_path(dataset.file_path)
        manifest_path = self._resolve_path(dataset.manifest_path)
        if not normalized_path.is_file():
            errors.append("NORMALIZED_FILE_MISSING")
        if not manifest_path.is_file():
            errors.append("MANIFEST_FILE_MISSING")
        if errors:
            return None, errors

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None, ["MANIFEST_INVALID_JSON"]

        if manifest.get("datasetId") != dataset.dataset_id:
            errors.append("MANIFEST_DATASET_ID_MISMATCH")
        if manifest.get("symbol") != dataset.symbol or manifest.get("interval") != interval:
            errors.append("MANIFEST_MARKET_MISMATCH")
        if manifest.get("closedRecordsOnly") is not True:
            errors.append("OPEN_CANDLES_NOT_EXCLUDED")
        for field in ("gapCount", "duplicateCount", "outOfOrderCount"):
            if int(manifest.get(field, 0) or 0) != 0:
                errors.append(f"MANIFEST_{field.upper()}_NONZERO")
        if float(manifest.get("coveragePct", 0.0) or 0.0) < 99.999:
            errors.append("INSUFFICIENT_COVERAGE")

        normalized_checksum = self._sha256(normalized_path)
        if normalized_checksum != dataset.checksum_sha256:
            errors.append("DATABASE_CHECKSUM_MISMATCH")
        if normalized_checksum != manifest.get("checksumSha256"):
            errors.append("MANIFEST_CHECKSUM_MISMATCH")

        raw_value = manifest.get("rawPath")
        if not raw_value:
            errors.append("RAW_PATH_MISSING")
        else:
            raw_path = self._resolve_path(str(raw_value), manifest_path)
            if not raw_path.is_file():
                errors.append("RAW_FILE_MISSING")
            elif self._sha256(raw_path) != manifest.get("rawChecksumSha256"):
                errors.append("RAW_CHECKSUM_MISMATCH")

        if errors:
            return None, errors

        previous_time: Optional[int] = None
        previous_close: Optional[float] = None
        turnover_per_minute: List[float] = []
        return_count = 0
        return_mean = 0.0
        return_m2 = 0.0
        actual_count = 0
        first_time: Optional[int] = None
        last_time: Optional[int] = None
        now_ms = int(time.time() * 1000)
        interval_minutes = step_ms / 60_000

        try:
            records = self._iter_json_array(normalized_path)
            for record in records:
                actual_count += 1
                candle_time = int(record["time"])
                open_price = float(record["open"])
                high = float(record["high"])
                low = float(record["low"])
                close = float(record["close"])
                volume = float(record["volume"])
                if not all(
                    math.isfinite(value)
                    for value in (open_price, high, low, close, volume)
                ):
                    errors.append("NORMALIZED_NONFINITE_VALUE")
                    break
                if (
                    min(open_price, high, low, close) <= 0
                    or volume < 0
                    or low > min(open_price, close)
                    or high < max(open_price, close)
                ):
                    errors.append("NORMALIZED_OHLCV_INVARIANT_FAILED")
                    break
                if previous_time is not None and candle_time - previous_time != step_ms:
                    errors.append("NORMALIZED_TIMELINE_NOT_CONTIGUOUS")
                    break
                if candle_time + step_ms > now_ms:
                    errors.append("NORMALIZED_CONTAINS_OPEN_CANDLE")
                    break
                if previous_close is not None:
                    log_return = math.log(close / previous_close)
                    return_count += 1
                    delta = log_return - return_mean
                    return_mean += delta / return_count
                    return_m2 += delta * (log_return - return_mean)
                turnover_per_minute.append((close * volume) / interval_minutes)
                if first_time is None:
                    first_time = candle_time
                last_time = candle_time
                previous_time = candle_time
                previous_close = close
        except (KeyError, TypeError, ValueError, OSError):
            errors.append("NORMALIZED_RECORD_INVALID")

        if errors:
            return None, errors

        if actual_count < 2 or first_time is None or last_time is None or return_count == 0:
            return None, ["NORMALIZED_RECORDS_INSUFFICIENT"]

        history_days = ((last_time + step_ms) - first_time) / 86_400_000
        if actual_count != int(dataset.record_count or 0) or actual_count != int(manifest.get("recordCount", 0) or 0):
            errors.append("RECORD_COUNT_MISMATCH")
        if first_time != int(dataset.start_time or 0) or last_time != int(dataset.end_time or 0):
            errors.append("DATABASE_TIME_RANGE_MISMATCH")
        if history_days + 1e-9 < self.minimum_history_days:
            errors.append("HISTORY_WINDOW_TOO_SHORT")
        if errors:
            return None, errors

        periods_per_day = 86_400_000 / step_ms
        return_stddev = math.sqrt(return_m2 / return_count)
        daily_volatility_pct = return_stddev * math.sqrt(periods_per_day) * 100
        return {
            "dataset_id": dataset.dataset_id,
            "symbol": dataset.symbol,
            "interval": interval,
            "record_count": actual_count,
            "history_days": round(history_days, 6),
            "coverage_pct": float(manifest.get("coveragePct", 100.0)),
            "median_turnover_per_minute": median(turnover_per_minute),
            "daily_volatility_pct": daily_volatility_pct,
            "start_time": first_time,
            "end_time": last_time,
        }, []

    def scan_opportunities(self, db: Session) -> List[Dict[str, Any]]:
        self.rejections = []
        datasets = (
            db.query(DatasetModel)
            .filter(
                DatasetModel.status == "APPROVED",
                DatasetModel.symbol.in_(self.symbols),
                DatasetModel.interval.in_(self.intervals),
            )
            .all()
        )

        best_by_market: Dict[tuple[str, str], Dict[str, Any]] = {}
        for dataset in datasets:
            metrics, errors = self._dataset_metrics(dataset)
            if errors or metrics is None:
                self.rejections.append(
                    {"dataset_id": dataset.dataset_id, "errors": errors or ["UNKNOWN_DATASET_ERROR"]}
                )
                continue
            market = (dataset.symbol, dataset.interval or "")
            current = best_by_market.get(market)
            if current is None or (
                metrics["history_days"], metrics["record_count"], metrics["end_time"]
            ) > (
                current["history_days"], current["record_count"], current["end_time"]
            ):
                best_by_market[market] = metrics

        required_markets = {(symbol, interval) for symbol in self.symbols for interval in self.intervals}
        missing_markets = sorted(required_markets - set(best_by_market))
        if self.require_complete_universe and missing_markets:
            self.rejections.extend(
                {
                    "dataset_id": None,
                    "symbol": symbol,
                    "interval": interval,
                    "errors": ["MISSING_REQUIRED_APPROVED_DATASET"],
                }
                for symbol, interval in missing_markets
            )
            db.query(OpportunityMatrixModel).filter(
                OpportunityMatrixModel.symbol.in_(self.symbols),
                OpportunityMatrixModel.interval.in_(self.intervals),
            ).update({OpportunityMatrixModel.dataset_status: "NOT_READY"}, synchronize_session=False)
            db.commit()
            return []

        candidates = list(best_by_market.values())
        if not candidates:
            return []

        liquidity_scores = self._minmax_scores(
            [float(candidate["median_turnover_per_minute"]) for candidate in candidates]
        )
        volatility_scores = self._minmax_scores(
            [float(candidate["daily_volatility_pct"]) for candidate in candidates]
        )
        for candidate, liquidity_score, volatility_score in zip(
            candidates, liquidity_scores, volatility_scores
        ):
            candidate["liquidity_score"] = liquidity_score
            candidate["volatility_score"] = volatility_score
            candidate["opportunity_score"] = round(
                (0.25 * liquidity_score)
                + (0.65 * volatility_score)
                + (0.10 * float(candidate["coverage_pct"])),
                8,
            )

        candidates.sort(
            key=lambda candidate: (
                candidate["opportunity_score"],
                candidate["daily_volatility_pct"],
                candidate["median_turnover_per_minute"],
                candidate["record_count"],
            ),
            reverse=True,
        )

        for rank, candidate in enumerate(candidates, start=1):
            candidate["rank"] = rank
            entry = db.query(OpportunityMatrixModel).filter(
                OpportunityMatrixModel.symbol == candidate["symbol"],
                OpportunityMatrixModel.interval == candidate["interval"],
            ).first()
            if entry is None:
                entry = OpportunityMatrixModel(
                    matrix_id=f"op_{uuid.uuid4().hex[:8]}",
                    symbol=candidate["symbol"],
                    interval=candidate["interval"],
                )
                db.add(entry)
            entry.liquidity_score = candidate["liquidity_score"]
            entry.volatility_score = candidate["volatility_score"]
            entry.dataset_status = "APPROVED"
            entry.rank = rank

        db.commit()
        return candidates


class LeverageAutopilot:
    """Explores real leverage tiers using actual FastEngine backtest execution."""

    def evaluate_leverage_staircase(
        self,
        db: Session,
        run_id: str,
        strategy_id: str,
        symbol: str,
        interval: str,
        history_days: float,
        dsl_dict: dict[str, Any],
        alternatives_tried: int,
        leverage_tiers: Optional[List[int]] = None,
        research_start_ms: Optional[int] = None,
    ) -> Dict[str, Any]:
        # Query snapshot rules
        rule_snap = db.query(InstrumentRuleSnapshotModel).filter(
            InstrumentRuleSnapshotModel.symbol == symbol
        ).first()

        max_allowed = min(500, max(1, int(rule_snap.max_leverage if rule_snap else 20)))
        requested_leverages = (
            leverage_tiers if leverage_tiers is not None else range(1, max_allowed + 1)
        )
        leverage_tiers = sorted({
            int(lev) for lev in requested_leverages if 1 <= int(lev) <= max_allowed
        })

        best_leverage = None
        best_equity = 0.0
        winning_backtest_id = None
        winning_evidence = None
        evidence_results: List[Dict[str, Any]] = []

        fast_engine = FastEngine(db=db)
        judge = StrategyEvidenceJudge()
        timeframe_minutes = {"1m": 1, "5m": 5, "15m": 15, "1h": 60}[interval]

        for lev in leverage_tiers:
            # Modify leverage in dsl
            strat_copy = json.loads(json.dumps(dsl_dict))
            strat_copy["position"]["leverage"] = lev

            try:
                # RUN REAL FAST ENGINE BACKTEST (NO FAKE FORMULA)
                bt_result = fast_engine.run_backtest(
                    strat_copy,
                    initial_capital=10000.0,
                    persist_artifacts=False,
                )
                final_equity = bt_result.get("finalEquity", 10000.0)
                bt_id = bt_result.get("backtestId", f"bt_{uuid.uuid4().hex[:8]}")
                backtest = (
                    db.query(BacktestModel)
                    .filter(BacktestModel.backtest_id == bt_id)
                    .first()
                )
                ledger_path = backtest.ledger_path if backtest else None
                trade_returns, trade_timestamps = load_trade_evidence(
                    bt_result, ledger_path
                )
                reported_trade_count = (
                    int(backtest.trades_count)
                    if backtest and backtest.trades_count is not None
                    else int(bt_result.get("tradesCount", bt_result.get("tradeCount", len(trade_returns))))
                )
                evidence = judge.evaluate(
                    initial_equity=10000.0,
                    final_equity=float(final_equity),
                    timeframe_minutes=timeframe_minutes,
                    history_days=history_days,
                    trade_returns=trade_returns,
                    trade_timestamps_ms=trade_timestamps,
                    reported_trade_count=reported_trade_count,
                    strategy=strat_copy,
                    alternatives_tried=alternatives_tried,
                    liquidated=bool(bt_result.get("liquidated", False)),
                    research_start_ms=research_start_ms,
                )
                evidence_results.append(
                    {"leverage": lev, "backtestId": bt_id, **evidence.to_dict()}
                )

                trial = LeverageTrialModel(
                    trial_id=f"lev_{uuid.uuid4().hex[:8]}",
                    run_id=run_id,
                    strategy_id=strategy_id,
                    symbol=symbol,
                    leverage=lev,
                    tier=1 if lev <= 20 else 2,
                    status=evidence.status.value,
                    final_equity=final_equity,
                )
                db.add(trial)

                if evidence.rankable and final_equity > best_equity:
                    best_equity = final_equity
                    best_leverage = lev
                    winning_backtest_id = bt_id
                    winning_evidence = evidence.to_dict()
            except Exception:
                trial = LeverageTrialModel(
                    trial_id=f"lev_{uuid.uuid4().hex[:8]}",
                    run_id=run_id,
                    strategy_id=strategy_id,
                    symbol=symbol,
                    leverage=lev,
                    tier=1,
                    status="FAILED",
                    final_equity=None,
                )
                db.add(trial)

        db.commit()
        return {
            "winning_leverage": best_leverage,
            "max_equity": best_equity,
            "winning_backtest_id": winning_backtest_id,
            "winning_evidence": winning_evidence,
            "evidence_results": evidence_results,
            "rankable": winning_backtest_id is not None,
        }


class AutopilotController:
    """Master controller managing the single-button autonomous quantitative search."""

    def __init__(self, run_id: Optional[str] = None) -> None:
        self.run_id = run_id or f"run_{uuid.uuid4().hex[:8]}"

    def log_decision(self, db: Session, module: str, decision: str, reason: str, alternatives: Optional[Dict] = None) -> None:
        dec = AutopilotDecisionModel(
            decision_id=f"dec_{uuid.uuid4().hex[:8]}",
            run_id=self.run_id,
            module=module,
            decision=decision,
            reason=reason,
            alternatives_json=json.dumps(alternatives) if alternatives else None,
        )
        db.add(dec)
        db.commit()

    def start_autopilot(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            run = db.query(AutopilotRunModel).filter(AutopilotRunModel.run_id == self.run_id).first()
            if not run:
                run = AutopilotRunModel(
                    run_id=self.run_id,
                    status="SCANNING",
                    mode="AUTOPILOT_ULTRA",
                    cpu_budget_workers=4,
                )
                db.add(run)
                db.commit()
            else:
                run.status = "SCANNING"
                db.commit()

            self.log_decision(
                db,
                "AutopilotController",
                "START_AUTOPILOT_ULTRA",
                "Iniciando busqueda autonoma cuantitativa real sin formulas simuladas ni parametros manuales.",
            )

            # 1. Real Universe Scan
            scanner = UniverseScanner()
            opportunities = scanner.scan_opportunities(db)
            if scanner.rejections:
                self.log_decision(
                    db,
                    "UniverseScanner",
                    "DATASETS_EXCLUDED_FROM_UNIVERSE",
                    "Se excluyeron datasets ausentes o que no superaron integridad, cierre, continuidad o historia minima.",
                    {"rejections": scanner.rejections},
                )

            if not opportunities:
                run.current_symbol = None
                run.current_interval = None
                run.explored_symbols_count = 0
                run.evaluated_strategies_count = 0
                run.status = "BLOCKED_DATA"
                db.commit()
                requirements = {
                    "symbols": scanner.symbols,
                    "intervals": scanner.intervals,
                    "minimumHistoryDays": scanner.minimum_history_days,
                    "requiredStatus": "APPROVED",
                }
                self.log_decision(
                    db,
                    "UniverseScanner",
                    "BLOCKED_NO_VERIFIED_UNIVERSE",
                    "El autopiloto se detuvo antes de generar estrategias porque no existe un universo completo de datos verificables.",
                    {"requirements": requirements, "rejections": scanner.rejections},
                )
                return {
                    "runId": self.run_id,
                    "status": "BLOCKED_DATA",
                    "symbol": None,
                    "interval": None,
                    "evaluatedCount": 0,
                    "bestCandidateId": None,
                    "bestFastReturnPct": 0.0,
                    "dataRequirements": requirements,
                    "rejections": scanner.rejections,
                }

            rule_snapshot = db.query(InstrumentRuleSnapshotModel).filter(
                InstrumentRuleSnapshotModel.symbol == opportunities[0]["symbol"]
            ).first()
            max_leverage = int(
                rule_snapshot.max_leverage if rule_snapshot else 20
            )

            run.current_symbol = opportunities[0]["symbol"]
            run.current_interval = "MULTI"
            run.explored_symbols_count = len(opportunities)
            run.status = "RUNNING"
            db.commit()

            self.log_decision(
                db,
                "UniverseScanner",
                "START_COARSE_TO_FINE_SUITE",
                (
                    "Universo verificado ordenado de 15m a 1m; cada mercado "
                    "continua linajes prometedores y rota al detectar estancamiento."
                ),
                {"opportunities": opportunities},
            )

            def control_state() -> str:
                db.expire_all()
                current = (
                    db.query(AutopilotRunModel)
                    .filter(AutopilotRunModel.run_id == self.run_id)
                    .first()
                )
                return str(current.status if current else "STOPPED")

            suite = FastEngineCampaignSuite(db, seed=42).run(
                opportunities,
                max_leverage=max_leverage,
                rounds_per_market=3,
                control_state=control_state,
            )
            suite_payload = suite.to_dict()
            champion_outcome = suite.champion_outcome
            champion_id = None
            best_fast_return = 0.0
            if champion_outcome is not None and champion_outcome.champion is not None:
                champion_dsl = champion_outcome.champion["strategy"]
                champion_ir = compile_to_ir(
                    StrategyDSL.model_validate(champion_dsl)
                )
                champion_id = f"strat_ultra_{champion_ir.dslHash[:16]}"
                db.merge(StrategyModel(
                    strategy_id=champion_id,
                    name=champion_dsl.get("metadata", {}).get(
                        "name", "Validated Ultra"
                    ),
                    version="1.0.0",
                    family=champion_dsl.get("metadata", {}).get(
                        "family", "QUANT"
                    ),
                    author="AUTOPILOT_EVOLUTION",
                    canonical_hash=champion_ir.dslHash,
                    dsl_json=json.dumps(champion_dsl),
                    validation_status="LOCKBOX_VALIDATED",
                ))
                best_fast_return = (
                    float(champion_outcome.champion["finalEquitySearch"])
                    - 10_000.0
                ) / 100.0

            run.evaluated_strategies_count = suite.evaluations
            run.best_candidate_id = champion_id
            run.best_fast_return_pct = best_fast_return
            run.status = suite.status
            db.commit()
            self.log_decision(
                db,
                "FastEngineCampaignSuite",
                suite.status,
                (
                    "Busqueda evolutiva multirronda terminada con continuidad, "
                    "rotacion por estancamiento y lockbox intacto."
                ),
                suite_payload,
            )
            return {
                "runId": self.run_id,
                "status": suite.status,
                "symbol": opportunities[0]["symbol"],
                "interval": "MULTI",
                "evaluatedCount": suite.evaluations,
                "bestCandidateId": champion_id,
                "bestFastReturnPct": best_fast_return,
                "campaignSuite": suite_payload,
            }

        except Exception as exc:
            db.rollback()
            failed_run = (
                db.query(AutopilotRunModel)
                .filter(AutopilotRunModel.run_id == self.run_id)
                .first()
            )
            if failed_run is not None:
                failed_run.status = "FAILED"
                db.commit()
            try:
                self.log_decision(
                    db,
                    "AutopilotController",
                    "AUTOPILOT_FAILED",
                    f"{type(exc).__name__}: {exc}",
                )
            except Exception:
                db.rollback()
            return {
                "runId": self.run_id,
                "status": "FAILED",
                "errorType": type(exc).__name__,
            }
        finally:
            db.close()

    def pause_autopilot(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            run = db.query(AutopilotRunModel).filter(AutopilotRunModel.run_id == self.run_id).first()
            if run:
                run.status = "PAUSED"
                db.commit()
                self.log_decision(db, "AutopilotController", "PAUSE_AUTOPILOT", "Autopiloto pausado por orden del usuario.")
            return {"runId": self.run_id, "status": "PAUSED"}
        finally:
            db.close()

    def resume_autopilot(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            run = db.query(AutopilotRunModel).filter(AutopilotRunModel.run_id == self.run_id).first()
            if run:
                run.status = "RUNNING"
                db.commit()
                self.log_decision(db, "AutopilotController", "RESUME_AUTOPILOT", "Autopiloto reanudado.")
            return {"runId": self.run_id, "status": "RUNNING"}
        finally:
            db.close()

    def stop_autopilot(self) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            run = db.query(AutopilotRunModel).filter(AutopilotRunModel.run_id == self.run_id).first()
            if run:
                run.status = "STOPPED"
                db.commit()
                self.log_decision(db, "AutopilotController", "STOP_AUTOPILOT", "Autopiloto detenido.")
            return {"runId": self.run_id, "status": "STOPPED"}
        finally:
            db.close()
