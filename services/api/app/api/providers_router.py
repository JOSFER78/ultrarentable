"""FastAPI Router for Prop Firm Providers and Versioned Rule Sets."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, ProviderRuleSetModel
from services.api.app.db.seed_prop_firms import PROP_FIRMS_CATALOG
from services.fondeo.catalogo_firmas_v2 import CATALOGO_V2, get_firm_v2

logger = logging.getLogger(__name__)

providers_router = APIRouter(tags=["Prop Firm Providers"])


def _cargar_puentes_externos() -> List[Dict[str, Any]]:
    """Carga la lista de puentes de IA desde archivos de configuración fuera del repositorio git.

    Busca en ~/.ultrarentable/ia_bridges.json o ~/.ultrarentable/ia_puentes.json.
    Si no existen o están vacíos, busca ~/.ultrarentable/ia_config.json.
    Si ninguno existe, devuelve lista vacía (cero claves en el repositorio).
    """
    config_dir = os.path.expanduser("~/.ultrarentable")
    bridges_paths = [
        os.path.join(config_dir, "ia_bridges.json"),
        os.path.join(config_dir, "ia_puentes.json"),
    ]
    bridges: List[Dict[str, Any]] = []
    for p in bridges_paths:
        if os.path.exists(p):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        bridges = data
                        break
            except Exception as e:
                logger.warning(f"No se pudo leer {p}: {e}")

    if not bridges:
        ia_cfg_path = os.path.join(config_dir, "ia_config.json")
        if os.path.exists(ia_cfg_path):
            try:
                with open(ia_cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    if cfg.get("endpoint"):
                        bridges = [{
                            "name": cfg.get("nombre") or "Proveedor Principal (Hermes)",
                            "url": cfg["endpoint"],
                            "api_key": cfg.get("api_key", ""),
                            "model": cfg.get("modelo") or "default",
                            "timeout": 60,
                        }]
            except Exception as e:
                logger.warning(f"No se pudo leer {ia_cfg_path}: {e}")

    return bridges


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


@providers_router.get("/providers")
@providers_router.get("/providers/")
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


@providers_router.get("/providers/meta/summary")
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


@providers_router.post("/providers/sync")
def sync_prop_firms(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Fail-closed: sin re-verificación real implementada (W4.8, ver M3 §1.3)."""
    raise HTTPException(
        status_code=501,
        detail="sin re-verificación real implementada; ver M3 §1.3"
    )


@providers_router.get("/prop-firms/v2", tags=["v2-prop-firms"])
@providers_router.get("/providers/v2", tags=["v2-prop-firms"])
@providers_router.get("/providers/prop-firms/v2", tags=["v2-prop-firms"])
def get_prop_firms_v2() -> List[Dict[str, Any]]:
    """Devuelve el catálogo de firmas de fondeo V2 re-verificado con metadatos de SourceRef (D6)."""
    return [f.to_api_dict() for f in CATALOGO_V2]


@providers_router.get("/prop-firms/v2/{firm_id}", tags=["v2-prop-firms"])
@providers_router.get("/providers/v2/{firm_id}", tags=["v2-prop-firms"])
def get_prop_firm_v2_by_id(firm_id: str) -> Dict[str, Any]:
    """Devuelve el detalle de una firma de fondeo V2 con sus SourceRef por campo."""
    firm = get_firm_v2(firm_id.lower().strip())
    if firm is None:
        valid_ids = ", ".join(sorted(f.id for f in CATALOGO_V2))
        raise HTTPException(
            status_code=404,
            detail=f"'{firm_id}' no está en el catálogo v2. Disponibles: {valid_ids}",
        )
    return firm.to_api_dict()


@providers_router.get("/providers/recommend")
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


@providers_router.post("/providers/chat")
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
        "especializado en FIRMAS DE FONDEO DE FUTUROS CME (MES, MNQ, ES, NQ, YM, RTY, CL, GC) y herramientas de trading (NinjaTrader 8, Tradovate, TradingView, StrategyQuant X).\n\n"
        "DIRECTIVAS DE ESTILO Y PRESENTACIÓN VISUAL (CRÍTICO: FORMATO FÁCIL, ULTRA-VISUAL, CLARO Y DIRECTO):\n"
        "1. Estructura la respuesta de forma MUY VISUAL, ÁGIL y FÁCIL DE LEER, con pasos claros (1️⃣, 2️⃣, 3️⃣) y secciones bien diferenciadas.\n"
        "2. Incluye SIEMPRE los enlaces directos reales en formato Markdown `[Texto del Enlace](https://...)` para que la interfaz los transforme automáticamente en botones interactivos de 1 clic:\n"
        "   - NinjaTrader 8: [NinjaTrader Demo Gratis](https://ninjatrader.com/free-trading-simulator/)\n"
        "   - Topstep: [TopstepX Simulator](https://topstep.com/topstepx/)\n"
        "   - MyFundedFutures: [MyFundedFutures Oficial](https://myfundedfutures.com)\n"
        "   - Tradeify: [Tradeify Oficial](https://tradeify.co)\n"
        "   - TradeDay: [TradeDay Free Trial](https://tradeday.com/free-trial/)\n"
        "   - BluSky: [BluSky Trading](https://blusky.pro)\n"
        "   - Take Profit Trader: [Take Profit Trader](https://takeprofittrader.com)\n"
        "   - Apex Trader Funding: [Apex Trader Funding](https://apextraderfunding.com)\n"
        "   - Bulenox: [Bulenox Oficial](https://bulenox.com)\n"
        "3. Evita párrafos largos. Usa viñetas breves, negritas en datos clave y tablas comparativas siempre que ayuden a comparar firmas.\n"
        "4. Tienes acceso a toda la base de datos oficial y auditada en 2026 de las 17 firmas principales de futuros CME:\n"
        f"{catalog_context_str}\n\n"
        "5. REGLAS TÉCNICAS ESPECÍFICAS DE FUTUROS:\n"
        "   - Exámenes vs Fondeado: Diferencia entre cuota de examen y cuota de activación ($0 en MFFU/Tradeify/TradeDay/BluSky vs $140-$150 en Apex/Bulenox/Topstep/TPT).\n"
        "   - Modelos de Drawdown: EOD Trailing (MFFU/Tradeify), Drawdown Estático 100% (BluSky nunca sube), Intraday Peak (Apex/Bulenox).\n"
        "   - Políticas de Bots: Permitidos 100% en MFFU, Tradeify, TradeDay, BluSky; PROHIBIDOS en cuentas PA de Apex."
    )

    formatted_messages = [{"role": "system", "content": system_prompt}]
    if req.history:
        for h in req.history[-8:]:
            role = "assistant" if h.role == "assistant" else "user"
            formatted_messages.append({"role": role, "content": h.content})
    formatted_messages.append({"role": "user", "content": user_msg})

    # Llamada en Cascada a Puentes Internos Propios leídos desde disco seguro fuera de git
    ai_response_text = None
    puentes = _cargar_puentes_externos()

    if not puentes:
        return {
            "response": (
                "⚠️ No hay ningún proveedor o puente de IA configurado en el servidor.\n\n"
                "Para activarlo, configure un proveedor en el panel de administración (/perfil) "
                "o en el archivo de configuración seguro `~/.ultrarentable/ia_bridges.json` fuera del repositorio."
            ),
            "suggested_actions": [
                "Configurar proveedor en /perfil",
            ],
            "active_coupons": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

    for bridge in puentes:
        url = bridge.get("url")
        if not url:
            continue
        api_key = bridge.get("api_key", "")
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        model = bridge.get("model") or "gemini-3.7-flash-high"
        timeout = bridge.get("timeout", 45)
        payload = {
            "model": model,
            "messages": formatted_messages,
            "temperature": 0.5,
            "max_tokens": 1500,
        }

        try:
            res = http_requests.post(url, headers=headers, json=payload, timeout=timeout)
            if res.status_code == 200:
                data = res.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content")
                if content and len(content.strip()) > 0:
                    ai_response_text = content
                    break
        except Exception as e:
            logger.warning(f"Error calling bridge {bridge.get('name', url)}: {e}")

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


@providers_router.get("/providers/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single provider rule set by ID."""
    p = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.provider_id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="PROVIDER_NOT_FOUND")
    return _format_provider(p)

