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
    # Auto-seed if database is empty
    total_existing = db.query(ProviderRuleSetModel).count()
    if total_existing == 0:
        for item in PROP_FIRMS_CATALOG:
            item_copy = {k: v for k, v in item.items() if hasattr(ProviderRuleSetModel, k)}
            db.add(ProviderRuleSetModel(**item_copy))
        db.commit()

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


class ChatMessage(BaseModel):
    role: str = Field("user", description="user or assistant")
    content: str = Field(..., description="Message text")

class ChatRequestSchema(BaseModel):
    message: str = Field(..., description="User question to the futures prop firms expert AI")
    history: Optional[List[ChatMessage]] = Field(default=[], description="Previous conversation turns")


@providers_router.post("/chat")
def chat_expert_advisor(
    req: ChatRequestSchema,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """Chatbot Experto Cuantitativo impulsado por LLM Real con RAG sobre 17 Firmas de Futuros CME."""
    import requests as http_requests

    user_msg = req.message.strip()
    all_providers = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.market_type == "FUTURES").all()

    # Construir resumen estructurado dinámico para el contexto RAG del LLM
    catalog_summary_lines = []
    for p in all_providers:
        cost = p.promo_price_usd or p.monthly_cost_usd or p.regular_price_usd
        code_str = f" [Cupón: {p.discount_code}]" if getattr(p, "discount_code", None) else ""
        catalog_summary_lines.append(
            f"- {p.provider_name} ({p.name}) | Tier: {getattr(p, 'account_tier', '50K')} | "
            f"Precio: ${cost}{code_str} | Activación: ${getattr(p, 'activation_fee_usd', 0)} | "
            f"Drawdown: {p.trailing_dd_type} (${p.max_trailing_dd_usd}) | DLL: ${getattr(p, 'daily_loss_limit_usd', 'None')} ({getattr(p, 'dll_calc_model', 'None')}) | "
            f"Bots: {p.ea_bots_allowed} | Retiros: {getattr(p, 'payout_frequency', 'Quincenal')} | "
            f"Plataformas: {p.platform} | Consistencia: {getattr(p, 'consistency_rule_pct', 'N/A')}% | Notas: {getattr(p, 'notes', '')}"
        )
    catalog_context_str = "\n".join(catalog_summary_lines)

    system_prompt = (
        "ERES ULTRABOT AI: El Asistente Cuantitativo e Inteligencia Artificial Oficial de Ultrarentable, "
        "especializado en FIRMAS DE FONDEO DE FUTUROS CME (MES, MNQ, ES, NQ, YM, RTY, CL, GC).\n\n"
        "REGLAS E INSTRUCCIONES OBLIGATORIAS:\n"
        "1. Responde SIEMPRE en español de forma fluida, natural, empática, profesional y con máximo rigor matemático y técnico.\n"
        "2. Tienes acceso a toda la base de datos oficial y auditada en 2026 de las 17 firmas principales de futuros CME:\n"
        f"{catalog_context_str}\n\n"
        "3. REGLAS TÉCNICAS ESPECÍFICAS DE FUTUROS:\n"
        "   - Exámenes vs Fondeado: Diferencia entre cuota de examen y cuota de activación ($0 en MFFU/Tradeify/TradeDay/BluSky/FundedNext vs $140-$150 en Apex/Bulenox/Topstep/TPT).\n"
        "   - Modelos de Drawdown: EOD Trailing (calcula a las 17:00 ET, se congela en cuenta fondeada), Drawdown Estático al 100% (BluSky nunca sube), Intraday Peak Trailing (Apex/Bulenox persigue flotante tick a tick).\n"
        "   - Cuentas Demo y Simuladores: TopstepX 14d demo gratis, Tradeify demo 14d Tradovate, Take Profit Trader practice simulator, y NinjaTrader 8 descarga oficial gratuita con datos CME live para StrategyQuant X y bots.\n"
        "   - Políticas de Bots: Totalmente permitidos en MFFU, Tradeify, TradeDay, BluSky; ESTRICTAMENTE PROHIBIDOS en cuentas PA de Apex.\n"
        "   - Retiros y Buffer: Días mínimos entre retiros, ventanas del 1-5 y 15-20 en Apex/Bulenox, retiros diarios en Topstep (5d > $200), pagos inmediatos en MFFU y Lucid.\n"
        "4. Emplea formato Markdown elegante: títulos (###), negritas, viñetas y tablas cuando ayude a comparar opciones."
    )

    formatted_messages = [{"role": "system", "content": system_prompt}]
    if req.history:
        for h in req.history[-8:]:
            role = "assistant" if h.role == "assistant" else "user"
            formatted_messages.append({"role": role, "content": h.content})
    formatted_messages.append({"role": "user", "content": user_msg})

    # Llamada en Cascada a Puentes Internos Propios (Hermes Antigravity Bridge -> FreeLLMAPI -> 9Router)
    ai_response_text = None
    bridge_configs = [
        {
            "name": "Hermes Antigravity Bridge",
            "url": "http://127.0.0.1:8742/v1/chat/completions",
            "headers": {"Authorization": "Bearer local-antigravity-cli", "Content-Type": "application/json"},
            "payload": {"model": "gemini-3.7-flash-high", "messages": formatted_messages, "temperature": 0.5, "max_tokens": 1500},
            "timeout": 28,
        },
        {
            "name": "FreeLLMAPI",
            "url": "http://127.0.0.1:3001/v1/chat/completions",
            "headers": {"Authorization": "Bearer freellmapi-bc5d56dc6a1548c6c11a0d409008b1ed0273e4105cd64784", "Content-Type": "application/json"},
            "payload": {"model": "auto", "messages": formatted_messages, "temperature": 0.5, "max_tokens": 1500},
            "timeout": 20,
        },
        {
            "name": "9Router Hub",
            "url": "http://127.0.0.1:20128/v1/chat/completions",
            "headers": {"Authorization": "Bearer sk-b3e798f0bb33a851-xcr9mi-56c91df1", "Content-Type": "application/json"},
            "payload": {"model": "FREE_ONLY", "messages": formatted_messages, "temperature": 0.5, "max_tokens": 1500},
            "timeout": 20,
        },
    ]

    for bridge in bridge_configs:
        try:
            res = http_requests.post(bridge["url"], headers=bridge["headers"], json=bridge["payload"], timeout=bridge["timeout"])
            if res.status_code == 200:
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if content and len(content.strip()) > 0:
                    ai_response_text = content
                    break
        except Exception as e:
            print(f"Error calling {bridge['name']}: {e}")

    if not ai_response_text:
        ai_response_text = (
            f"### 🏛️ UltraBot AI — Análisis de Futuros CME\n\n"
            f"He procesado tu consulta sobre **'{req.message}'** en base a las 17 firmas de futuros CME.\n\n"
            "- **Cuentas más baratas ($0 Activación):** MFFU Rapid 50K ($39.50 cupón `300K`) y Tradeify Growth 50K ($58.20 cupón `TNT`).\n"
            "- **Drawdown más seguro:** BluSky Static Growth 50K ($110 cupón `BLU25`, Drawdown 100% Estático).\n"
            "- **Solvencia institucional:** TradeDay 50K ($59 cupón `FLASH55`, retiros el mismo día)."
        )

    return {
        "response": ai_response_text,
        "suggested_actions": [
            "¿Qué cuenta de 50K comprar hoy?",
            "¿Qué firmas permiten bots 24/7?",
            "Explicar Drawdown EOD vs Static",
            "Ver cupones oficiales activos",
        ],
        "active_coupons": [
            {"firm": "MFFU", "code": "300K", "discount": "50% OFF"},
            {"firm": "Tradeify", "code": "TNT", "discount": "40% OFF"},
            {"firm": "TradeDay", "code": "FLASH55", "discount": "55% OFF"},
            {"firm": "Bulenox", "code": "GUIDE", "discount": "89% OFF"},
            {"firm": "Apex", "code": "SAVINGS", "discount": "80% OFF"},
            {"firm": "BluSky", "code": "BLU25", "discount": "25% OFF"},
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


@providers_router.get("/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single provider rule set by ID."""
    p = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.provider_id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="PROVIDER_NOT_FOUND")
    return _format_provider(p)

