from __future__ import annotations

import hashlib
import json
import os
import re
import time
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session

from services.api.app.bingx.client import BingXPyRestClient
from services.api.app.ingestion.eth_pipeline import (
    HistoricalIngestionError,
    build_eth_research_datasets,
)
from services.api.app.config import DATA_DIR
from services.api.app.db.database import (
    BacktestModel,
    CampaignEventModel,
    CampaignModel,
    CampaignTrialModel,
    DatasetModel,
    DB_PATH,
    InstrumentModel,
    RawIngestLogModel,
    ResearchSourceModel,
    SearchConfigModel,
    SearchLogModel,
    StrategyCompilationModel,
    StrategyModel,
    ValidationErrorLogModel,
    get_db,
    init_db,
)
from services.api.app.api.prop_firms import prop_firms_router
from services.api.app.api.sqx_router import sqx_router

router = APIRouter()
router.include_router(prop_firms_router)
router.include_router(sqx_router)

_INTERVAL_RE = re.compile(r"^(\d+)(m|h|d|w)$")


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _interval_ms(interval: str) -> int:
    match = _INTERVAL_RE.fullmatch(interval)
    if not match:
        raise HTTPException(status_code=422, detail=f"UNSUPPORTED_INTERVAL: {interval}")
    amount = int(match.group(1))
    unit = match.group(2)
    factors = {"m": 60_000, "h": 3_600_000, "d": 86_400_000, "w": 604_800_000}
    return amount * factors[unit]


def _nullable_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed == parsed and abs(parsed) != float("inf") else None


def _nullable_int(value: Any) -> int | None:
    if value in (None, ""):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
    except ValueError:
        return str(path.resolve()).replace("\\", "/")


def _data_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path(DATA_DIR).resolve())).replace("\\", "/")
    except ValueError:
        return _repo_relative(path)


def _write_atomic(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    temporary.replace(path)


def _save_raw_rest(
    *,
    endpoint: str,
    params: dict[str, Any],
    payload: Any,
    feed_path: Path,
    db: Session,
) -> tuple[Path, str, int]:
    received_ms = int(time.time() * 1000)
    envelope = {
        "venue": "BINGX",
        "endpoint": endpoint,
        "params": params,
        "receiveTimestamp": received_ms,
        "capturedAt": datetime.now(timezone.utc).isoformat(),
        "payload": payload,
    }
    raw_bytes = _canonical_json(envelope).encode("utf-8")
    raw_checksum = _sha256_bytes(raw_bytes)
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S-%fZ")
    raw_path = Path(DATA_DIR) / "raw" / "rest" / feed_path / f"{stamp}.json"
    _write_atomic(raw_path, raw_bytes)
    db.add(
        RawIngestLogModel(
            endpoint=endpoint,
            params_json=_canonical_json(params),
            raw_body_path=_repo_relative(raw_path),
            sha256_raw=raw_checksum,
            receive_time=received_ms,
            status_code=200,
            client_version="python-rest-v3",
            transformer_version="kline-normalizer-v2",
        )
    )
    return raw_path, raw_checksum, received_ms


def _validate_dataset_artifacts(ds: DatasetModel) -> list[str]:
    errors: list[str] = []
    file_path = Path(ds.file_path)
    manifest_path = Path(ds.manifest_path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path
    if not manifest_path.is_absolute():
        manifest_path = Path.cwd() / manifest_path
    if not file_path.exists():
        errors.append("NORMALIZED_FILE_MISSING")
        return errors
    if not manifest_path.exists():
        errors.append("MANIFEST_FILE_MISSING")
        return errors

    try:
        normalized_bytes = file_path.read_bytes()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = json.loads(normalized_bytes)
    except Exception as exc:
        return [f"ARTIFACT_PARSE_ERROR: {exc}"]

    if _sha256_bytes(normalized_bytes) != ds.checksum_sha256:
        errors.append("NORMALIZED_CHECKSUM_MISMATCH")
    if manifest.get("checksumSha256") != ds.checksum_sha256:
        errors.append("MANIFEST_CHECKSUM_MISMATCH")
    if manifest.get("recordCount") != len(records) or len(records) != ds.record_count:
        errors.append("RECORD_COUNT_MISMATCH")
    if not manifest.get("closedRecordsOnly"):
        errors.append("CLOSED_RECORDS_NOT_PROVEN")
    if not manifest.get("rawPath") or not manifest.get("rawChecksumSha256"):
        errors.append("RAW_CHAIN_MISSING")
    else:
        raw_ref = Path(str(manifest["rawPath"]).replace("\\", "/"))
        raw_path = (Path.cwd() / raw_ref) if raw_ref.parts and raw_ref.parts[0] == "data" else (Path(DATA_DIR) / raw_ref)
        if not raw_path.exists():
            errors.append("RAW_FILE_MISSING")
        elif _sha256_bytes(raw_path.read_bytes()) != manifest.get("rawChecksumSha256"):
            errors.append("RAW_CHECKSUM_MISMATCH")
    if ds.start_time < 1_000_000_000_000 or ds.end_time < 1_000_000_000_000:
        errors.append("TIMESTAMP_UNIT_NOT_MILLISECONDS")
    if ds.gap_count != 0 or ds.duplicate_count != 0:
        errors.append("DATA_QUALITY_ERRORS_PRESENT")
    # Verify normalized records are actually in order (independent of raw source ordering)
    if len(records) >= 2:
        for i in range(len(records) - 1):
            if records[i]["time"] >= records[i + 1]["time"]:
                errors.append("NORMALIZED_ORDER_VIOLATION")
                break
    return errors


@router.get("/status")
def get_system_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    started = time.perf_counter()
    contracts_count = 0
    bingx_status = "OFFLINE"
    bingx_error: str | None = None
    try:
        contracts = BingXPyRestClient().get_contracts()
        contracts_count = len(contracts) if isinstance(contracts, list) else 0
        bingx_status = "ONLINE"
    except Exception as exc:
        bingx_error = str(exc)

    sqlite_status = "WAL_ACTIVE" if Path(DB_PATH).exists() else "OFFLINE"
    return {
        "status": "ONLINE" if sqlite_status == "WAL_ACTIVE" else "DEGRADED",
        "mode": "LOCAL_REAL_ONLY",
        "venue": "BINGX",
        "timestamp": int(time.time() * 1000),
        "sqlite_status": sqlite_status,
        "sqlite_path": str(DB_PATH),
        "bingx_status": bingx_status,
        "bingx_error": bingx_error,
        "latency_ms": int((time.perf_counter() - started) * 1000),
        "contracts_count": contracts_count,
        "datasets_count": db.query(DatasetModel).count(),
        "approved_datasets": db.query(DatasetModel).filter(DatasetModel.status == "APPROVED").count(),
        "strategies_count": db.query(StrategyModel).count(),
        "backtests_count": db.query(BacktestModel).count(),
        "campaigns_count": db.query(CampaignModel).count(),
        "account_status": (
            "CREDENTIALS_CONFIGURED_NOT_PROBED"
            if os.getenv("BINGX_API_KEY") and os.getenv("BINGX_SECRET_KEY")
            else "NOT_CONFIGURED"
        ),
    }


@router.get("/modules")
def get_modules_status(db: Session = Depends(get_db)) -> dict[str, Any]:
    completed = db.query(BacktestModel).filter(BacktestModel.status == "COMPLETED").count()
    return {
        "command_center": {"status": "ACTIVE", "detail": "FastAPI local + SQLite WAL"},
        "data_pipeline": {
            "status": "ACTIVE",
            "total_datasets": db.query(DatasetModel).count(),
            "approved_datasets": db.query(DatasetModel).filter(DatasetModel.status == "APPROVED").count(),
            "validating_datasets": db.query(DatasetModel).filter(DatasetModel.status == "VALIDATING").count(),
        },
        "strategy_lab": {
            "status": "REGISTRY_ONLY",
            "detail": "Persistencia disponible; compilador DSL pendiente",
            "strategies_stored": db.query(StrategyModel).count(),
        },
        "backtester": {
            "status": "ENGINE_NOT_IMPLEMENTED",
            "detail": "No existe todavía un ejecutor de backtests",
            "backtests_completed": completed,
        },
        "campaigns": {
            "status": "ORCHESTRATOR_NOT_IMPLEMENTED",
            "detail": "No existe todavía ProcessPoolExecutor ni motor evolutivo",
            "campaigns_total": db.query(CampaignModel).count(),
        },
        "leaderboard": {
            "status": "AWAITING_VERIFIED_BACKTESTS",
            "audited_entries": 0,
        },
        "research": {
            "status": "REGISTRY_ONLY",
            "detail": "Registro manual trazable; recuperación automática pendiente",
            "sources_registered": db.query(ResearchSourceModel).count(),
        },
    }


@router.get("/instruments")
def list_instruments(db: Session = Depends(get_db)):
    instruments = db.query(InstrumentModel).all()
    if not instruments:
        contracts = BingXPyRestClient().get_contracts()
        for contract in contracts:
            symbol = contract.get("symbol")
            if not symbol:
                continue
            db.merge(
                InstrumentModel(
                    symbol=symbol,
                    asset=contract.get("asset"),
                    currency=contract.get("currency"),
                    maker_fee_rate=_nullable_float(contract.get("makerFeeRate")),
                    taker_fee_rate=_nullable_float(contract.get("takerFeeRate") or contract.get("feeRate")),
                    price_precision=_nullable_int(contract.get("pricePrecision")),
                    quantity_precision=_nullable_int(contract.get("quantityPrecision")),
                    trade_min_quantity=_nullable_float(contract.get("tradeMinQuantity")),
                    trade_min_usdt=_nullable_float(contract.get("tradeMinUSDT")),
                    status=_nullable_int(contract.get("status")) or 0,
                )
            )
        db.commit()
        instruments = db.query(InstrumentModel).all()
    return [
        {
            "symbol": item.symbol,
            "asset": item.asset,
            "currency": item.currency,
            "makerFeeRate": item.maker_fee_rate,
            "takerFeeRate": item.taker_fee_rate,
            "pricePrecision": item.price_precision,
            "quantityPrecision": item.quantity_precision,
            "tradeMinQuantity": item.trade_min_quantity,
            "tradeMinUSDT": item.trade_min_usdt,
            "status": item.status,
        }
        for item in instruments
    ]


@router.get("/datasets")
def list_datasets(db: Session = Depends(get_db)):
    datasets = db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).all()
    return [
        {
            "datasetId": d.dataset_id,
            "venue": d.venue,
            "symbol": d.symbol,
            "feedType": d.feed_type,
            "interval": d.interval,
            "startTime": d.start_time,
            "endTime": d.end_time,
            "recordCount": d.record_count,
            "gapCount": d.gap_count,
            "duplicateCount": d.duplicate_count,
            "outOfOrderCount": d.out_of_order_count,
            "coveragePct": d.coverage_pct,
            "checksumSha256": d.checksum_sha256,
            "status": d.status,
            "filePath": d.file_path,
            "manifestPath": d.manifest_path,
            "createdAt": d.created_at.isoformat() if d.created_at else None,
        }
        for d in datasets
    ]


@router.post("/datasets/{dataset_id}/approve")
def approve_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(DatasetModel).filter(DatasetModel.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="DATASET_NOT_FOUND")
    errors = _validate_dataset_artifacts(ds)
    if errors:
        ds.status = "REJECTED"
        db.commit()
        raise HTTPException(status_code=422, detail={"code": "DATASET_VALIDATION_FAILED", "errors": errors})
    ds.status = "APPROVED"
    db.commit()
    return {"status": "SUCCESS", "dataset_id": dataset_id, "new_status": "APPROVED"}


@router.post("/datasets/{dataset_id}/reject")
def reject_dataset(dataset_id: str, db: Session = Depends(get_db)):
    ds = db.query(DatasetModel).filter(DatasetModel.dataset_id == dataset_id).first()
    if not ds:
        raise HTTPException(status_code=404, detail="DATASET_NOT_FOUND")
    ds.status = "REJECTED"
    db.commit()
    return {"status": "SUCCESS", "dataset_id": dataset_id, "new_status": "REJECTED"}


@router.post("/ingestion/backfill")
def trigger_backfill(
    symbol: str = Query("ETH-USDT", min_length=3, max_length=40),
    interval: str = Query("1h"),
    limit: int = Query(1000, ge=10, le=1000),
    db: Session = Depends(get_db),
):
    step_ms = _interval_ms(interval)
    endpoint = "/openApi/swap/v3/quote/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    raw_klines = BingXPyRestClient().get_klines(symbol, interval, limit=limit)
    if not raw_klines:
        raise HTTPException(status_code=404, detail="NO_KLINES_RETURNED")

    raw_path, raw_checksum, received_ms = _save_raw_rest(
        endpoint=endpoint,
        params=params,
        payload=raw_klines,
        feed_path=Path("klines") / symbol / interval,
        db=db,
    )

    source_times = [int(item.get("time", 0)) for item in raw_klines if item.get("time") is not None]
    out_of_order_count = sum(1 for a, b in zip(source_times, source_times[1:]) if b < a)
    mapped: list[dict[str, float | int]] = []
    for item in raw_klines:
        try:
            candle_time = int(item["time"])
            candle = {
                "time": candle_time,
                "open": float(item["open"]),
                "high": float(item["high"]),
                "low": float(item["low"]),
                "close": float(item["close"]),
                "volume": float(item["volume"]),
            }
        except (KeyError, TypeError, ValueError):
            continue
        if candle_time + step_ms <= received_ms:
            mapped.append(candle)

    mapped.sort(key=lambda item: int(item["time"]))
    seen: set[int] = set()
    duplicate_count = 0
    normalized: list[dict[str, float | int]] = []
    for candle in mapped:
        candle_time = int(candle["time"])
        if candle_time in seen:
            duplicate_count += 1
            continue
        seen.add(candle_time)
        normalized.append(candle)
    if not normalized:
        raise HTTPException(status_code=422, detail="NO_CLOSED_KLINES")

    gap_count = sum(
        1
        for previous, current in zip(normalized, normalized[1:])
        if int(current["time"]) - int(previous["time"]) != step_ms
    )
    expected_records = ((int(normalized[-1]["time"]) - int(normalized[0]["time"])) // step_ms) + 1
    coverage_pct = round((len(normalized) / expected_records) * 100, 8) if expected_records > 0 else 0.0

    normalized_bytes = _canonical_json(normalized).encode("utf-8")
    checksum = _sha256_bytes(normalized_bytes)
    first = int(normalized[0]["time"])
    last = int(normalized[-1]["time"])
    dataset_id = f"ds_bingx_{symbol.replace('-', '_')}_{interval}_{first}_{last}_{checksum[:10]}"
    normalized_path = Path(DATA_DIR) / "normalized" / f"{dataset_id}.json"
    manifest_path = Path(DATA_DIR) / "normalized" / f"{dataset_id}_manifest.json"
    _write_atomic(normalized_path, normalized_bytes)

    manifest = {
        "datasetId": dataset_id,
        "venue": "BINGX",
        "symbol": symbol,
        "feedType": f"kline_{interval}",
        "interval": interval,
        "timestampUnit": "milliseconds",
        "startTime": first,
        "endTime": last,
        "recordCount": len(normalized),
        "gapCount": gap_count,
        "duplicateCount": duplicate_count,
        "outOfOrderCount": out_of_order_count,
        "coveragePct": coverage_pct,
        "checksumSha256": checksum,
        "rawChecksumSha256": raw_checksum,
        "rawPath": _data_relative(raw_path),
        "normalizedPath": _data_relative(normalized_path),
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "closedRecordsOnly": True,
        "completeHistory": False,
        "request": params,
    }
    _write_atomic(manifest_path, json.dumps(manifest, indent=2, ensure_ascii=False).encode("utf-8"))

    db.merge(
        DatasetModel(
            dataset_id=dataset_id,
            venue="BINGX",
            symbol=symbol,
            feed_type=f"kline_{interval}",
            interval=interval,
            start_time=first,
            end_time=last,
            record_count=len(normalized),
            gap_count=gap_count,
            duplicate_count=duplicate_count,
            out_of_order_count=out_of_order_count,
            coverage_pct=coverage_pct,
            checksum_sha256=checksum,
            status="VALIDATING",
            file_path=_repo_relative(normalized_path),
            manifest_path=_repo_relative(manifest_path),
        )
    )
    db.commit()
    return {
        "status": "SUCCESS",
        "dataset_id": dataset_id,
        "record_count": len(normalized),
        "checksum": checksum,
        "validation_status": "VALIDATING",
        "complete_history": False,
        "message": "Backfill de una sola página. Requiere validación y aprobación explícita.",
    }


@router.post("/ingestion/eth-research")
def trigger_eth_research_ingestion(
    days: int = Query(160, ge=3, le=610),
    db: Session = Depends(get_db),
):
    """Build the approved ETH research universe from one real BingX 1m window."""
    try:
        return build_eth_research_datasets(db, days=days)
    except HistoricalIngestionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=422,
            detail={"code": "ETH_RESEARCH_INGESTION_FAILED", "message": str(exc)},
        ) from exc


@router.get("/strategies")
def list_strategies(db: Session = Depends(get_db)):
    strategies = db.query(StrategyModel).order_by(StrategyModel.created_at.desc()).all()
    return [
        {
            "strategyId": s.strategy_id,
            "name": s.name,
            "version": s.version,
            "family": s.family,
            "author": s.author,
            "canonicalHash": s.canonical_hash,
            "parentId": s.parent_id,
            "generation": s.generation,
            "seed": s.seed,
            "dslJson": s.dsl_json,
            "validationStatus": "REGISTRY_ONLY_NOT_COMPILED",
            "createdAt": s.created_at.isoformat() if s.created_at else None,
        }
        for s in strategies
    ]


@router.post("/strategies")
def create_strategy(data: dict[str, Any], db: Session = Depends(get_db)):
    if not data.get("name") or "dsl" not in data:
        raise HTTPException(status_code=422, detail="NAME_AND_DSL_REQUIRED")
    dsl = data["dsl"]
    if not isinstance(dsl, dict):
        raise HTTPException(status_code=422, detail="DSL_MUST_BE_OBJECT")
    dsl_json = _canonical_json(dsl)
    canonical_hash = _sha256_bytes(dsl_json.encode("utf-8"))
    strategy_id = f"strat_{canonical_hash[:16]}"
    db.merge(
        StrategyModel(
            strategy_id=strategy_id,
            name=str(data["name"]),
            version=str(data.get("version", "0.0.0-draft")),
            family=str(data.get("family", "unclassified")),
            author=str(data.get("author", "User")),
            canonical_hash=canonical_hash,
            parent_id=data.get("parentId"),
            generation=int(data.get("generation", 0)),
            seed=data.get("seed"),
            dsl_json=dsl_json,
        )
    )
    db.commit()
    return {
        "status": "SUCCESS",
        "strategy_id": strategy_id,
        "canonical_hash": canonical_hash,
        "validation_status": "REGISTRY_ONLY_NOT_COMPILED",
    }


@router.get("/backtests")
def list_backtests(db: Session = Depends(get_db)):
    rows = db.query(BacktestModel).order_by(BacktestModel.created_at.desc()).all()
    return [
        {
            "backtestId": b.backtest_id,
            "strategyId": b.strategy_id,
            "datasetId": b.dataset_id,
            "engineType": b.engine_type,
            "initialCapital": b.initial_capital,
            "leverage": b.leverage,
            "finalEquity": b.final_equity,
            "netReturnPct": b.net_return_pct,
            "maxDrawdownPct": b.max_drawdown_pct,
            "winRate": b.win_rate,
            "tradesCount": b.trades_count,
            "profitFactor": b.profit_factor,
            "checksum": b.checksum,
            "status": b.status,
            "createdAt": b.created_at.isoformat() if b.created_at else None,
        }
        for b in rows
    ]


@router.get("/rentables")
def get_rentable_strategies(limit: int = 10):
    """Proxy rentable strategies from SQX router."""
    from services.api.app.api.sqx_router import rentable_sqx_strategies
    return rentable_sqx_strategies(limit=limit)


@router.get("/leaderboard")
def get_leaderboard(db: Session = Depends(get_db)):
    candidates = (
        db.query(BacktestModel)
        .filter(BacktestModel.status == "COMPLETED")
        .order_by(BacktestModel.net_return_pct.desc())
        .all()
    )
    verified: list[BacktestModel] = []
    for candidate in candidates:
        if not candidate.checksum or not candidate.ledger_path or not candidate.artifacts_path:
            continue
        if not Path(candidate.ledger_path).exists() or not Path(candidate.artifacts_path).exists():
            continue
        verified.append(candidate)
    return [
        {
            "rank": index + 1,
            "backtestId": b.backtest_id,
            "strategyId": b.strategy_id,
            "engine": b.engine_type,
            "returnPct": b.net_return_pct,
            "maxDrawdownPct": b.max_drawdown_pct,
            "winRate": b.win_rate,
            "tradesCount": b.trades_count,
            "profitFactor": b.profit_factor,
            "checksum": b.checksum,
            "date": b.created_at.isoformat() if b.created_at else None,
        }
        for index, b in enumerate(verified)
    ]


@router.get("/campaigns")
def list_campaigns(db: Session = Depends(get_db)):
    campaigns = db.query(CampaignModel).order_by(CampaignModel.created_at.desc()).all()
    return [
        {
            "campaignId": c.campaign_id,
            "name": c.name,
            "symbol": c.symbol,
            "interval": c.interval,
            "populationSize": c.population_size,
            "generationsCount": c.generations_count,
            "currentGeneration": c.current_generation,
            "seed": c.seed,
            "status": c.status,
            "createdAt": c.created_at.isoformat() if c.created_at else None,
        }
        for c in campaigns
    ]


@router.get("/search-configs")
def list_search_configs(db: Session = Depends(get_db)):
    configs = db.query(SearchConfigModel).order_by(SearchConfigModel.created_at.desc()).all()
    return [
        {
            "configId": c.config_id,
            "name": c.name,
            "mode": c.mode,
            "project": c.project,
            "databank": c.databank,
            "symbol": c.symbol,
            "interval": c.interval,
            "population": c.population,
            "targetMultiplier": c.target_multiplier,
            "maxDrawdownPct": c.max_drawdown_pct,
            "consistencyTarget": c.consistency_target,
            "techniques": json.loads(c.techniques_json) if c.techniques_json else [],
            "createdAt": c.created_at.isoformat() if c.created_at else None,
        }
        for c in configs
    ]


@router.post("/search-configs")
def create_search_config(payload: dict[str, Any], db: Session = Depends(get_db)) -> dict[str, Any]:
    mode = str(payload.get("mode", "ultra")).lower()
    if mode not in {"ultra", "fondeo"}:
        raise HTTPException(status_code=422, detail="MODE_MUST_BE_ULTRA_OR_FONDEO")
    project = str(payload.get("project", "Ultra_Auto_Pilot")).strip() or "Ultra_Auto_Pilot"
    databank = str(payload.get("databank", "Results")).strip() or "Results"
    symbol = payload.get("symbol")
    interval = payload.get("interval")
    population = _nullable_int(payload.get("population"))
    target_multiplier = _nullable_float(payload.get("targetMultiplier"))
    max_drawdown_pct = _nullable_float(payload.get("maxDrawdownPct"))
    consistency_target = _nullable_float(payload.get("consistencyTarget"))
    techniques = payload.get("techniques") or []
    if not isinstance(techniques, list):
        raise HTTPException(status_code=422, detail="TECHNIQUES_MUST_BE_A_LIST")
    config_id = f"cfg_{hashlib.sha256(_canonical_json(payload).encode('utf-8')).hexdigest()[:12]}"
    db.merge(
        SearchConfigModel(
            config_id=config_id,
            name=str(payload.get("name", "default")).strip() or "default",
            mode=mode,
            project=project,
            databank=databank,
            symbol=str(symbol) if symbol is not None else None,
            interval=str(interval) if interval is not None else None,
            population=population,
            target_multiplier=target_multiplier,
            max_drawdown_pct=max_drawdown_pct,
            consistency_target=consistency_target,
            techniques_json=json.dumps(techniques, ensure_ascii=False),
        )
    )
    db.commit()
    return {
        "status": "SUCCESS",
        "configId": config_id,
        "mode": mode,
        "project": project,
        "databank": databank,
    }


@router.post("/search-configs/{config_id}/run")
def run_search_config(config_id: str, db: Session = Depends(get_db)) -> dict[str, Any]:
    config = db.query(SearchConfigModel).filter(SearchConfigModel.config_id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="SEARCH_CONFIG_NOT_FOUND")
    return {
        "status": "QUEUED",
        "configId": config_id,
        "mode": config.mode,
        "project": config.project,
        "databank": config.databank,
        "message": "Config ready. Call SQX run/ingest/rentable with this mode-aware setup.",
    }


@router.get("/research")
def list_research_sources(db: Session = Depends(get_db)):
    sources = db.query(ResearchSourceModel).order_by(ResearchSourceModel.created_at.desc()).all()
    return [
        {
            "sourceId": s.source_id,
            "title": s.title,
            "url": s.url,
            "author": s.author,
            "fetchDate": s.fetch_date.isoformat() if s.fetch_date else None,
            "sha256Hash": s.sha256_hash,
            "licenseInfo": s.license_info,
            "hypothesisText": s.hypothesis_text,
            "associatedBacktestId": s.associated_backtest_id,
            "createdAt": s.created_at.isoformat() if s.created_at else None,
        }
        for s in sources
    ]


@router.post("/research")
def create_research_source(data: dict[str, Any], db: Session = Depends(get_db)):
    title = str(data.get("title", "")).strip()
    url = str(data.get("url", "")).strip()
    content = str(data.get("content", "")).strip()
    hypothesis = str(data.get("hypothesisText", "")).strip()
    if not title or not url or not content or not hypothesis:
        raise HTTPException(status_code=422, detail="TITLE_URL_SOURCE_CONTENT_AND_HYPOTHESIS_REQUIRED")
    canonical_source = _canonical_json({"url": url, "content": content})
    sha256_hash = _sha256_bytes(canonical_source.encode("utf-8"))
    source_id = f"src_{sha256_hash[:16]}"
    db.merge(
        ResearchSourceModel(
            source_id=source_id,
            title=title,
            url=url,
            author=(str(data.get("author", "")).strip() or None),
            raw_content=content,
            sha256_hash=sha256_hash,
            license_info=(str(data.get("licenseInfo", "")).strip() or None),
            hypothesis_text=hypothesis,
            associated_backtest_id=data.get("associatedBacktestId"),
        )
    )
    db.commit()
    return {"status": "SUCCESS", "source_id": source_id, "sha256_hash": sha256_hash}


# ─── DSL Phase D Endpoints ───────────────────────────────────────────────────

from services.api.app.dsl.engine import (
    StrategyDSL,
    canonical_hash as dsl_canonical_hash,
    canonical_json as dsl_canonical_json,
    validate_semantics,
    compile_to_ir,
    extract_required_series,
    extract_max_lookback,
    SeriesName,
    COMPARISON_OPS,
    LOGIC_OPS,
    TIMEFRAMES,
    IndicatorName,
    DSL_VERSION,
    COMPILER_VERSION,
)
from pydantic import ValidationError as PydanticValidationError


@router.get("/dsl/schema")
def get_dsl_schema():
    """Return the JSON Schema for DSL v1.0.0."""
    schema_path = Path(__file__).resolve().parents[4] / "schemas" / "dsl_v1_strategy.json"
    if schema_path.exists():
        return json.loads(schema_path.read_text(encoding="utf-8"))
    return {"error": "SCHEMA_FILE_NOT_FOUND", "path": str(schema_path)}


@router.get("/dsl/operators")
def get_dsl_operators():
    """Return all available operators, series, indicators, and timeframes."""
    return {
        "dslVersion": DSL_VERSION,
        "comparisonOps": list(COMPARISON_OPS),
        "logicOps": list(LOGIC_OPS),
        "series": [s.value for s in SeriesName],
        "indicators": [i.value for i in IndicatorName],
        "timeframes": list(TIMEFRAMES),
        "families": ["breakout", "mean_reversion", "trend_following", "momentum", "volatility", "statistical_arbitrage"],
        "origins": ["MANUAL", "RESEARCH", "MUTATION", "CROSSOVER"],
        "marginModes": ["ISOLATED", "CROSS"],
        "orderTypes": ["MARKET", "LIMIT"],
    }


@router.post("/strategies/validate")
def validate_strategy(data: dict[str, Any], db: Session = Depends(get_db)):
    """Structural and semantic validation of a DSL strategy without saving."""
    dsl_input = data.get("dsl", data)

    # Step 1: Structural validation (Pydantic)
    structural_errors: list[dict[str, str]] = []
    try:
        parsed = StrategyDSL(**dsl_input)
    except PydanticValidationError as exc:
        for error in exc.errors():
            structural_errors.append({
                "code": "STRUCTURAL_VALIDATION_ERROR",
                "path": ".".join(str(p) for p in error["loc"]),
                "message": error["msg"],
            })
        return {
            "valid": False,
            "structurallyValid": False,
            "semanticallyValid": False,
            "errors": structural_errors,
        }

    # Step 2: Semantic validation (against real catalog)
    available_symbols: set[str] = set()
    instruments = db.query(InstrumentModel).all()
    for inst in instruments:
        available_symbols.add(inst.symbol)

    semantic_errors = validate_semantics(
        parsed,
        available_symbols=available_symbols if available_symbols else None,
        available_series=set(SeriesName),  # all series structurally valid; actual availability checked at backtest time
    )

    return {
        "valid": len(semantic_errors) == 0,
        "structurallyValid": True,
        "semanticallyValid": len(semantic_errors) == 0,
        "canonicalHash": dsl_canonical_hash(parsed),
        "requiredSeries": sorted([s.value for s in extract_required_series(parsed)]),
        "maxLookback": extract_max_lookback(parsed),
        "errors": [e.model_dump() for e in semantic_errors],
    }


@router.post("/strategies/{strategy_id}/compile")
def compile_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Compile a stored strategy to IR. Requires structural + semantic validity."""
    strat = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="STRATEGY_NOT_FOUND")

    try:
        dsl_dict = json.loads(strat.dsl_json)
        parsed = StrategyDSL(**dsl_dict)
    except (PydanticValidationError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"STRATEGY_STRUCTURALLY_INVALID: {exc}")

    # Semantic check
    available_symbols: set[str] = {inst.symbol for inst in db.query(InstrumentModel).all()}
    semantic_errors = validate_semantics(
        parsed,
        available_symbols=available_symbols if available_symbols else None,
        available_series=set(SeriesName),
    )
    if semantic_errors:
        raise HTTPException(status_code=422, detail={
            "code": "SEMANTIC_VALIDATION_FAILED",
            "errors": [e.model_dump() for e in semantic_errors],
        })

    # Compile
    ir = compile_to_ir(parsed)
    ir_json = dsl_canonical_json(ir.model_dump(mode="json"))

    # Save compilation artifact
    artifact_path = Path(DATA_DIR) / "artifacts" / "compilations" / f"{strategy_id}_{ir.irHash[:12]}.json"
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(ir_json, encoding="utf-8")

    # Persist compilation entry and update strategy status
    compilation_id = f"cmp_{ir.irHash[:16]}"
    db.merge(
        StrategyCompilationModel(
            compilation_id=compilation_id,
            strategy_id=strategy_id,
            dsl_hash=ir.dslHash,
            ir_hash=ir.irHash,
            compiler_version=ir.compilerVersion,
            dsl_version=ir.dslVersion,
            instruction_count=len(ir.instructions),
            max_lookback=ir.maxLookback,
            required_series_json=json.dumps(ir.requiredSeries),
            artifact_path=_repo_relative(artifact_path),
        )
    )
    strat.validation_status = "COMPILED"
    db.commit()

    return {
        "status": "COMPILED",
        "strategy_id": strategy_id,
        "compilation_id": compilation_id,
        "dslHash": ir.dslHash,
        "irHash": ir.irHash,
        "compilerVersion": ir.compilerVersion,
        "dslVersion": ir.dslVersion,
        "instructionCount": len(ir.instructions),
        "requiredSeries": ir.requiredSeries,
        "maxLookback": ir.maxLookback,
        "artifactPath": _repo_relative(artifact_path),
    }


@router.get("/strategies/{strategy_id}")
def get_strategy(strategy_id: str, db: Session = Depends(get_db)):
    """Get a single strategy with full details."""
    strat = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="STRATEGY_NOT_FOUND")

    validation_status = "REGISTRY_ONLY_NOT_COMPILED"
    try:
        dsl_dict = json.loads(strat.dsl_json)
        parsed = StrategyDSL(**dsl_dict)
        validation_status = "STRUCTURALLY_VALID"
        errors = validate_semantics(parsed, available_series=set(SeriesName))
        if not errors:
            validation_status = "SEMANTICALLY_VALID"
        # Check if compilation artifact exists
        compilations_dir = Path(DATA_DIR) / "artifacts" / "compilations"
        if compilations_dir.exists():
            compiled_files = list(compilations_dir.glob(f"{strategy_id}_*.json"))
            if compiled_files:
                validation_status = "COMPILED"
    except Exception:
        validation_status = "PARSE_ERROR"

    return {
        "strategyId": strat.strategy_id,
        "name": strat.name,
        "version": strat.version,
        "family": strat.family,
        "author": strat.author,
        "canonicalHash": strat.canonical_hash,
        "parentId": strat.parent_id,
        "generation": strat.generation,
        "seed": strat.seed,
        "dslJson": strat.dsl_json,
        "validationStatus": validation_status,
        "createdAt": strat.created_at.isoformat() if strat.created_at else None,
    }


@router.get("/strategies/{strategy_id}/compilations")
def get_strategy_compilations(strategy_id: str):
    """List all compilation artifacts for a strategy."""
    compilations_dir = Path(DATA_DIR) / "artifacts" / "compilations"
    if not compilations_dir.exists():
        return []
    compiled_files = sorted(compilations_dir.glob(f"{strategy_id}_*.json"))
    results = []
    for f in compiled_files:
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            results.append({
                "irHash": data.get("irHash"),
                "dslHash": data.get("dslHash"),
                "compilerVersion": data.get("compilerVersion"),
                "dslVersion": data.get("dslVersion"),
                "instructionCount": len(data.get("instructions", [])),
                "artifactPath": str(f),
            })
        except Exception:
            continue
    return results


# ─── Fast Engine Endpoints (Phase E) ─────────────────────────────────────────

from services.api.app.engine.fast_engine import FastEngine, FastEngineException


@router.post("/backtests/fast")
def run_fast_backtest(data: dict[str, Any], db: Session = Depends(get_db)):
    """Run a deterministic fast backtest on an APPROVED dataset using compiled IR."""
    strategy_id = data.get("strategyId")
    dataset_id = data.get("datasetId")
    initial_capital = float(data.get("initialCapital", 10000.0))

    if not strategy_id or not dataset_id:
        raise HTTPException(status_code=422, detail="STRATEGY_ID_AND_DATASET_ID_REQUIRED")

    strat = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="STRATEGY_NOT_FOUND")

    try:
        dsl_dict = json.loads(strat.dsl_json)
        parsed_dsl = StrategyDSL(**dsl_dict)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"STRATEGY_PARSE_ERROR: {exc}")

    # Find latest compilation for strategy
    compilations_dir = Path(DATA_DIR) / "artifacts" / "compilations"
    compiled_files = sorted(compilations_dir.glob(f"{strategy_id}_*.json")) if compilations_dir.exists() else []
    if not compiled_files:
        # Auto-compile on demand
        try:
            compiled_ir = compile_to_ir(parsed_dsl)
        except Exception as exc:
            raise HTTPException(status_code=422, detail=f"COMPILATION_FAILED: {exc}")
    else:
        try:
            ir_dict = json.loads(compiled_files[-1].read_text(encoding="utf-8"))
            compiled_ir = CompiledIR(**ir_dict)
        except Exception:
            compiled_ir = compile_to_ir(parsed_dsl)

    engine = FastEngine(db)
    try:
        result = engine.execute(
            strategy_dsl=parsed_dsl,
            compiled_ir=compiled_ir,
            dataset_id=dataset_id,
            initial_capital=initial_capital,
            persist_artifacts=bool(data.get("persistArtifacts", False)),
        )
        return result
    except FastEngineException as exc:
        raise HTTPException(status_code=422, detail={"code": exc.code, "message": exc.message})


@router.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str, db: Session = Depends(get_db)):
    """Get single backtest details."""
    b = db.query(BacktestModel).filter(BacktestModel.backtest_id == backtest_id).first()
    if not b:
        raise HTTPException(status_code=404, detail="BACKTEST_NOT_FOUND")
    return {
        "backtestId": b.backtest_id,
        "strategyId": b.strategy_id,
        "datasetId": b.dataset_id,
        "engineType": b.engine_type,
        "initialCapital": b.initial_capital,
        "leverage": b.leverage,
        "finalEquity": b.final_equity,
        "netReturnPct": b.net_return_pct,
        "maxDrawdownPct": b.max_drawdown_pct,
        "winRate": b.win_rate,
        "tradesCount": b.trades_count,
        "profitFactor": b.profit_factor,
        "checksum": b.checksum,
        "status": b.status,
        "ledgerPath": b.ledger_path,
        "createdAt": b.created_at.isoformat() if b.created_at else None,
    }


@router.get("/backtests/{backtest_id}/trades")
def get_backtest_trades(backtest_id: str, db: Session = Depends(get_db)):
    """Get trades ledger for a backtest."""
    b = db.query(BacktestModel).filter(BacktestModel.backtest_id == backtest_id).first()
    if not b or not b.ledger_path or not Path(b.ledger_path).exists():
        raise HTTPException(status_code=404, detail="BACKTEST_LEDGER_NOT_FOUND")
    data = json.loads(Path(b.ledger_path).read_text(encoding="utf-8"))
    return data.get("trades", [])


@router.get("/backtests/{backtest_id}/equity")
def get_backtest_equity(backtest_id: str, db: Session = Depends(get_db)):
    """Get equity curve for a backtest."""
    b = db.query(BacktestModel).filter(BacktestModel.backtest_id == backtest_id).first()
    if not b or not b.ledger_path or not Path(b.ledger_path).exists():
        raise HTTPException(status_code=404, detail="BACKTEST_LEDGER_NOT_FOUND")
    data = json.loads(Path(b.ledger_path).read_text(encoding="utf-8"))
    return data.get("equityCurve", [])


@router.get("/backtests/{backtest_id}/artifacts")
def get_backtest_artifacts(backtest_id: str, db: Session = Depends(get_db)):
    """Get full raw artifact payload and checksum for a backtest."""
    b = db.query(BacktestModel).filter(BacktestModel.backtest_id == backtest_id).first()
    if not b or not b.ledger_path or not Path(b.ledger_path).exists():
        raise HTTPException(status_code=404, detail="BACKTEST_ARTIFACTS_NOT_FOUND")
    return json.loads(Path(b.ledger_path).read_text(encoding="utf-8"))


@router.post("/backtests/{backtest_id}/reproduce")
def reproduce_backtest(backtest_id: str, db: Session = Depends(get_db)):
    """Reproduce backtest and verify identical checksum."""
    b = db.query(BacktestModel).filter(BacktestModel.backtest_id == backtest_id).first()
    if not b or not b.ledger_path or not Path(b.ledger_path).exists():
        raise HTTPException(status_code=404, detail="BACKTEST_NOT_FOUND")

    orig_data = json.loads(Path(b.ledger_path).read_text(encoding="utf-8"))
    orig_checksum = orig_data.get("checksum")

    strat_id = b.strategy_id
    ds_id = b.dataset_id

    # Re-run execution
    res = run_fast_backtest({"strategyId": strat_id, "datasetId": ds_id, "initialCapital": b.initial_capital}, db)
    new_checksum = res.get("checksum")

    reproducible = (orig_checksum == new_checksum)
    return {
        "backtestId": backtest_id,
        "reproducible": reproducible,
        "originalChecksum": orig_checksum,
        "reproducedChecksum": new_checksum,
    }


# ─── Autonomous Factory Campaign Endpoints (Phase F) ─────────────────────────

from services.api.app.factory.orchestrator import AutonomousCampaignOrchestrator


@router.post("/campaigns/autonomous")
def create_autonomous_campaign(data: dict[str, Any], db: Session = Depends(get_db)):
    """Create a new autonomous search campaign (Autopilot)."""
    symbol = str(data.get("symbol", "ETH-USDT")).upper()
    if symbol == "AUTO":
        symbol = "ETH-USDT"

    interval = str(data.get("interval", "1h"))
    if interval == "AUTO":
        interval = "1h"

    population_size = int(data.get("populationSize", 10))
    generations_count = int(data.get("generationsCount", 3))
    seed = int(data.get("seed", 42))
    mode = str(data.get("mode", "EXPLORE"))
    target_multiplier = float(data.get("targetMultiplier", 11.0))

    campaign_id = f"cmp_auto_{symbol.replace('-', '_')}_{int(time.time())}"

    db.merge(
        CampaignModel(
            campaign_id=campaign_id,
            name=f"Autopilot {symbol} {interval}",
            symbol=symbol,
            interval=interval,
            population_size=population_size,
            generations_count=generations_count,
            current_generation=0,
            seed=seed,
            status="CREATED",
            mode=mode,
            target_multiplier=target_multiplier,
        )
    )
    db.add(
        CampaignEventModel(
            campaign_id=campaign_id,
            event_type="CAMPAIGN_CREATED",
            message=f"Campaign created: {symbol} {interval}, target {target_multiplier}x",
        )
    )
    db.commit()

    return {
        "status": "SUCCESS",
        "campaignId": campaign_id,
        "name": f"Autopilot {symbol} {interval}",
        "symbol": symbol,
        "interval": interval,
        "populationSize": population_size,
        "generationsCount": generations_count,
        "mode": mode,
        "targetMultiplier": target_multiplier,
        "campaignStatus": "CREATED",
    }


@router.post("/campaigns/{campaign_id}/start")
def start_autonomous_campaign(campaign_id: str, db: Session = Depends(get_db)):
    """Run an autonomous campaign search cycle."""
    c = db.query(CampaignModel).filter(CampaignModel.campaign_id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CAMPAIGN_NOT_FOUND")

    orchestrator = AutonomousCampaignOrchestrator(campaign_id)
    res = orchestrator.run_generation_cycle(
        symbol=c.symbol,
        timeframe=c.interval,
        population_size=c.population_size,
        generations_count=c.generations_count,
        seed=c.seed,
        mode=c.mode or "EXPLORE",
        target_multiplier=c.target_multiplier or 11.0,
    )
    return res


@router.post("/campaigns/{campaign_id}/pause")
def pause_campaign(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(CampaignModel).filter(CampaignModel.campaign_id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CAMPAIGN_NOT_FOUND")
    c.status = "PAUSED"
    db.commit()
    return {"status": "SUCCESS", "campaignId": campaign_id, "newStatus": "PAUSED"}


@router.post("/campaigns/{campaign_id}/resume")
def resume_campaign(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(CampaignModel).filter(CampaignModel.campaign_id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CAMPAIGN_NOT_FOUND")
    c.status = "FAST_EVALUATING"
    db.commit()
    return {"status": "SUCCESS", "campaignId": campaign_id, "newStatus": "FAST_EVALUATING"}


@router.post("/campaigns/{campaign_id}/stop")
def stop_campaign(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(CampaignModel).filter(CampaignModel.campaign_id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CAMPAIGN_NOT_FOUND")
    c.status = "COMPLETED"
    db.commit()
    return {"status": "SUCCESS", "campaignId": campaign_id, "newStatus": "COMPLETED"}


@router.get("/campaigns/{campaign_id}/population")
def get_campaign_population(campaign_id: str, db: Session = Depends(get_db)):
    c = db.query(CampaignModel).filter(CampaignModel.campaign_id == campaign_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="CAMPAIGN_NOT_FOUND")
    strats = db.query(StrategyModel).filter(StrategyModel.author == "AutonomousFactory").order_by(StrategyModel.created_at.desc()).all()
    return [
        {
            "strategyId": s.strategy_id,
            "name": s.name,
            "version": s.version,
            "family": s.family,
            "canonicalHash": s.canonical_hash,
            "generation": s.generation,
            "createdAt": s.created_at.isoformat() if s.created_at else None,
        }
        for s in strats
    ]


@router.get("/campaigns/{campaign_id}/events")
def get_campaign_events(campaign_id: str, db: Session = Depends(get_db)):
    events = db.query(CampaignEventModel).filter(CampaignEventModel.campaign_id == campaign_id).order_by(CampaignEventModel.created_at.desc()).all()
    return [
        {
            "id": e.id,
            "eventType": e.event_type,
            "message": e.message,
            "createdAt": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


# ==========================================
# AUTOPILOTO ULTRA API ENDPOINTS (V5)
# ==========================================

from services.api.app.factory.autopilot import AutopilotController
from services.api.app.db.database import (
    AutopilotRunModel,
    AutopilotDecisionModel,
    OpportunityMatrixModel,
    LeverageTrialModel,
)

@router.get("/search/background")
def get_background_search_status(db: Session = Depends(get_db)):
    """Estado del buscador en segundo plano: progreso global + últimas líneas de log + estado SQX en vivo."""
    try:
        logs = (
            db.query(SearchLogModel)
            .order_by(SearchLogModel.id.desc())
            .limit(60)
            .all()
        )
    except Exception as exc:
        print("ERROR SEARCH LOGS:", exc)
        logs = []
    rows = [
        {
            "id": l.id,
            "ts": l.ts,
            "level": l.level,
            "stage": l.stage,
            "message": l.message,
            "runId": l.run_id,
        }
        for l in reversed(logs)
    ]
    # Progreso derivado de los logs RUN (heurística simple, se puede refinar con tabla de celdas).
    total = 3
    done = 0
    for l in rows:
        if l["level"] == "info" and l["stage"] == "RUN" and "buscando" in l["message"]:
            pass
    # Contar celdas completadas: últimas líneas FINISH dan percent.
    pct = 0.0
    for l in rows:
        if l["stage"] == "FINISH":
            m = re.search(r"(\d+(\.\d+)?)% \((\d+)/(\d+)\)", l["message"] or "")
            if m:
                pct = float(m.group(1))
                done = int(m.group(3))
                total = int(m.group(4))
                break

    # ── Live SQX state (best-effort, non-blocking) ──
    sqx_live = {}
    try:
        import sys as _sys
        _sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "sqx_bridge"))
        from sqx_client import SQXMCPClient
        _c = SQXMCPClient("http://127.0.0.1:8080/mcp", timeout=8)
        _databanks = {"Results": 0, "Last generation": 0, "Results_robust_20260809": 0}
        for db_name in _databanks:
            try:
                strats = _c.list_strategies("Ultra_Auto_Pilot", db_name)
                _databanks[db_name] = len(strats) if isinstance(strats, list) else 0
            except Exception:
                _databanks[db_name] = -1
        sqx_live = {
            "databanks": _databanks,
            "evolving": _databanks.get("Last generation", 0) > 0,
            "resultsCount": _databanks.get("Results", 0),
            "lastGenCount": _databanks.get("Last generation", 0),
        }
    except Exception as sqx_err:
        sqx_live = {"error": str(sqx_err)}

    # ── Active search config ──
    active_config = None
    try:
        cfg = (
            db.query(SearchConfigModel)
            .order_by(SearchConfigModel.created_at.desc())
            .first()
        )
        if cfg:
            active_config = {
                "configId": cfg.config_id,
                "name": cfg.name,
                "mode": cfg.mode,
                "project": cfg.project,
                "databank": cfg.databank,
                "symbol": cfg.symbol,
                "interval": cfg.interval,
                "population": cfg.population,
            }
    except Exception:
        pass

    # ── Strategy pipeline stats ──
    pipeline = {}
    try:
        total_strats = db.query(StrategyModel).count()
        pipeline["totalStrategies"] = total_strats
    except Exception:
        pass

    return {
        "status": "SUCCESS",
        "percent": pct,
        "done": done,
        "total": total,
        "logs": rows,
        "sqxLive": sqx_live,
        "activeConfig": active_config,
        "pipeline": pipeline,
    }


@router.post("/search/background/run")
def start_background_search(payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db)):
    """Lanza el buscador en segundo plano de forma asíncrona (no bloquea la API)."""
    import threading
    from services.background_searcher import run_matrix, SEARCH_MATRIX

    def _worker():
        try:
            run_matrix(SEARCH_MATRIX)
        except Exception as e:  # pragma: no cover
            import traceback
            traceback.print_exc()

    t = threading.Thread(target=_worker, name="bg-search-matrix", daemon=True)
    t.start()
    return {"status": "QUEUED", "message": "Búsqueda en segundo plano en marcha. Consulta /api/v1/search/background para progreso."}


@router.post("/autopilot/start", status_code=202)
def start_autopilot(payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db)):
    """Single-button Autopilot trigger. Accepts empty body {} and returns 202 Accepted."""
    existing = (
        db.query(AutopilotRunModel)
        .filter(
            AutopilotRunModel.status.in_(
                ["QUEUED", "SCANNING", "RUNNING", "PAUSED"]
            )
        )
        .order_by(AutopilotRunModel.created_at.desc())
        .first()
    )
    if existing:
        return {
            "status": "SUCCESS",
            "autopilot": {
                "runId": existing.run_id,
                "status": existing.status,
            },
        }
    controller = AutopilotController()
    db.add(AutopilotRunModel(
        run_id=controller.run_id,
        status="QUEUED",
        mode="AUTOPILOT_ULTRA",
        cpu_budget_workers=4,
    ))
    db.commit()
    worker = threading.Thread(
        target=controller.start_autopilot,
        name=f"ultrarentable-{controller.run_id}",
        daemon=True,
    )
    worker.start()
    return {
        "status": "SUCCESS",
        "autopilot": {"runId": controller.run_id, "status": "QUEUED"},
    }

@router.post("/autopilot/pause")
def pause_autopilot(payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db)):
    run = db.query(AutopilotRunModel).order_by(AutopilotRunModel.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="AUTOPILOT_RUN_NOT_FOUND")
    controller = AutopilotController(run_id=run.run_id)
    res = controller.pause_autopilot()
    return {"status": "SUCCESS", "autopilot": res}

@router.post("/autopilot/resume")
def resume_autopilot(payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db)):
    run = db.query(AutopilotRunModel).order_by(AutopilotRunModel.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="AUTOPILOT_RUN_NOT_FOUND")
    controller = AutopilotController(run_id=run.run_id)
    res = controller.resume_autopilot()
    return {"status": "SUCCESS", "autopilot": res}

@router.post("/autopilot/stop")
def stop_autopilot(payload: dict[str, Any] = Body(default={}), db: Session = Depends(get_db)):
    run = db.query(AutopilotRunModel).order_by(AutopilotRunModel.created_at.desc()).first()
    if not run:
        raise HTTPException(status_code=404, detail="AUTOPILOT_RUN_NOT_FOUND")
    controller = AutopilotController(run_id=run.run_id)
    res = controller.stop_autopilot()
    return {"status": "SUCCESS", "autopilot": res}

@router.get("/autopilot/status")
def get_autopilot_status(db: Session = Depends(get_db)):
    run = db.query(AutopilotRunModel).order_by(AutopilotRunModel.created_at.desc()).first()
    if not run:
        return {
            "status": "READY",
            "runId": None,
            "mode": "AUTOPILOT_ULTRA",
            "currentSymbol": "ETH-USDT",
            "currentInterval": "1h",
            "bestFastReturnPct": 0.0,
            "evaluatedStrategiesCount": 0,
            "exploredSymbolsCount": 0,
        }
    return {
        "status": run.status,
        "runId": run.run_id,
        "mode": run.mode,
        "currentSymbol": run.current_symbol,
        "currentInterval": run.current_interval,
        "bestCandidateId": run.best_candidate_id,
        "bestFastReturnPct": run.best_fast_return_pct,
        "bestCanonicalReturnPct": run.best_canonical_return_pct,
        "evaluatedStrategiesCount": run.evaluated_strategies_count,
        "exploredSymbolsCount": run.explored_symbols_count,
        "createdAt": run.created_at.isoformat() if run.created_at else None,
    }

@router.get("/autopilot/decisions")
def get_autopilot_decisions(db: Session = Depends(get_db)):
    decisions = db.query(AutopilotDecisionModel).order_by(AutopilotDecisionModel.created_at.desc()).all()
    return [
        {
            "decisionId": d.decision_id,
            "runId": d.run_id,
            "module": d.module,
            "decision": d.decision,
            "reason": d.reason,
            "alternatives": json.loads(d.alternatives_json) if d.alternatives_json else None,
            "createdAt": d.created_at.isoformat() if d.created_at else None,
        }
        for d in decisions
    ]

@router.get("/autopilot/best-candidate")
def get_autopilot_best_candidate(db: Session = Depends(get_db)):
    run = db.query(AutopilotRunModel).order_by(AutopilotRunModel.created_at.desc()).first()
    if not run or not run.best_candidate_id:
        return {"candidate": None}
    strat = db.query(StrategyModel).filter(StrategyModel.strategy_id == run.best_candidate_id).first()
    if not strat:
        return {"candidate": None}
    return {
        "candidate": {
            "strategyId": strat.strategy_id,
            "name": strat.name,
            "family": strat.family,
            "author": strat.author,
            "canonicalHash": strat.canonical_hash,
            "dsl": json.loads(strat.dsl_json) if strat.dsl_json else None,
            "bestFastReturnPct": run.best_fast_return_pct,
            "createdAt": strat.created_at.isoformat() if strat.created_at else None,
        }
    }

@router.get("/autopilot/candidates")
def get_autopilot_candidates(db: Session = Depends(get_db)):
    strats = db.query(StrategyModel).filter(StrategyModel.author == "AUTOPILOT_FACTORY").order_by(StrategyModel.created_at.desc()).all()
    return [
        {
            "strategyId": s.strategy_id,
            "name": s.name,
            "family": s.family,
            "canonicalHash": s.canonical_hash,
            "createdAt": s.created_at.isoformat() if s.created_at else None,
        }
        for s in strats
    ]

@router.get("/autopilot/lineages")
def get_autopilot_lineages(db: Session = Depends(get_db)):
    return {"lineages": []}

@router.get("/autopilot/data-readiness")
def get_autopilot_data_readiness(db: Session = Depends(get_db)):
    matrix = db.query(OpportunityMatrixModel).order_by(OpportunityMatrixModel.rank.asc()).all()
    return [
        {
            "symbol": m.symbol,
            "interval": m.interval,
            "liquidityScore": m.liquidity_score,
            "volatilityScore": m.volatility_score,
            "datasetStatus": m.dataset_status,
            "rank": m.rank,
        }
        for m in matrix
    ]

@router.get("/autopilot/leverage-trials")
def get_autopilot_leverage_trials(db: Session = Depends(get_db)):
    trials = db.query(LeverageTrialModel).order_by(LeverageTrialModel.created_at.desc()).all()
    return [
        {
            "trialId": t.trial_id,
            "runId": t.run_id,
            "strategyId": t.strategy_id,
            "symbol": t.symbol,
            "leverage": t.leverage,
            "tier": t.tier,
            "status": t.status,
            "finalEquity": t.final_equity,
            "createdAt": t.created_at.isoformat() if t.created_at else None,
        }
        for t in trials
    ]



