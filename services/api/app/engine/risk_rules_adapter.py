from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
import math
from typing import Any, Mapping

from services.api.app.engine.margin_model import (
    BingXMarketRiskRules,
    MaintenanceTier,
    MarginModelError,
    build_risk_rules,
)


class RiskRulesUnavailable(RuntimeError):
    """The campaign lacks a fresh, auditable exchange-rule snapshot."""


def _value(source: Any, name: str, default: Any = None) -> Any:
    if isinstance(source, Mapping):
        return source.get(name, default)
    return getattr(source, name, default)


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, datetime):
        raise RiskRulesUnavailable(f"{field} is missing")
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _require_provenance(snapshot: Any, label: str) -> None:
    if not _value(snapshot, "source_endpoint"):
        raise RiskRulesUnavailable(f"{label} source_endpoint is missing")
    digest = str(_value(snapshot, "raw_sha256", ""))
    if len(digest) != 64 or any(char not in "0123456789abcdefABCDEF" for char in digest):
        raise RiskRulesUnavailable(f"{label} raw_sha256 is invalid")


def _require_fresh(snapshot: Any, label: str, now: datetime, max_age: timedelta) -> None:
    captured_at = _utc(_value(snapshot, "captured_at"), f"{label} captured_at")
    if captured_at > now + timedelta(minutes=5):
        raise RiskRulesUnavailable(f"{label} captured_at is in the future")
    if now - captured_at > max_age:
        raise RiskRulesUnavailable(f"{label} snapshot is stale")


def _parse_tiers(raw: Any) -> tuple[MaintenanceTier, ...]:
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RiskRulesUnavailable("maintenance_tiers_json is invalid JSON") from exc
    if not isinstance(raw, list) or not raw:
        raise RiskRulesUnavailable("complete maintenance tiers are missing")

    tiers: list[MaintenanceTier] = []
    for index, item in enumerate(raw):
        if not isinstance(item, Mapping):
            raise RiskRulesUnavailable(f"maintenance tier {index} is not an object")
        limit = item.get("max_notional", item.get("maxNotional"))
        if limit is None and index == len(raw) - 1:
            limit = math.inf
        rate = item.get("maintenance_margin_rate", item.get("maintenanceMarginRate"))
        amount = item.get("maintenance_amount", item.get("maintenanceAmount", 0.0))
        max_leverage = item.get("max_leverage", item.get("maxLeverage"))
        try:
            tiers.append(
                MaintenanceTier(
                    float(limit),
                    float(rate),
                    float(amount),
                    int(max_leverage) if max_leverage is not None else None,
                )
            )
        except (TypeError, ValueError, MarginModelError) as exc:
            raise RiskRulesUnavailable(f"maintenance tier {index} is invalid") from exc
    return tuple(tiers)


def load_verified_bingx_risk_rules(
    rule_snapshot: Any,
    fee_snapshot: Any,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(hours=24),
) -> BingXMarketRiskRules:
    """Build executable rules only from fresh, checksummed BingX snapshots.

    A historical single ``maintenance_margin_rate`` is intentionally rejected:
    BingX applies notional tiers and maintenance amounts, so flattening those
    brackets would create false liquidations or false survivors.
    """

    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    if max_age <= timedelta(0):
        raise ValueError("max_age must be positive")
    if rule_snapshot is None:
        raise RiskRulesUnavailable("instrument rule snapshot is missing")
    if fee_snapshot is None:
        raise RiskRulesUnavailable("account fee snapshot is missing")

    _require_provenance(rule_snapshot, "instrument rule")
    _require_provenance(fee_snapshot, "account fee")
    _require_fresh(rule_snapshot, "instrument rule", now, max_age)
    _require_fresh(fee_snapshot, "account fee", now, max_age)

    symbol = str(_value(rule_snapshot, "symbol", ""))
    fee_symbol = _value(fee_snapshot, "symbol")
    if fee_symbol not in (None, "", symbol):
        raise RiskRulesUnavailable("fee snapshot belongs to a different symbol")

    tiers_raw = _value(rule_snapshot, "maintenance_tiers_json")
    if tiers_raw is None:
        tiers_raw = _value(rule_snapshot, "maintenance_tiers")
    tiers = _parse_tiers(tiers_raw)

    try:
        return build_risk_rules(
            symbol=symbol,
            max_leverage=int(_value(rule_snapshot, "max_leverage")),
            taker_fee_rate=float(_value(fee_snapshot, "taker_fee")),
            maintenance_tiers=tiers,
        )
    except (TypeError, ValueError, MarginModelError) as exc:
        raise RiskRulesUnavailable("verified snapshots contain invalid risk values") from exc
