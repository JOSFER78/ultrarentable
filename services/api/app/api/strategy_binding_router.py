"""Strict binding between an extracted strategy and an approved physical dataset."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import Column, DateTime, String, UniqueConstraint

from services.api.app.db.database import Base, DatasetModel, SessionLocal, StrategyModel


class StrategyDatasetBindingModel(Base):
    __tablename__ = "strategy_dataset_bindings"
    __table_args__ = (UniqueConstraint("strategy_id", name="uq_strategy_dataset_binding_strategy"),)

    binding_id = Column(String, primary_key=True, index=True)
    strategy_id = Column(String, index=True, nullable=False)
    strategy_hash = Column(String, nullable=False)
    dataset_id = Column(String, index=True, nullable=False)
    dataset_hash = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    bound_at = Column(DateTime, default=datetime.utcnow)


router = APIRouter(prefix="/strategy-lab", tags=["Strategy Lab Binding"])


class BindDatasetRequest(BaseModel):
    dataset_id: str = Field(..., min_length=1)


def _physical_sha256(path_text: str) -> str:
    path = Path(path_text)
    if not path.is_file():
        raise HTTPException(status_code=422, detail="DATASET_FILE_NOT_FOUND")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@router.post("/strategies/{strategy_id}/bind-dataset")
def bind_strategy_dataset(strategy_id: str, request: BindDatasetRequest) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        strategy = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
        if not strategy:
            raise HTTPException(status_code=404, detail="STRATEGY_NOT_FOUND")
        dataset = db.query(DatasetModel).filter(DatasetModel.dataset_id == request.dataset_id).first()
        if not dataset:
            raise HTTPException(status_code=404, detail="DATASET_NOT_FOUND")
        if dataset.status != "APPROVED":
            raise HTTPException(status_code=409, detail="DATASET_NOT_APPROVED")
        if not dataset.checksum_sha256:
            raise HTTPException(status_code=409, detail="DATASET_HASH_MISSING")
        if not dataset.file_path:
            raise HTTPException(status_code=409, detail="DATASET_FILE_PATH_MISSING")

        dsl = {}
        try:
            import json
            dsl = json.loads(strategy.dsl_json) if strategy.dsl_json else {}
        except Exception as exc:
            raise HTTPException(status_code=409, detail=f"STRATEGY_SOURCE_INVALID:{exc}") from exc

        market = dsl.get("market") or {}
        strategy_symbol = market.get("symbol")
        strategy_timeframe = market.get("timeframe")
        if not strategy_symbol or not strategy_timeframe:
            raise HTTPException(status_code=409, detail="STRATEGY_MARKET_IDENTITY_UNPROVEN")
        if str(strategy_symbol).upper() != str(dataset.symbol).upper():
            raise HTTPException(status_code=409, detail="DATASET_SYMBOL_MISMATCH")
        if str(strategy_timeframe).lower() != str(dataset.interval).lower():
            raise HTTPException(status_code=409, detail="DATASET_TIMEFRAME_MISMATCH")

        actual_hash = _physical_sha256(dataset.file_path)
        if actual_hash.lower() != dataset.checksum_sha256.lower():
            raise HTTPException(status_code=409, detail="DATASET_PHYSICAL_HASH_MISMATCH")

        binding_id = f"binding:{strategy.strategy_id}:{dataset.dataset_id}"
        existing = db.query(StrategyDatasetBindingModel).filter(StrategyDatasetBindingModel.strategy_id == strategy.strategy_id).first()
        if existing and existing.dataset_id != dataset.dataset_id:
            raise HTTPException(status_code=409, detail="STRATEGY_ALREADY_BOUND_TO_DIFFERENT_DATASET")

        if not existing:
            db.add(
                StrategyDatasetBindingModel(
                    binding_id=binding_id,
                    strategy_id=strategy.strategy_id,
                    strategy_hash=strategy.canonical_hash,
                    dataset_id=dataset.dataset_id,
                    dataset_hash=actual_hash,
                    symbol=dataset.symbol,
                    timeframe=dataset.interval,
                )
            )
        db.commit()
        return {
            "status": "BOUND",
            "binding_id": binding_id,
            "strategy_id": strategy.strategy_id,
            "strategy_hash": strategy.canonical_hash,
            "dataset_id": dataset.dataset_id,
            "dataset_hash": actual_hash,
            "symbol": dataset.symbol,
            "timeframe": dataset.interval,
            "provenance": "PHYSICAL_FILE_SHA256_VERIFIED",
            "next_step": "CANONICAL_BASELINE_BACKTEST",
        }
    finally:
        db.close()


@router.get("/strategies/{strategy_id}/binding")
def get_strategy_binding(strategy_id: str) -> Dict[str, Any]:
    db = SessionLocal()
    try:
        binding = db.query(StrategyDatasetBindingModel).filter(StrategyDatasetBindingModel.strategy_id == strategy_id).first()
        if not binding:
            return {"status": "UNBOUND", "strategy_id": strategy_id}
        return {
            "status": "BOUND",
            "binding_id": binding.binding_id,
            "strategy_id": binding.strategy_id,
            "strategy_hash": binding.strategy_hash,
            "dataset_id": binding.dataset_id,
            "dataset_hash": binding.dataset_hash,
            "symbol": binding.symbol,
            "timeframe": binding.timeframe,
            "bound_at": binding.bound_at.isoformat() if binding.bound_at else None,
        }
    finally:
        db.close()
