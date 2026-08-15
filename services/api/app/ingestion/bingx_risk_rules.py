from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Any, Mapping
import uuid

from sqlalchemy.orm import Session

from services.api.app.config import DATA_DIR
from services.api.app.bingx.client import BingXPyRestClient
from services.api.app.db.database import (
    AccountFeeSnapshotModel,
    InstrumentRuleSnapshotModel,
)


SOURCE_ENDPOINT = "/api/v1/quote/contract/marginTiered/get"
SYMBOL_PATTERN = re.compile(r"^[A-Z0-9]+-[A-Z]+$")


class BingXRiskCaptureError(RuntimeError):
    pass


@dataclass(frozen=True)
class NormalizedRiskRules:
    symbol: str
    max_leverage: int
    maintenance_tiers: tuple[dict[str, float | int], ...]
    raw_sha256: str
    raw_json: str


@dataclass(frozen=True)
class NormalizedPublicFees:
    symbol: str
    maker_fee: float
    taker_fee: float
    raw_sha256: str
    raw_json: str


def _canonical_payload(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _parse_maintenance_tiers(value: Any) -> tuple[dict[str, float | int], ...]:
    if not isinstance(value, str) or not value.strip():
        raise BingXRiskCaptureError("maintenanceTiered is missing")
    tiers: list[dict[str, float | int]] = []
    previous_end = 0.0
    for index, segment in enumerate(value.split(";")):
        fields = segment.split(":")
        if len(fields) != 4 or "-" not in fields[0]:
            raise BingXRiskCaptureError(f"maintenance tier {index} is malformed")
        start_raw, end_raw = fields[0].split("-", 1)
        try:
            start = float(start_raw)
            end = float(end_raw)
            rate = float(fields[1])
            max_leverage = int(fields[2])
            amount = float(fields[3])
        except (TypeError, ValueError) as exc:
            raise BingXRiskCaptureError(
                f"maintenance tier {index} contains invalid numbers"
            ) from exc
        if start != previous_end or end <= start:
            raise BingXRiskCaptureError(
                f"maintenance tier {index} is not contiguous and ascending"
            )
        if not 0 <= rate < 1 or amount < 0 or not 1 <= max_leverage <= 1000:
            raise BingXRiskCaptureError(f"maintenance tier {index} is out of range")
        tiers.append(
            {
                "max_notional": end,
                "maintenance_margin_rate": rate,
                "maintenance_amount": amount,
                "max_leverage": min(max_leverage, 500),
            }
        )
        previous_end = end
    return tuple(tiers)


def normalize_margin_payload(
    payload: Mapping[str, Any], symbol: str
) -> NormalizedRiskRules:
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise BingXRiskCaptureError("invalid BingX symbol")
    if payload.get("code") != 0 or not isinstance(payload.get("data"), Mapping):
        raise BingXRiskCaptureError("BingX margin response was not successful")
    tiers = _parse_maintenance_tiers(payload["data"].get("maintenanceTiered"))
    raw_json = _canonical_payload(payload)
    return NormalizedRiskRules(
        symbol=symbol,
        max_leverage=min(500, max(int(tier["max_leverage"]) for tier in tiers)),
        maintenance_tiers=tiers,
        raw_sha256=hashlib.sha256(raw_json.encode("utf-8")).hexdigest(),
        raw_json=raw_json,
    )


def normalize_public_contract_fees(
    contract: Mapping[str, Any], symbol: str
) -> NormalizedPublicFees:
    if not SYMBOL_PATTERN.fullmatch(symbol) or contract.get("symbol") != symbol:
        raise BingXRiskCaptureError("public fee contract belongs to another symbol")
    try:
        maker_fee = float(contract["makerFeeRate"])
        taker_value = contract.get("takerFeeRate")
        if taker_value is None:
            taker_value = contract["feeRate"]
        taker_fee = float(taker_value)
    except (KeyError, TypeError, ValueError) as exc:
        raise BingXRiskCaptureError("public contract fees are missing") from exc
    if not 0 <= maker_fee < 1 or not 0 <= taker_fee < 1:
        raise BingXRiskCaptureError("public contract fees are out of range")
    raw_json = _canonical_payload(contract)
    return NormalizedPublicFees(
        symbol=symbol,
        maker_fee=maker_fee,
        taker_fee=taker_fee,
        raw_sha256=hashlib.sha256(raw_json.encode("utf-8")).hexdigest(),
        raw_json=raw_json,
    )


def capture_margin_payload(
    symbol: str,
    *,
    script_path: Path | None = None,
    timeout_seconds: int = 90,
) -> Mapping[str, Any]:
    if not SYMBOL_PATTERN.fullmatch(symbol):
        raise BingXRiskCaptureError("invalid BingX symbol")
    script = script_path or Path(__file__).parents[2] / "scripts" / "capture_bingx_risk_rules.mjs"
    try:
        completed = subprocess.run(
            ["node", str(script), symbol],
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError) as exc:
        raise BingXRiskCaptureError("failed to capture BingX margin rules") from exc
    if not isinstance(payload, Mapping):
        raise BingXRiskCaptureError("BingX margin response is not an object")
    return payload


def persist_risk_snapshot(
    db: Session,
    rules: NormalizedRiskRules,
    *,
    captured_at: datetime | None = None,
    raw_dir: Path | None = None,
) -> InstrumentRuleSnapshotModel:
    captured_at = captured_at or datetime.now(timezone.utc)
    target_dir = raw_dir or Path(DATA_DIR) / "raw" / "risk_rules"
    target_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = f"risk_{rules.symbol.replace('-', '_')}_{uuid.uuid4().hex[:12]}"
    raw_path = target_dir / f"{snapshot_id}.json"
    temporary_path = raw_path.with_suffix(".json.tmp")
    temporary_path.write_text(rules.raw_json, encoding="utf-8")
    temporary_path.replace(raw_path)
    snapshot = InstrumentRuleSnapshotModel(
        snapshot_id=snapshot_id,
        symbol=rules.symbol,
        captured_at=captured_at,
        source_endpoint=SOURCE_ENDPOINT,
        raw_path=str(raw_path),
        raw_sha256=rules.raw_sha256,
        max_leverage=rules.max_leverage,
        maintenance_margin_rate=float(
            rules.maintenance_tiers[0]["maintenance_margin_rate"]
        ),
        maintenance_tiers_json=json.dumps(
            list(rules.maintenance_tiers),
            sort_keys=True,
            separators=(",", ":"),
        ),
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def capture_and_persist_risk_rules(
    db: Session, symbol: str
) -> InstrumentRuleSnapshotModel:
    return persist_risk_snapshot(
        db,
        normalize_margin_payload(capture_margin_payload(symbol), symbol),
    )


def persist_public_fee_snapshot(
    db: Session,
    fees: NormalizedPublicFees,
    *,
    captured_at: datetime | None = None,
    raw_dir: Path | None = None,
) -> AccountFeeSnapshotModel:
    captured_at = captured_at or datetime.now(timezone.utc)
    target_dir = raw_dir or Path(DATA_DIR) / "raw" / "fee_rules"
    target_dir.mkdir(parents=True, exist_ok=True)
    snapshot_id = f"fee_{fees.symbol.replace('-', '_')}_{uuid.uuid4().hex[:12]}"
    raw_path = target_dir / f"{snapshot_id}.json"
    temporary_path = raw_path.with_suffix(".json.tmp")
    temporary_path.write_text(fees.raw_json, encoding="utf-8")
    temporary_path.replace(raw_path)
    snapshot = AccountFeeSnapshotModel(
        snapshot_id=snapshot_id,
        account_hash="PUBLIC_DEFAULT",
        symbol=fees.symbol,
        maker_fee=fees.maker_fee,
        taker_fee=fees.taker_fee,
        captured_at=captured_at,
        source_endpoint="/openApi/swap/v2/quote/contracts",
        raw_path=str(raw_path),
        raw_sha256=fees.raw_sha256,
    )
    db.add(snapshot)
    db.commit()
    db.refresh(snapshot)
    return snapshot


def capture_and_persist_public_fees(
    db: Session,
    symbol: str,
    *,
    contracts: list[Mapping[str, Any]] | None = None,
) -> AccountFeeSnapshotModel:
    contracts = contracts if contracts is not None else BingXPyRestClient().get_contracts()
    contract = next((item for item in contracts if item.get("symbol") == symbol), None)
    if contract is None:
        raise BingXRiskCaptureError(f"public contract {symbol} was not found")
    return persist_public_fee_snapshot(
        db,
        normalize_public_contract_fees(contract, symbol),
    )
