"""Catálogo de Prop Firms V2 — Fuente Canónica Re-verificada con SourceRef (D6).

Este catálogo implementa la directiva D6:
- Cada dato investigado lleva su `SourceRef` (confidence, url, captured_at, note).
- confidence in {"fetch", "ws_official", "unverified"}.
- NUNCA url == "" (cadena vacía).
- Si un valor es None, confidence == "unverified" y url is None.
- Si un valor es distinto de None, confidence in {"fetch", "ws_official"} y url no vacía.
- Cero valores inventados o heredados del corpus sin verificación primaria.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Literal, Optional, Tuple

Confidence = Literal["fetch", "ws_official", "unverified"]


@dataclass(frozen=True)
class SourceRef:
    """Referencia de procedencia y trazabilidad de un dato en el catálogo."""
    confidence: Confidence
    url: Optional[str] = None
    captured_at: Optional[str] = None
    note: str = ""


@dataclass(frozen=True)
class FirmaV2:
    """Entidad inmutable de una firma de fondeo con metadatos de riesgo, economía y procedencia."""
    id: str
    nombre: str

    # Parámetros de riesgo
    trailing_dd_tipo: Optional[str]
    trailing_dd_tipo_source: SourceRef

    trailing_dd_valor_50k: Optional[float]
    trailing_dd_valor_source: SourceRef

    perdida_diaria_limite_50k: Optional[float]
    perdida_diaria_source: SourceRef

    consistencia_pct: Optional[float]
    consistencia_source: SourceRef

    min_dias_trading: Optional[int]
    min_dias_source: SourceRef

    max_micros_50k: Optional[int]
    max_micros_source: SourceRef

    hora_cierre_obligatoria: Optional[str]
    hora_cierre_source: SourceRef

    # Parámetros económicos
    precio_examen_50k: Optional[float]
    precio_examen_source: SourceRef

    coste_activacion_50k: Optional[float]
    coste_activacion_source: SourceRef

    payout_split_pct: Optional[float]
    payout_split_source: SourceRef

    # Reglas de ejecución / automatización
    vps_permitido: Optional[bool]
    vps_permitido_source: SourceRef

    def campos_con_fuente(self) -> List[Tuple[str, Any, SourceRef]]:
        """Devuelve la lista de tuplas (nombre_campo, valor, source_ref) para validación D6."""
        return [
            ("trailing_dd_tipo", self.trailing_dd_tipo, self.trailing_dd_tipo_source),
            ("trailing_dd_valor_50k", self.trailing_dd_valor_50k, self.trailing_dd_valor_source),
            ("perdida_diaria_limite_50k", self.perdida_diaria_limite_50k, self.perdida_diaria_source),
            ("consistencia_pct", self.consistencia_pct, self.consistencia_source),
            ("min_dias_trading", self.min_dias_trading, self.min_dias_source),
            ("max_micros_50k", self.max_micros_50k, self.max_micros_source),
            ("hora_cierre_obligatoria", self.hora_cierre_obligatoria, self.hora_cierre_source),
            ("precio_examen_50k", self.precio_examen_50k, self.precio_examen_source),
            ("coste_activacion_50k", self.coste_activacion_50k, self.coste_activacion_source),
            ("payout_split_pct", self.payout_split_pct, self.payout_split_source),
            ("vps_permitido", self.vps_permitido, self.vps_permitido_source),
        ]

    def to_api_dict(self) -> Dict[str, Any]:
        """Serializa la firma a un diccionario estructurado donde cada campo contiene su valor y su SourceRef."""
        d: Dict[str, Any] = {
            "id": self.id,
            "nombre": self.nombre,
        }
        for campo, val, src in self.campos_con_fuente():
            src_dict = {
                "confidence": src.confidence,
                "url": src.url,
                "captured_at": src.captured_at,
                "note": src.note,
            }
            d[campo] = {
                "valor": val,
                "source": src_dict,
            }
            d[f"{campo}_source"] = src_dict
        return d


CATALOGO_V2: Tuple[FirmaV2, ...] = (
    # 1. Topstep
    FirmaV2(
        id="topstep",
        nombre="Topstep",
        trailing_dd_tipo="EOD",
        trailing_dd_tipo_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit",
            captured_at="2026-09-01",
            note="The MLL updates at the end of each trading day but is monitored in real time throughout the session. Both realized and unrealized P&L count toward it.",
        ),
        trailing_dd_valor_50k=2000.0,
        trailing_dd_valor_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit",
            captured_at="2026-09-01",
            note="50K: $2,000 · 100K: $3,000 · 150K: $4,500",
        ),
        perdida_diaria_limite_50k=None,
        perdida_diaria_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Existe DLL en Topstep pero el importe en USD para 50K es no verificable en fuente primaria directa.",
        ),
        consistencia_pct=50.0,
        consistencia_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284208",
            captured_at="2026-09-01",
            note="Your single best day of profit must stay at or below 50% of your Profit Target.",
        ),
        min_dias_trading=2,
        min_dias_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284197",
            captured_at="2026-09-01",
            note="Combine aprobable en 2 días de trading",
        ),
        max_micros_50k=50,
        max_micros_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284197",
            captured_at="2026-09-01",
            note="50K: 5 minis / 50 micros",
        ),
        hora_cierre_obligatoria="15:10 CT",
        hora_cierre_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284206",
            captured_at="2026-09-01",
            note="All positions must be closed by 3:10 PM CT every weekday.",
        ),
        precio_examen_50k=85.0,
        precio_examen_source=SourceRef(
            confidence="fetch",
            url="https://www.topstep.com/no-activation-fee",
            captured_at="2026-09-01",
            note="$85/mes suscripción mensual en ruta sin tarifa de activación",
        ),
        coste_activacion_50k=0.0,
        coste_activacion_source=SourceRef(
            confidence="fetch",
            url="https://www.topstep.com/no-activation-fee",
            captured_at="2026-09-01",
            note="$0 tarifa de activación en ruta sin activación",
        ),
        payout_split_pct=90.0,
        payout_split_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/8284233",
            captured_at="2026-09-01",
            note="90/10 payout split",
        ),
        vps_permitido=False,
        vps_permitido_source=SourceRef(
            confidence="fetch",
            url="https://help.topstep.com/en/articles/11187768-topstepx-api-access",
            captured_at="2026-09-01",
            note="All trading activity must originate from your personal device. The use of VPS, VPNs, and remote servers is prohibited by Topstep's Terms of Use.",
        ),
    ),

    # 2. Apex Trader Funding
    FirmaV2(
        id="apex",
        nombre="Apex Trader Funding",
        trailing_dd_tipo="INTRADAY_FLOATING",
        trailing_dd_tipo_source=SourceRef(
            confidence="ws_official",
            url="https://apextraderfunding.com/help-center/evaluation-accounts-ea/intraday-trailing-drawdown-evaluations/",
            captured_at="2026-09-01",
            note="Apex ofrece dos productos paralelos desde marzo 2026: EOD e Intraday trailing.",
        ),
        trailing_dd_valor_50k=None,
        trailing_dd_valor_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Importes de drawdown por tamaño 2026 no verificables con fuente primaria directa por bloqueo 403.",
        ),
        perdida_diaria_limite_50k=None,
        perdida_diaria_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="No verificable cifra exacta oficial de DLL.",
        ),
        consistencia_pct=50.0,
        consistencia_source=SourceRef(
            confidence="ws_official",
            url="https://apextraderfunding.com/help-center/legacy-helpful-items/what-are-the-consistency-rules-for-legacy-pa-and-funded-accounts/",
            captured_at="2026-09-01",
            note="50% del beneficio usado en solicitud, aplicado en payout de Performance Account.",
        ),
        min_dias_trading=1,
        min_dias_source=SourceRef(
            confidence="ws_official",
            url="https://apextraderfunding.com/help-center/evaluation-accounts-ea/legacy-evaluation-rules/",
            captured_at="2026-09-01",
            note="Evaluación EOD aprobable en 1 día de trading.",
        ),
        max_micros_50k=None,
        max_micros_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="No verificable con cifras fiables 2026.",
        ),
        hora_cierre_obligatoria=None,
        hora_cierre_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Flat time no localizado en fuentes oficiales disponibles.",
        ),
        precio_examen_50k=None,
        precio_examen_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Precios regulares 2026 no verificables con fuente primaria directa.",
        ),
        coste_activacion_50k=None,
        coste_activacion_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Activación no verificable con fuente primaria fiable.",
        ),
        payout_split_pct=None,
        payout_split_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Cifra exacta 2026 no verificable.",
        ),
        vps_permitido=None,
        vps_permitido_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="VPN/proxy prohibido para ocultar identidad; VPS no aclarado explícitamente en ToS.",
        ),
    ),

    # 3. My Funded Futures (MFFU)
    FirmaV2(
        id="mffu",
        nombre="My Funded Futures",
        trailing_dd_tipo="EOD",
        trailing_dd_tipo_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="Rapid en evaluación = EOD; en Sim-Funded pasa a Intraday.",
        ),
        trailing_dd_valor_50k=2000.0,
        trailing_dd_valor_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="50K: $2,000 de trailing drawdown",
        ),
        perdida_diaria_limite_50k=None,
        perdida_diaria_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="MFFU no tiene Daily Loss Limit en planes Rapid (diferenciador de marca confirmado por fetch).",
        ),
        consistencia_pct=50.0,
        consistencia_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="Rapid: 50% consistencia solo en evaluación",
        ),
        min_dias_trading=2,
        min_dias_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="2 días mínimos para evaluación Rapid",
        ),
        max_micros_50k=50,
        max_micros_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="50K: 5 minis / 50 micros",
        ),
        hora_cierre_obligatoria=None,
        hora_cierre_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Flat time no localizado en términos fetcheados.",
        ),
        precio_examen_50k=209.0,
        precio_examen_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="$209 precio regular 50K Rapid",
        ),
        coste_activacion_50k=0.0,
        coste_activacion_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="$0 activación",
        ),
        payout_split_pct=90.0,
        payout_split_source=SourceRef(
            confidence="fetch",
            url="https://myfundedfutures.com/plans/rapid",
            captured_at="2026-09-01",
            note="90/10 split",
        ),
        vps_permitido=None,
        vps_permitido_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="No verificado por fetch directo de ToS.",
        ),
    ),

    # 4. TradeDay
    FirmaV2(
        id="tradeday",
        nombre="TradeDay",
        trailing_dd_tipo="EOD",
        trailing_dd_tipo_source=SourceRef(
            confidence="fetch",
            url="https://www.tradeday.com/terms-and-conditions",
            captured_at="2026-09-01",
            note="EOD Trailing Drawdown limits (Fast Pass conserva EOD en fondeada; Quick Pay fondeada pasa a Intraday).",
        ),
        trailing_dd_valor_50k=None,
        trailing_dd_valor_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Tabla de importes de drawdown por tamaño no verificable por fetch directo.",
        ),
        perdida_diaria_limite_50k=None,
        perdida_diaria_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="No existe DLL en TradeDay 2.0.",
        ),
        consistencia_pct=45.0,
        consistencia_source=SourceRef(
            confidence="fetch",
            url="https://tradeday.freshdesk.com/en/support/solutions/articles/103000008847",
            captured_at="2026-09-01",
            note="Fast Pass: No day greater than 45% (Quick Pay: 30%).",
        ),
        min_dias_trading=3,
        min_dias_source=SourceRef(
            confidence="fetch",
            url="https://tradeday.freshdesk.com/en/support/solutions/articles/103000008847",
            captured_at="2026-09-01",
            note="Fast Pass: 3 días mínimos (Quick Pay: 5 días).",
        ),
        max_micros_50k=None,
        max_micros_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Tabla de contratos no verificable por fetch directo.",
        ),
        hora_cierre_obligatoria="10 min antes del cierre de sesión",
        hora_cierre_source=SourceRef(
            confidence="fetch",
            url="https://www.tradeday.com/terms-and-conditions",
            captured_at="2026-09-01",
            note="Day-trading only and all positions must be closed at least 10 minutes prior to the end of any session.",
        ),
        precio_examen_50k=None,
        precio_examen_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Precio regular no verificable por alta dispersión promocional.",
        ),
        coste_activacion_50k=None,
        coste_activacion_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Activación $0 en TradeDay 2.0 pero sin URL primaria individual fetcheada.",
        ),
        payout_split_pct=None,
        payout_split_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Split 80%-95% sin URL primaria individual fetcheada.",
        ),
        vps_permitido=False,
        vps_permitido_source=SourceRef(
            confidence="fetch",
            url="https://tradeday.freshdesk.com/en/support/solutions/articles/103000295384",
            captured_at="2026-09-01",
            note="TradeDay does not allow the use of virtual private servers (VPS)",
        ),
    ),

    # 5. Take Profit Trader
    FirmaV2(
        id="take_profit_trader",
        nombre="Take Profit Trader",
        trailing_dd_tipo=None,
        trailing_dd_tipo_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Mecanismo EOD en Test / Intraday en PRO citado en reseñas pero dominio oficial bloqueado con 403.",
        ),
        trailing_dd_valor_50k=None,
        trailing_dd_valor_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Importe de drawdown no verificable por fuente primaria directa.",
        ),
        perdida_diaria_limite_50k=None,
        perdida_diaria_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="DLL no verificable con fuente oficial directa.",
        ),
        consistencia_pct=50.0,
        consistencia_source=SourceRef(
            confidence="fetch",
            url="https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013-Rule-5-Be-Consistent",
            captured_at="2026-09-01",
            note="no single trading day may exceed 50% of your total net profits",
        ),
        min_dias_trading=3,
        min_dias_source=SourceRef(
            confidence="ws_official",
            url="https://takeprofittrader.com/blog/3-day-evals",
            captured_at="2026-09-01",
            note="3 días mínimos de trading desde cambio 2026.",
        ),
        max_micros_50k=None,
        max_micros_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="No verificable por fuente oficial directa.",
        ),
        hora_cierre_obligatoria=None,
        hora_cierre_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Flat time no verificado.",
        ),
        precio_examen_50k=170.0,
        precio_examen_source=SourceRef(
            confidence="ws_official",
            url="https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172548967069",
            captured_at="2026-09-01",
            note="$170/mes precio base 50K según snippet oficial.",
        ),
        coste_activacion_50k=None,
        coste_activacion_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Activación no verificable.",
        ),
        payout_split_pct=90.0,
        payout_split_source=SourceRef(
            confidence="ws_official",
            url="https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172548967069",
            captured_at="2026-09-01",
            note="90% split en cuenta PRO.",
        ),
        vps_permitido=None,
        vps_permitido_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Bots totalmente autónomos prohibidos; política VPS no verificada.",
        ),
    ),

    # 6. Tradeify
    FirmaV2(
        id="tradeify",
        nombre="Tradeify",
        trailing_dd_tipo=None,
        trailing_dd_tipo_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Dominio help.tradeify.co bloqueado con 403; no verificable por fuente primaria directa.",
        ),
        trailing_dd_valor_50k=None,
        trailing_dd_valor_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Drawdown 50K no verificable por fuente primaria directa.",
        ),
        perdida_diaria_limite_50k=None,
        perdida_diaria_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="DLL presente en Growth pero no en Select Flex; no verificable por fuente primaria directa.",
        ),
        consistencia_pct=None,
        consistencia_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Consistencia 40% no verificable por fuente primaria directa.",
        ),
        min_dias_trading=None,
        min_dias_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Mínimo de días no verificable.",
        ),
        max_micros_50k=None,
        max_micros_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Contratos no verificables por fuente primaria.",
        ),
        hora_cierre_obligatoria=None,
        hora_cierre_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Flat time no verificable.",
        ),
        precio_examen_50k=None,
        precio_examen_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Precio 50K Growth $139 no verificable por fuente primaria directa.",
        ),
        coste_activacion_50k=None,
        coste_activacion_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Activación no verificable por fuente primaria directa.",
        ),
        payout_split_pct=None,
        payout_split_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="Split 90/10 no verificable por fuente primaria directa.",
        ),
        vps_permitido=None,
        vps_permitido_source=SourceRef(
            confidence="unverified",
            url=None,
            captured_at="2026-09-01",
            note="VPN/VPS prohibido en login; resto en zona gris.",
        ),
    ),
)


def get_firm_v2(firm_id: str) -> Optional[FirmaV2]:
    """Obtiene una firma del catálogo v2 por su identificador único."""
    for f in CATALOGO_V2:
        if f.id == firm_id:
            return f
    return None


def verificar_catalogo() -> List[str]:
    """Valida el cumplimiento estricto de la directiva D6 en CATALOGO_V2.

    Reglas D6:
    1. Nunca url == "" (cadena vacía). url debe ser None o str no vacía.
    2. Si valor is not None => confidence in {"fetch", "ws_official"} y url no vacía.
    3. Si valor is None => confidence == "unverified" y url is None.
    4. confidence debe ser una de {"fetch", "ws_official", "unverified"}.
    """
    errores: List[str] = []
    for firma in CATALOGO_V2:
        for campo, val, src in firma.campos_con_fuente():
            prefix = f"[{firma.id}.{campo}]"

            # 1. confidence válido
            if src.confidence not in ("fetch", "ws_official", "unverified"):
                errores.append(f"{prefix} confidence '{src.confidence}' inválido")

            # 2. Nunca url vacía
            if src.url == "":
                errores.append(f"{prefix} url no puede ser cadena vacía (debe ser None o URL válida)")

            # 3. Regla D6: valor presente exige fuente verificada
            if val is not None:
                if src.confidence not in ("fetch", "ws_official"):
                    errores.append(f"{prefix} tiene valor {val!r} pero confidence es '{src.confidence}' (debe ser 'fetch' o 'ws_official')")
                if not src.url:
                    errores.append(f"{prefix} tiene valor {val!r} pero url está vacía o es None")
            else:
                # 4. Si el valor es None, debe ser unverified y url None
                if src.confidence != "unverified":
                    errores.append(f"{prefix} valor es None pero confidence es '{src.confidence}' (debe ser 'unverified')")
                if src.url is not None:
                    errores.append(f"{prefix} valor es None pero url es '{src.url}' (debe ser None)")

    return errores
