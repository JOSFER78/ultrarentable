"""Evidence-first strategy laboratory API.

Pipeline:
EXTRACTED_UNVERIFIED -> STRUCTURALLY_VERIFIED -> BACKTEST_VERIFIED -> CERTIFIED_CURRENT

Extraction is source capture only. Missing facts stay missing; this module never
creates backtests, profitability, capital, datasets or certification evidence.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel, DatasetModel
from services.sqx_bridge.sqx_client import SQXMCPClient, SQXMCPError
from services.sqx_bridge.ingest_sqx_results import DATABANK, extract_stats

router = APIRouter(prefix="/strategy-lab", tags=["Strategy Lab"])


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _canonical_payload(project: str, databank: str, name: str, raw_stats: Dict[str, Any]) -> str:
    payload = {
        "schema": "ultrarentable.strategy-source.v1",
        "source": {
            "engine": "StrategyQuantX",
            "project": project,
            "databank": databank,
            "strategy_name": name,
        },
        "raw_stats": raw_stats,
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _explicit_market_identity(raw: Dict[str, Any]) -> tuple[str | None, str | None]:
    """Read symbol/timeframe only when SQX labels them explicitly."""
    columns = raw.get("columns") or []
    values = raw.get("values") or []
    symbol: str | None = None
    timeframe: str | None = None
    for column, value in zip(columns, values):
        label = str(column).strip().lower()
        text = str(value).strip() if value is not None else ""
        if not text:
            continue
        if symbol is None and label in {"symbol", "instrument", "market", "asset"}:
            symbol = text
        if timeframe is None and label in {"timeframe", "tf", "period", "bar period"}:
            timeframe = text
    if symbol:
        compact = symbol.upper().replace("/", "-").replace("_AUTO", "").replace("_FUT", "").replace("_PERP", "")
        if compact.endswith("USDT") and "-" not in compact:
            compact = f"{compact[:-4]}-USDT"
        symbol = compact
    return symbol, timeframe


def _source_record(strategy: StrategyModel) -> Dict[str, Any]:
    dsl = json.loads(strategy.dsl_json) if strategy.dsl_json else {}
    source = dsl.get("source", {})
    raw_stats = dsl.get("raw_stats", {})
    market = dsl.get("market", {})
    return {
        "strategy_id": strategy.strategy_id,
        "name": strategy.name,
        "strategy_version": strategy.version,
        "strategy_hash": strategy.canonical_hash,
        "validation_status": strategy.validation_status,
        "source_engine": source.get("engine"),
        "source_project": source.get("project"),
        "source_databank": source.get("databank"),
        "source_strategy_name": source.get("strategy_name"),
        "symbol": market.get("symbol"),
        "timeframe": market.get("timeframe"),
        "dataset_id": market.get("dataset_id"),
        "dataset_hash": market.get("dataset_hash"),
        "raw_stats": raw_stats,
        "created_at": strategy.created_at.isoformat() if strategy.created_at else None,
    }


@router.get("/overview")
def strategy_lab_overview() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        extracted = db.query(StrategyModel).filter(StrategyModel.family == "sqx_extracted").count()
        structural = db.query(StrategyModel).filter(StrategyModel.validation_status == "STRUCTURALLY_VERIFIED").count()
        backtest_verified = (
            db.query(BacktestModel)
            .join(StrategyModel, StrategyModel.strategy_id == BacktestModel.strategy_id)
            .filter(StrategyModel.family == "sqx_extracted", BacktestModel.status == "COMPLETED")
            .count()
        )
        certified = db.query(StrategyModel).filter(StrategyModel.validation_status == "CERTIFIED_CURRENT").count()
        datasets = db.query(DatasetModel).filter(DatasetModel.status == "APPROVED").count()
        return {
            "status": "SUCCESS",
            "as_of_utc": _utc_now(),
            "pipeline": {
                "extracted": extracted,
                "structurally_verified": structural,
                "backtest_verified": backtest_verified,
                "certified_current": certified,
                "approved_datasets": datasets,
            },
            "evidence_policy": "A stage never implies the next stage.",
        }
    finally:
        db.close()


@router.get("/strategies")
def strategy_lab_strategies(limit: int = Query(100, ge=1, le=1000)) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        rows = (
            db.query(StrategyModel)
            .filter(StrategyModel.family == "sqx_extracted")
            .order_by(StrategyModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return {"status": "SUCCESS", "count": len(rows), "strategies": [_source_record(row) for row in rows]}
    finally:
        db.close()


@router.get("/strategies/{strategy_id}")
def strategy_lab_strategy(strategy_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        row = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="STRATEGY_NOT_FOUND")
        return {"status": "SUCCESS", "strategy": _source_record(row)}
    finally:
        db.close()


@router.get("/sqx/status")
def strategy_lab_sqx_status(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    try:
        client = SQXMCPClient(base_url=url)
        return {"status": "SUCCESS", "source": "StrategyQuantX", "result": client.check_connection()}
    except Exception as exc:
        return {"status": "UNAVAILABLE", "source": "StrategyQuantX", "error": str(exc)}


@router.post("/extract/{project_name}")
def extract_from_sqx(project_name: str) -> Dict[str, Any]:
    """Capture real SQX source records without creating quantitative results."""
    project_name = project_name.strip()
    if not project_name:
        raise HTTPException(status_code=422, detail="PROJECT_NAME_REQUIRED")
    client = SQXMCPClient()
    try:
        strategy_names = client.list_strategies(project_name, DATABANK) or []
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_UNAVAILABLE: {exc}") from exc

    db = SessionLocal()
    inserted = unchanged = quarantined = 0
    try:
        for name in strategy_names:
            try:
                raw = client.get_strategy_stats(project_name, DATABANK, name)
            except Exception:
                quarantined += 1
                continue
            if not isinstance(raw, dict) or not raw:
                quarantined += 1
                continue

            # Parse real source statistics for display/research; values are never used
            # as certification evidence at this stage.
            try:
                metrics = extract_stats(raw) or {}
            except Exception:
                metrics = {}
            symbol, timeframe = _explicit_market_identity(raw)

            strategy_id = f"sqx:{project_name}:{DATABANK}:{name}"
            payload = _canonical_payload(project_name, DATABANK, name, raw)
            strategy_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            encoded = json.dumps(
                {
                    "schema": "ultrarentable.strategy-source.v1",
                    "source": {
                        "engine": "StrategyQuantX",
                        "project": project_name,
                        "databank": DATABANK,
                        "strategy_name": name,
                        "extracted_at_utc": _utc_now(),
                    },
                    "market": {
                        "symbol": symbol,
                        "timeframe": timeframe,
                        "dataset_id": None,
                        "dataset_hash": None,
                    },
                    "raw_stats": metrics,
                }, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )

            existing = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
            if existing and existing.canonical_hash == strategy_hash and existing.dsl_json == encoded:
                unchanged += 1
                continue
            if existing:
                existing.canonical_hash = strategy_hash
                existing.dsl_json = encoded
                existing.validation_status = "EXTRACTED_UNVERIFIED"
                existing.version = "SOURCE-1"
                existing.created_at = datetime.utcnow()
            else:
                db.add(
                    StrategyModel(
                        strategy_id=strategy_id,
                        name=name,
                        version="SOURCE-1",
                        family="sqx_extracted",
                        author="StrategyQuantX",
                        canonical_hash=strategy_hash,
                        generation=0,
                        dsl_json=encoded,
                        validation_status="EXTRACTED_UNVERIFIED",
                        created_at=datetime.utcnow(),
                    )
                )
                inserted += 1
        db.commit()
        return {
            "status": "SUCCESS",
            "project": project_name,
            "databank": DATABANK,
            "found": len(strategy_names),
            "inserted": inserted,
            "unchanged": unchanged,
            "quarantined": quarantined,
            "next_step": "REQUIRES_REAL_DATASET_AND_CANONICAL_BACKTEST",
        }
    finally:
        db.close()


@router.post("/improvement/plan/{strategy_id}")
def organic_improvement_plan(strategy_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        row = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
        if not row:
            raise HTTPException(status_code=404, detail="STRATEGY_NOT_FOUND")
        dsl = json.loads(row.dsl_json) if row.dsl_json else {}
        raw_stats = dsl.get("raw_stats") or {}
        return {
            "status": "NO_MUTATION_PERFORMED",
            "strategy_id": strategy_id,
            "parent_hash": row.canonical_hash,
            "evidence": {
                "has_real_dataset": bool(dsl.get("market", {}).get("dataset_id")),
                "has_dataset_hash": bool(dsl.get("market", {}).get("dataset_hash")),
                "source_engine": dsl.get("source", {}).get("engine"),
                "raw_metric_fields": sorted(raw_stats.keys()),
            },
            "organic_next_steps": [
                "Bind an approved real dataset matching the extracted symbol/timeframe.",
                "Run the canonical deterministic backtest without parameter changes.",
                "Measure failure modes and regime dependence.",
                "Only then propose the smallest evidence-backed mutation.",
                "Re-backtest the child from scratch and preserve parent/child lineage.",
            ],
        }
    finally:
        db.close()
