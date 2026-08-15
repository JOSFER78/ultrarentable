"""FastAPI Router for Prop Firm Providers and Versioned Rule Sets."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, ProviderRuleSetModel

providers_router = APIRouter(prefix="/providers", tags=["Prop Firm Providers"])


class ProviderCreateSchema(BaseModel):
    provider_id: str = Field(..., description="Unique provider ID (e.g. topstep_combine_50k)")
    name: str = Field(..., description="Display name")
    provider_name: str = Field(..., description="Firm name")
    market_type: str = Field("FUTURES", description="FUTURES, CFD, CRYPTO")
    platform: str = Field("Tradovate / NinjaTrader")
    allowed_instruments: str = Field("MES, MNQ, ES, NQ")
    account_size: float = Field(50000.0)
    target_usd: float = Field(3000.0)
    target_pct: float = Field(6.0)
    daily_loss_limit_usd: Optional[float] = None
    daily_loss_limit_pct: Optional[float] = None
    dll_calc_model: str = Field("EOD Balance")
    max_trailing_dd_usd: float = Field(2000.0)
    max_trailing_dd_pct: float = Field(4.0)
    trailing_dd_type: str = Field("EOD Trailing")
    consistency_rule_pct: float = Field(50.0)
    min_trading_days: int = Field(2)
    overnight_allowed: bool = Field(False)
    news_trading_allowed: bool = Field(True)
    ea_bots_allowed: str = Field("PERMITTED")
    monthly_cost_usd: Optional[float] = None
    source_url: Optional[str] = None
    verified_at: Optional[str] = None
    verification_status: str = Field("VERIFIED")
    notes: Optional[str] = None


@providers_router.get("")
def list_providers(
    market_type: Optional[str] = Query(None, description="FUTURES, CFD, CRYPTO"),
    verification_status: Optional[str] = Query(None, description="VERIFIED, UNVERIFIED"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all prop firm providers with filtering."""
    query = db.query(ProviderRuleSetModel)
    if market_type:
        query = query.filter(ProviderRuleSetModel.market_type == market_type.upper())
    if verification_status:
        query = query.filter(ProviderRuleSetModel.verification_status == verification_status.upper())
    
    results = []
    for p in query.all():
        results.append({
            "provider_id": p.provider_id,
            "name": p.name,
            "provider_name": p.provider_name,
            "market_type": p.market_type,
            "platform": p.platform,
            "allowed_instruments": p.allowed_instruments,
            "account_size": p.account_size,
            "target_usd": p.target_usd,
            "target_pct": p.target_pct,
            "daily_loss_limit_usd": p.daily_loss_limit_usd,
            "daily_loss_limit_pct": p.daily_loss_limit_pct,
            "dll_calc_model": p.dll_calc_model,
            "max_trailing_dd_usd": p.max_trailing_dd_usd,
            "max_trailing_dd_pct": p.max_trailing_dd_pct,
            "trailing_dd_type": p.trailing_dd_type,
            "consistency_rule_pct": p.consistency_rule_pct,
            "min_trading_days": p.min_trading_days,
            "overnight_allowed": p.overnight_allowed,
            "news_trading_allowed": p.news_trading_allowed,
            "ea_bots_allowed": p.ea_bots_allowed,
            "monthly_cost_usd": p.monthly_cost_usd,
            "source_url": p.source_url,
            "verified_at": p.verified_at,
            "verification_status": p.verification_status,
            "notes": p.notes,
        })
    return results


@providers_router.get("/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single provider rule set by ID."""
    p = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.provider_id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="PROVIDER_NOT_FOUND")
    return {
        "provider_id": p.provider_id,
        "name": p.name,
        "provider_name": p.provider_name,
        "market_type": p.market_type,
        "platform": p.platform,
        "allowed_instruments": p.allowed_instruments,
        "account_size": p.account_size,
        "target_usd": p.target_usd,
        "target_pct": p.target_pct,
        "daily_loss_limit_usd": p.daily_loss_limit_usd,
        "daily_loss_limit_pct": p.daily_loss_limit_pct,
        "dll_calc_model": p.dll_calc_model,
        "max_trailing_dd_usd": p.max_trailing_dd_usd,
        "max_trailing_dd_pct": p.max_trailing_dd_pct,
        "trailing_dd_type": p.trailing_dd_type,
        "consistency_rule_pct": p.consistency_rule_pct,
        "min_trading_days": p.min_trading_days,
        "overnight_allowed": p.overnight_allowed,
        "news_trading_allowed": p.news_trading_allowed,
        "ea_bots_allowed": p.ea_bots_allowed,
        "monthly_cost_usd": p.monthly_cost_usd,
        "source_url": p.source_url,
        "verified_at": p.verified_at,
        "verification_status": p.verification_status,
        "notes": p.notes,
    }
