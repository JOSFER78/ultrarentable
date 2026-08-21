"""FastAPI Router for Prop Firm Providers and Versioned Rule Sets."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, ProviderRuleSetModel
from services.api.app.db.seed_prop_firms import PROP_FIRMS_CATALOG

providers_router = APIRouter(prefix="/providers", tags=["Prop Firm Providers"])


class ProviderCreateSchema(BaseModel):
    provider_id: str = Field(..., description="Unique provider ID (e.g. topstep_combine_50k)")
    name: str = Field(..., description="Display name")
    provider_name: str = Field(..., description="Firm name")
    market_type: str = Field("FUTURES", description="FUTURES, CFD, CRYPTO")
    platform: str = Field("Tradovate / NinjaTrader")
    allowed_instruments: str = Field("MES, MNQ, ES, NQ")
    account_size: float = Field(50000.0)
    program_type: str = Field("Standard")
    account_tier: str = Field("50K")
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
    regular_price_usd: Optional[float] = None
    promo_price_usd: Optional[float] = None
    discount_code: Optional[str] = None
    discount_pct: float = Field(0.0)
    activation_fee_usd: float = Field(0.0)
    payout_split_pct: float = Field(90.0)
    payout_frequency: str = Field("Quincenal")
    payout_buffer_usd: float = Field(0.0)
    funded_trailing_lock: str = Field("LOCKS_AT_INITIAL_BALANCE")
    contracts_limit: Optional[str] = None
    trust_score: int = Field(85)
    stage_type: str = Field("EVALUATION")
    source_url: Optional[str] = None
    verified_at: Optional[str] = None
    verification_status: str = Field("VERIFIED")
    notes: Optional[str] = None


def _format_provider(p: ProviderRuleSetModel) -> Dict[str, Any]:
    return {
        "provider_id": p.provider_id,
        "name": p.name,
        "provider_name": p.provider_name,
        "market_type": p.market_type,
        "platform": p.platform,
        "allowed_instruments": p.allowed_instruments,
        "account_size": p.account_size,
        "program_type": getattr(p, "program_type", "Standard"),
        "account_tier": getattr(p, "account_tier", "50K"),
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
        "monthly_cost_usd": p.monthly_cost_usd or p.promo_price_usd or p.regular_price_usd,
        "regular_price_usd": getattr(p, "regular_price_usd", p.monthly_cost_usd),
        "promo_price_usd": getattr(p, "promo_price_usd", p.monthly_cost_usd),
        "discount_code": getattr(p, "discount_code", None),
        "discount_pct": getattr(p, "discount_pct", 0.0),
        "activation_fee_usd": getattr(p, "activation_fee_usd", 0.0),
        "payout_split_pct": getattr(p, "payout_split_pct", 90.0),
        "payout_frequency": getattr(p, "payout_frequency", "Quincenal"),
        "payout_buffer_usd": getattr(p, "payout_buffer_usd", 0.0),
        "funded_trailing_lock": getattr(p, "funded_trailing_lock", "LOCKS_AT_INITIAL_BALANCE"),
        "contracts_limit": getattr(p, "contracts_limit", None),
        "trust_score": getattr(p, "trust_score", 85),
        "stage_type": getattr(p, "stage_type", "EVALUATION"),
        "source_url": p.source_url,
        "verified_at": p.verified_at,
        "verification_status": p.verification_status,
        "notes": p.notes,
    }


@providers_router.get("")
def list_providers(
    market_type: Optional[str] = Query(None, description="FUTURES, CFD, CRYPTO"),
    account_tier: Optional[str] = Query(None, description="10K, 25K, 50K, 100K, 150K, 200K, 250K, 300K"),
    trailing_dd_type: Optional[str] = Query(None, description="EOD Trailing, Intraday Peak Trailing, Static, Balance Based"),
    ea_bots_allowed: Optional[str] = Query(None, description="PERMITTED, PROHIBITED"),
    no_activation_fee: Optional[bool] = Query(None, description="Filter for 0 activation fee accounts"),
    verification_status: Optional[str] = Query(None, description="VERIFIED, UNVERIFIED"),
    search: Optional[str] = Query(None, description="Search by name, provider or platform"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List all prop firm providers with multidimensional filtering."""
    query = db.query(ProviderRuleSetModel)
    
    if market_type and market_type.upper() != "ALL":
        query = query.filter(ProviderRuleSetModel.market_type == market_type.upper())
    
    if account_tier and account_tier.upper() != "ALL":
        query = query.filter(ProviderRuleSetModel.account_tier == account_tier.upper())
        
    if trailing_dd_type and trailing_dd_type.upper() != "ALL":
        query = query.filter(ProviderRuleSetModel.trailing_dd_type.ilike(f"%{trailing_dd_type}%"))
        
    if ea_bots_allowed and ea_bots_allowed.upper() != "ALL":
        if ea_bots_allowed.upper() == "PERMITTED":
            query = query.filter(ProviderRuleSetModel.ea_bots_allowed.ilike("%PERMITTED%"))
        else:
            query = query.filter(ProviderRuleSetModel.ea_bots_allowed == ea_bots_allowed.upper())
            
    if no_activation_fee is True:
        query = query.filter(ProviderRuleSetModel.activation_fee_usd == 0.0)
        
    if verification_status and verification_status.upper() != "ALL":
        query = query.filter(ProviderRuleSetModel.verification_status == verification_status.upper())
        
    if search:
        s = f"%{search.lower()}%"
        query = query.filter(
            (ProviderRuleSetModel.name.ilike(s)) |
            (ProviderRuleSetModel.provider_name.ilike(s)) |
            (ProviderRuleSetModel.platform.ilike(s))
        )
    
    # Order by Trust Score DESC, then Account Size ASC
    query = query.order_by(ProviderRuleSetModel.trust_score.desc(), ProviderRuleSetModel.account_size.asc())
    
    return [_format_provider(p) for p in query.all()]


@providers_router.get("/meta/summary")
def get_meta_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Return summary statistics of all cataloged prop firms."""
    all_providers = db.query(ProviderRuleSetModel).all()
    
    firms = set(p.provider_name for p in all_providers)
    futures_count = sum(1 for p in all_providers if p.market_type == "FUTURES")
    cfd_count = sum(1 for p in all_providers if p.market_type == "CFD")
    crypto_count = sum(1 for p in all_providers if p.market_type == "CRYPTO")
    promo_count = sum(1 for p in all_providers if (getattr(p, "discount_pct", 0) > 0 or getattr(p, "discount_code", None)))
    no_activation_count = sum(1 for p in all_providers if getattr(p, "activation_fee_usd", 0) == 0.0)
    
    last_verified = max([p.verified_at for p in all_providers if p.verified_at] or ["2026-08-21"])
    
    return {
        "total_firms": len(firms),
        "total_accounts": len(all_providers),
        "futures_accounts": futures_count,
        "cfd_accounts": cfd_count,
        "crypto_accounts": crypto_count,
        "active_promotions_count": promo_count,
        "no_activation_fee_accounts": no_activation_count,
        "last_sync_timestamp": datetime.utcnow().isoformat(),
        "last_verified_date": last_verified,
        "status": "ONLINE_CANONICAL"
    }


@providers_router.post("/sync")
def sync_prop_firms(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Synchronize / Refresh catalog with verified canonical data."""
    updated = 0
    created = 0
    now_str = datetime.utcnow().strftime("%Y-%m-%d")
    
    for item in PROP_FIRMS_CATALOG:
        item_copy = dict(item)
        item_copy["verified_at"] = now_str
        
        p = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.provider_id == item["provider_id"]).first()
        if p:
            for k, v in item_copy.items():
                setattr(p, k, v)
            updated += 1
        else:
            p_new = ProviderRuleSetModel(**item_copy)
            db.add(p_new)
            created += 1
            
    db.commit()
    
    return {
        "status": "SUCCESS",
        "message": f"Sincronización completada exitosamente. {updated} cuentas actualizadas, {created} nuevas registradas.",
        "timestamp": datetime.utcnow().isoformat(),
        "total_cataloged": len(PROP_FIRMS_CATALOG)
    }


@providers_router.get("/recommend")
def recommend_accounts(
    budget_usd: float = Query(100.0, description="Presupuesto disponible en USD para la compra"),
    use_bots: bool = Query(True, description="¿Vas a operar con bots automáticos?"),
    prefer_drawdown: str = Query("EOD", description="EOD, STATIC, INTRADAY"),
    market_pref: str = Query("FUTURES", description="FUTURES, CFD, CRYPTO, ALL"),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """Calcula y recomienda las mejores cuentas basándose en el perfil cuantitativo del usuario."""
    query = db.query(ProviderRuleSetModel)
    
    if market_pref != "ALL":
        query = query.filter(ProviderRuleSetModel.market_type == market_pref.upper())
        
    candidates = query.all()
    scored = []
    
    for p in candidates:
        score = float(p.trust_score)
        
        # Filtro de bots
        if use_bots:
            if "PROHIBITED" in p.ea_bots_allowed:
                score -= 60.0
            elif "PERMITTED" in p.ea_bots_allowed:
                score += 15.0
                
        # Filtro de Drawdown
        if prefer_drawdown.upper() == "EOD" and "EOD" in p.trailing_dd_type:
            score += 20.0
        elif prefer_drawdown.upper() == "STATIC" and "Static" in p.trailing_dd_type:
            score += 25.0
        elif prefer_drawdown.upper() == "INTRADAY" and "Intraday" in p.trailing_dd_type:
            score += 10.0
            
        # Bonificación por $0 activación
        if p.activation_fee_usd == 0.0:
            score += 15.0
            
        # Bonificación por coste accesible
        price = p.promo_price_usd or p.monthly_cost_usd or p.regular_price_usd or 100.0
        if price <= budget_usd:
            score += 15.0
        else:
            score -= (price - budget_usd) * 0.2
            
        # Bonificación por retiros rápidos
        if "Día 1" in (p.payout_frequency or "") or "Same Day" in (p.payout_frequency or ""):
            score += 10.0
            
        scored.append((score, p))
        
    # Ordenar por score decreciente
    scored.sort(key=lambda x: x[0], reverse=True)
    
    top_3 = scored[:3]
    results = []
    for rank, (score_val, item) in enumerate(top_3, 1):
        formatted = _format_provider(item)
        formatted["recommendation_rank"] = rank
        formatted["calculated_suitability_score"] = round(score_val, 1)
        results.append(formatted)
        
    return results


@providers_router.get("/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single provider rule set by ID."""
    p = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.provider_id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="PROVIDER_NOT_FOUND")
    return _format_provider(p)
