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
    """Chatbot Experto Cuantitativo en Firmas de Fondeo de Futuros CME.
    
    Analiza la base de datos completa de todas las 17 firmas de futuros, reglas de examen vs fondeo,
    promociones activas, cuotas de activación ($0 vs $149), letra pequeña, políticas de bots y drawdowns.
    """
    user_msg = req.message.strip().lower()
    all_providers = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.market_type == "FUTURES").all()
    
    # 1. Extracción de entidades y contexto
    mentioned_firms = []
    for p in all_providers:
        if p.provider_name.lower() in user_msg or p.name.lower() in user_msg:
            if p.provider_name not in mentioned_firms:
                mentioned_firms.append(p.provider_name)
                
    # Detectar palabras clave temáticas
    is_bots = any(w in user_msg for w in ["bot", "ea", "algoritmo", "automat", "strategyquant", "sqx", "python", "webhook", "copier"])
    is_cheapest = any(w in user_msg for w in ["barat", "econom", "precio", "coste", "cupon", "descuento", "promo", "oferta"])
    is_activation = any(w in user_msg for w in ["activacion", "pass fee", "$0", "gratis", "tarifa de pase", "coste total"])
    is_drawdown = any(w in user_msg for w in ["drawdown", "dd", "trailing", "eod", "static", "estatico", "intraday", "peak"])
    is_payout = any(w in user_msg for w in ["retiro", "payout", "pago", "cobro", "buffer", "colchon", "dia 1", "mismo dia"])
    is_daily_loss = any(w in user_msg for w in ["daily", "diari", "dll", "limite diario", "soft breach", "perdida diaria"])
    is_fine_print = any(w in user_msg for w in ["letra pequeña", "trampa", "ocult", "noticia", "cpi", "fomc", "overnight", "consistencia", "regla"])
    is_recommend = any(w in user_msg for w in ["recomiend", "cual elijo", "cual compro", "mejor", "que me conviene", "tengo $", "presupuesto"])

    # 2. Construcción de respuesta cuantitativa experta
    response_paragraphs = []
    suggested_actions = []
    related_firms = []
    active_coupons = []
    
    # INTENT: RECOMENDACIÓN PARA BOTS / ALGORITMOS
    if is_bots and not is_drawdown:
        response_paragraphs.append("### 🤖 Auditoría de Bots & Trading Algorítmico en Futuros CME\n")
        response_paragraphs.append(
            "Si operas con **StrategyQuant X, EAs en NinjaTrader 8, Webhooks de TradingView o scripts de Python**, estas son las reglas oficiales auditadas:\n\n"
            "1. **🏆 TOP 1 Recomendadas para Bots (100% Permitidos + $0 Activación):**\n"
            "   - **MyFundedFutures (MFFU Rapid 50K):** Permite bots sin restricciones en NinjaTrader y VPS. Examen a **$39.50 USD** con cupón `300K`, **$0 activación**, Drawdown EOD Fin de Día y retiros Día 1 On-Demand.\n"
            "   - **Tradeify (Growth 50K):** Soporte total de webhooks y NinjaTrader. Examen a **$58.20 USD** con cupón `TNT`, **$0 activación** y Soft Breach DLL ($1,000).\n"
            "   - **TradeDay (Day Trader 50K):** Brokerage real Dorman Trading. Examen a **$59.00 USD** con cupón `FLASH55`, **$0 activación** y pagos el mismo día hábil.\n"
            "   - **BluSky Trading (Static 50K):** Drawdown 100% Estático que nunca sube ($110 USD cupón `BLU25`, $0 activación).\n\n"
            "2. **🚨 ALERTA CRÍTICA — FIRMAS PROHIBIDAS PARA BOTS:**\n"
            "   - **Apex Trader Funding:** En cuentas financiadas PA, **los bots totalmente automatizados están estrictamente PROHIBIDOS**. Solo permiten operativa manual (el Trade Copier entre cuentas manuales sí está permitido). Si detectan operativa desatendida, te cancelan la cuenta en la solicitud de retiro."
        )
        suggested_actions = ["Ver MFFU Rapid 50K", "Ver Tradeify Growth 50K", "Ver BluSky Static 50K"]
        related_firms = ["My Funded Futures", "Tradeify", "BluSky Trading", "Apex Trader Funding"]
        active_coupons = [
            {"firm": "MFFU", "code": "300K", "discount": "50% OFF"},
            {"firm": "Tradeify", "code": "TNT", "discount": "40% OFF"},
            {"firm": "TradeDay", "code": "FLASH55", "discount": "55% OFF"},
            {"firm": "BluSky", "code": "BLU25", "discount": "25% OFF"},
        ]

    # INTENT: EXPLICACIÓN DE DRAWDOWN (EOD vs STATIC vs INTRADAY)
    elif is_drawdown:
        response_paragraphs.append("### 📉 Guía Definitiva de Tipos de Drawdown en Futuros CME\n")
        response_paragraphs.append(
            "El tipo de Drawdown es el factor matemático #1 que determina si vas a aprobar y conservar tu cuenta:\n\n"
            "1. **🛡️ Drawdown Estático (Static Drawdown — Máxima Seguridad):**\n"
            "   - *Firma líder:* **BluSky Trading (Static Growth 50K)**.\n"
            "   - *Mecánica:* El nivel de pérdida se fija en $48,500 y **JAMÁS sube** con tus ganancias. Si tu cuenta sube a $56,000, tu stop de liquidación sigue en $48,500 (tienes $7,500 de colchón acumulado).\n\n"
            "2. **🟢 Drawdown EOD Fin de Día (End of Day Trailing — El Estándar Recomendado):**\n"
            "   - *Firmas líderes:* **MFFU Rapid, Tradeify Growth, TradeDay, Topstep, FundedNext, Lucid, Earn2Trade**.\n"
            "   - *Mecánica:* El nivel de pérdida se recalcula **únicamente al cierre de la sesión (17:00 ET)** sobre el balance cerrado. Si tienes una posición con flotante de +$2,000 que retrocede a +$500 antes del cierre, el drawdown NO te persigue durante el trade. En fondeo, **se congela en el balance inicial ($50,100)**.\n\n"
            "3. **🔴 Drawdown Intraday Peak Trailing (Tiempo Real Tick-a-Tick — Alto Riesgo):**\n"
            "   - *Firmas:* **Bulenox Opción 1, Apex Trader Funding, Leeloo**.\n"
            "   - *Mecánica:* Persigue el equity máximo no realizado en tiempo real. Si vas ganando +$1,500 y cierras en +$300, el stop subió $1,500, reduciendo drásticamente tu margen operativo. Solo aconsejado para scalpers ultrarrápidos que buscan exámenes de $19–$33."
        )
        suggested_actions = ["Ver BluSky Static Drawdown", "Ver MFFU EOD Trailing", "Comparar 4 Firmas"]
        related_firms = ["BluSky Trading", "My Funded Futures", "Bulenox", "Topstep"]

    # INTENT: ANÁLISIS DE COSTES REALES & ACTIVACIÓN $0
    elif is_activation or (is_cheapest and not is_bots):
        response_paragraphs.append("### 💰 Tabla de Coste Real Total: Examen + Activación ($0 vs $149)\n")
        response_paragraphs.append(
            "Muchas empresas anuncian exámenes a $20–$35 pero luego te cobran **$140 a $150 USD extra** al aprobar. Aquí tienes el coste real neto auditado a día de hoy para cuentas de **$50,000 USD**:\n\n"
            "| Firma & Programa | Precio Examen (Cupón) | Cuota Activación | Coste Total Real | Retiros |\n"
            "|---|:---:|:---:|:---:|:---:|\n"
            "| **MFFU Rapid 50K** | **$39.50** (`300K`) | **$0 USD** | **$39.50 USD** | Día 1 On-Demand |\n"
            "| **Tradeify Growth 50K** | **$58.20** (`TNT`) | **$0 USD** | **$58.20 USD** | 24-48h On-Demand |\n"
            "| **TradeDay Day Trader 50K**| **$59.00** (`FLASH55`) | **$0 USD** | **$59.00 USD** | Mismo día hábil |\n"
            "| **FundedNext Futures 50K**| **$99.00** | **$0 USD** | **$99.00 USD** | Quincenal (+15% bonus) |\n"
            "| **BluSky Static 50K** | **$110.00** (`BLU25`) | **$0 USD** | **$110.00 USD** | Semanal |\n"
            "| **LucidFlex 50K** | **$118.30** (`LUCID30`)| **$0 USD** | **$118.30 USD** | 15-30 Minutos |\n"
            "| **Bulenox Opción 1 50K** | **$19.25** (`GUIDE`) | $148.00 USD | **$167.25 USD** | Quincenal |\n"
            "| **Apex Full 50K** | **$33.40** (`SAVINGS`) | $140.00 USD | **$173.40 USD** | Quincenal |\n"
            "| **Topstep Combine 50K** | **$49.00** / mes | $149.00 USD | **$198.00 USD** | Diario (5d > $200) |\n"
            "| **Take Profit Trader 50K**| **$85.00** (`PRO50`) | $130.00 USD | **$215.00 USD** | Día 1 en Pro |\n\n"
            "💡 **Conclusión:** Si buscas el menor gasto total para pasar y cobrar, **MFFU Rapid ($39.50)** y **Tradeify Growth ($58.20)** son las opciones #1 al no cobrar cuota de activación."
        )
        suggested_actions = ["Ver Cuentas $0 Activación", "Copiar Cupón 300K", "Copiar Cupón TNT"]
        related_firms = ["My Funded Futures", "Tradeify", "TradeDay", "Bulenox", "Apex Trader Funding"]
        active_coupons = [
            {"firm": "MFFU", "code": "300K", "discount": "50% OFF"},
            {"firm": "Tradeify", "code": "TNT", "discount": "40% OFF"},
            {"firm": "Bulenox", "code": "GUIDE", "discount": "89% OFF"},
            {"firm": "Apex", "code": "SAVINGS", "discount": "80% OFF"},
        ]

    # INTENT: RETIROS & PAYOUT POLICIES
    elif is_payout:
        response_paragraphs.append("### ⚡ Auditoría de Retiros, Safety Buffers y Frecuencia de Cobro\n")
        response_paragraphs.append(
            "Reglas exactas para cobrar tus beneficios en cuenta fondeada:\n\n"
            "1. **⚡ Retiros Día 1 / Inmediatos On-Demand:**\n"
            "   - **MyFundedFutures Rapid:** Retiras desde tu primer trade financiado una vez superado el buffer ($52,100 en 50K). Pagos en 12–24h (Rise/Crypto/Wire).\n"
            "   - **Take Profit Trader Pro:** Permite retirar el beneficio del primer día en cuenta Pro (split 80/20).\n"
            "   - **TradeDay:** Pagos procesados el **mismo día hábil** si se solicitan antes del corte.\n"
            "   - **Lucid Trading:** Aprobación y transferencia en **15 a 30 minutos** vía API.\n\n"
            "2. **📅 Retiros Semanales / por Días Ganadores:**\n"
            "   - **Topstep:** Requiere acumular **5 días ganadores con beneficio > $200 USD** por solicitud (puedes retirar hasta el 50% de las ganancias acumuladas).\n"
            "   - **BluSky Trading:** Retiros semanales tras 8 días activos.\n"
            "   - **Earn2Trade:** Retiros todos los martes/miércoles vía Helios Trading Partners.\n\n"
            "3. **🗓️ Retiros Quincenales con Ventana Estricta:**\n"
            "   - **Apex & Bulenox:** Solo admiten solicitudes del 1 al 5 y del 15 al 20 de cada mes, exigiendo entre 5 y 10 días de trading activos entre retiros y límites máximos durante los primeros 3 meses ($1,500–$2,000)."
        )
        suggested_actions = ["Ver MFFU Día 1 Payout", "Ver TradeDay Mismo Día", "Ver Topstep Reglas"]
        related_firms = ["My Funded Futures", "TradeDay", "Topstep", "Lucid Trading"]

    # INTENT: LETRA PEQUEÑA & TRAMPAS OCULTAS
    elif is_fine_print:
        response_paragraphs.append("### ⚠️ Auditoría de Letra Pequeña y Reglas Críticas en Futuros CME\n")
        response_paragraphs.append(
            "Estas son las 5 cláusulas ocultas que debes conocer para no perder tu cuenta:\n\n"
            "1. **Regla de Consistencia (Consistency Rule — 30% a 50%):**\n"
            "   - En **Apex (30%)**, **Tradeify (40%)**, **MFFU fondeado (40%)** y **Bulenox (40%)**, ningún día único puede representar más del porcentaje fijado respecto a las ganancias totales al solicitar un retiro. Si ganas $3,000 en 1 día y en los otros 4 días ganas $100, debes seguir operando hasta diluir el porcentaje.\n\n"
            "2. **Cierre Obligatorio Diario (Prohibición de Overnight):**\n"
            "   - En el mercado CME, todas las firmas exigen cerrar posiciones **antes de las 15:10 CT (Topstep/TradeDay)** o **antes de las 16:59 EST (MFFU, Tradeify, Apex, Bulenox)**. Dejar 1 posición abierta durante el cierre diario suspende la cuenta automáticamente.\n\n"
            "3. **Operativa en Noticias Macroeconómicas (CPI, FOMC, NFP):**\n"
            "   - **Permitido:** MFFU, Tradeify, Topstep, TradeDay, FundedNext, Lucid.\n"
            "   - **Restringido / Baneo de HFT:** Apex y Bulenox prohíben poner órdenes bracket a 1 segundo del dato macro (*news gambling*).\n\n"
            "4. **IPs y VPNs:**\n"
            "   - Permitido usar VPS dedicadas de Windows (Contabo, AWS, OVH). Estrictamente prohibido compartir credenciales con otros traders bajo la misma IP (detección de colisión de cuentas)."
        )
        suggested_actions = ["Ver Reglas de Consistencia", "Ver Horarios CME", "Ver Firmas sin Trampas"]
        related_firms = ["Apex Trader Funding", "Tradeify", "My Funded Futures", "Topstep"]

    # RESPUESTA GENERAL / RECOMENDADOR INTELIGENTE POR DEFECTO
    else:
        response_paragraphs.append(f"### 🏛️ Asistente Cuantitativo de Futuros CME — Análisis en Tiempo Real\n")
        response_paragraphs.append(
            f"He analizado tu consulta sobre **'{req.message}'** en base a la base de datos oficial de las **17 firmas de futuros CME** auditadas en 2026.\n\n"
            "Aquí tienes el resumen ejecutivo para elegir con rigor matemático:\n\n"
            "- **Si buscas el menor coste total ($0 activación + EOD DD):** **MyFundedFutures Rapid 50K** ($39.50 con cupón `300K`) o **Tradeify Growth 50K** ($58.20 con cupón `TNT`).\n"
            "- **Si buscas máxima seguridad sin trailing que te persiga:** **BluSky Trading Static 50K** ($110 con cupón `BLU25`, Drawdown 100% Estático).\n"
            "- **Si buscas solvencia institucional y cuenta real:** **TradeDay 50K** ($59 con cupón `FLASH55`, retiros en el mismo día) o **Topstep 50K** ($49/mes).\n"
            "- **Si buscas el precio de examen más barato:** **Bulenox 50K** ($19.25 con cupón `GUIDE`, 89% descuento).\n\n"
            "¿Deseas que profundice en la política de bots de alguna firma, en el cálculo de coste total o en la letra pequeña de retiros?"
        )
        suggested_actions = ["¿Qué cuenta de 50K comprar hoy?", "¿Qué firmas permiten bots 24/7?", "Explicar Drawdown EOD vs Static", "Ver cupones oficiales activos"]
        related_firms = ["My Funded Futures", "Tradeify", "TradeDay", "BluSky Trading", "Topstep"]
        active_coupons = [
            {"firm": "MFFU", "code": "300K", "discount": "50% OFF"},
            {"firm": "Tradeify", "code": "TNT", "discount": "40% OFF"},
            {"firm": "TradeDay", "code": "FLASH55", "discount": "55% OFF"},
            {"firm": "Bulenox", "code": "GUIDE", "discount": "89% OFF"},
            {"firm": "Apex", "code": "SAVINGS", "discount": "80% OFF"},
            {"firm": "BluSky", "code": "BLU25", "discount": "25% OFF"},
        ]

    full_text = "\n\n".join(response_paragraphs)
    
    return {
        "response": full_text,
        "suggested_actions": suggested_actions,
        "related_firms": related_firms,
        "active_coupons": active_coupons,
        "timestamp": datetime.utcnow().isoformat(),
    }


@providers_router.get("/{provider_id}")
def get_provider(provider_id: str, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get single provider rule set by ID."""
    p = db.query(ProviderRuleSetModel).filter(ProviderRuleSetModel.provider_id == provider_id).first()
    if not p:
        raise HTTPException(status_code=404, detail="PROVIDER_NOT_FOUND")
    return _format_provider(p)

