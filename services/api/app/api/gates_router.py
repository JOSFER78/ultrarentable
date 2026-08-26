"""Canonical quantitative-gates API surface.

This module is intentionally evidence-first. It may expose gate definitions and
persist explicit configuration, but it must never fabricate performance,
trade ledgers, equity curves, telemetry, or cloud-sync claims.
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from contracts.gate_directory import GATES_DIRECTORY
from services.api.app.db.database import BacktestModel, get_db
from services.api.app.config import STATE_DB_PATH


gates_router = APIRouter(prefix="/gates", tags=["11 Quantitative Gates"])


def _find_gate(slug: str) -> Dict[str, Any]:
    gate = next((item for item in GATES_DIRECTORY if item["slug"] == slug or str(item["id"]) == slug or f"gate-{item['id']}" == slug), None)
    if gate is None:
        raise HTTPException(status_code=404, detail=f"GATE_NOT_FOUND: {slug}")
    return gate


def _config_table(db: Session) -> None:
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS gate_configurations (
            slug TEXT PRIMARY KEY,
            gate_number INTEGER NOT NULL,
            name TEXT NOT NULL,
            parameters_json TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            updated_by TEXT NOT NULL
        )
    """))
    db.commit()


def _configured_params(gate: Dict[str, Any], db: Session) -> Dict[str, Any]:
    params = copy.deepcopy(gate["default_params"])
    _config_table(db)
    row = db.execute(text("SELECT parameters_json FROM gate_configurations WHERE slug = :slug"), {"slug": gate["slug"]}).mappings().first()
    if row:
        stored = json.loads(row["parameters_json"])
        for key, value in stored.items():
            if key in params:
                params[key] = value
    return params


@gates_router.get("")
def list_all_gates(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    return [
        {
            **gate,
            "params": _configured_params(gate, db),
            "evidence_status": "NO_EVIDENCE",
            "performance_status": "NOT_AVAILABLE",
            "execution_status": "NOT_AVAILABLE",
            "cloud_sync_status": "NOT_CONFIGURED",
        }
        for gate in GATES_DIRECTORY
    ]


@gates_router.get("/{slug}")
def get_gate_by_slug(slug: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    gate = _find_gate(slug)
    return {
        **gate,
        "params": _configured_params(gate, db),
        "evidence_status": "NO_EVIDENCE",
        "performance_status": "NOT_AVAILABLE",
        "execution_status": "NOT_AVAILABLE",
        "cloud_sync_status": "NOT_CONFIGURED",
        "retrieved_at": datetime.now(timezone.utc).isoformat(),
    }


class GateConfigUpdateSchema(BaseModel):
    params: Dict[str, Any] = Field(default_factory=dict)
    source: Optional[str] = "MANUAL_UI"


@gates_router.put("/{slug}/config")
def update_gate_config(slug: str, body: GateConfigUpdateSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    gate = _find_gate(slug)
    allowed = set(gate["default_params"])
    unknown = sorted(set(body.params) - allowed)
    if unknown:
        raise HTTPException(status_code=422, detail={"code": "UNKNOWN_GATE_PARAMETERS", "parameters": unknown})
    _config_table(db)
    payload = json.dumps(body.params, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    config_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    now = datetime.now(timezone.utc).isoformat()
    db.execute(text("""
        INSERT INTO gate_configurations(slug, gate_number, name, parameters_json, updated_at, updated_by)
        VALUES (:slug, :gate_number, :name, :parameters_json, :updated_at, :updated_by)
        ON CONFLICT(slug) DO UPDATE SET
            parameters_json=excluded.parameters_json,
            updated_at=excluded.updated_at,
            updated_by=excluded.updated_by,
            gate_number=excluded.gate_number,
            name=excluded.name
    """), {
        "slug": gate["slug"], "gate_number": gate["id"], "name": gate["name"],
        "parameters_json": payload, "updated_at": now, "updated_by": body.source or "MANUAL_UI"
    })
    db.commit()
    return {
        "status": "SUCCESS",
        "slug": gate["slug"],
        "updated_params": body.params,
        "config_hash": config_hash,
        "persisted": True,
        "cloud_sync_status": "NOT_CONFIGURED",
    }


class SemanticAIPromptSchema(BaseModel):
    prompt: str = Field(..., min_length=1)
    candidate_id: Optional[str] = None


@gates_router.post("/{slug}/ai-semantic-edit")
def ai_semantic_edit_gate(slug: str, body: SemanticAIPromptSchema) -> Dict[str, Any]:
    _find_gate(slug)
    raise HTTPException(
        status_code=409,
        detail={
            "code": "AI_GATE_EDIT_REQUIRES_VERIFIED_POLICY",
            "message": "Natural-language gate mutation is disabled until it is backed by a versioned policy/evidence change. No inferred quantitative values are applied.",
        },
    )


@gates_router.get("/nautilus/detailed-backtest/{candidate_id}")
def get_nautilus_detailed_backtest(candidate_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    rows = (
        db.query(BacktestModel)
        .filter(BacktestModel.strategy_id == candidate_id, BacktestModel.status == "COMPLETED")
        .order_by(BacktestModel.created_at.desc())
        .all()
    )
    verified = next((row for row in rows if row.checksum and row.ledger_path and row.artifacts_path and Path(row.ledger_path).exists() and Path(row.artifacts_path).exists()), None)
    if verified is None:
        raise HTTPException(status_code=404, detail={"code": "NO_EVIDENCE", "candidate_id": candidate_id})

    ledger = json.loads(Path(verified.ledger_path).read_text(encoding="utf-8"))
    return {
        "status": "VERIFIED_ARTIFACT",
        "candidate_id": candidate_id,
        "backtest_id": verified.backtest_id,
        "engine_type": verified.engine_type,
        "checksum": verified.checksum,
        "source_ledger": verified.ledger_path,
        "source_artifacts": verified.artifacts_path,
        "performance_summary": {
            "final_equity": verified.final_equity,
            "net_return_pct": verified.net_return_pct,
            "max_drawdown_pct": verified.max_drawdown_pct,
            "win_rate": verified.win_rate,
            "trades_count": verified.trades_count,
            "profit_factor": verified.profit_factor,
        },
        "equity_curve": ledger.get("equityCurve", []),
        "trade_blotter": ledger.get("trades", []),
        "event_log": ledger.get("eventLog", []),
    }
