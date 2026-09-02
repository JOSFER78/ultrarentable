"""services/engine_version.py
SSOT Canónico de Versión del Motor Cuantitativo, Huella Digital y Gobernanza.
Especificación oficial según Sección 7, 8, 12 y 13 del Informe Maestro v5.3.0 / v5.4.0.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# 5.5.0 (2026-08-31): cambio de SEMANTICA de senal de entrada en event_backtest_engine.
#   CROSS_ABOVE/CROSS_BELOW se evaluaban como comparacion de estado (ema_fast > ema_slow),
#   cierta en ~la mitad de las velas => la estrategia estaba casi siempre en mercado.
#   Ahora se evaluan como EVENTO de cruce (prev <= y actual >), como define el contrato.
# 5.6.0 (2026-08-31): multiplicador de contrato dependiente del venue: FONDEO usa
#   point_value CME real (ES 50, NQ 20, GC 100...), ULTRA usa 1.0 (perpetuo BingX).
# 5.7.0 (2026-08-31): friccion de ejecucion coherente. Spread medido por barra (spread_mean
#   Dukascopy, OHLC en bid) con fills asimetricos ask/bid cuando >=90% de barras lo traen;
#   comision de futuros fija POR LADO (antes: porcentual en entrada + fija ida-y-vuelta en
#   salida); slippage de entrada ya no se cobra dos veces; point_value en el slippage de
#   entrada y en el cierre END_OF_DATASET (que ademas no aplicaba point_value al PnL).
# 5.8.0 (2026-08-31): FONDEO dimensiona en contratos CME ENTEROS (floor); si el riesgo
#   configurado no alcanza 1 contrato, la operacion no se toma. ULTRA (point_value=1) no cambia.
# 5.9.0 (2026-08-31): LATENCIA de entrada. La senal decidida al cierre de la vela N se
#   ejecuta en la APERTURA de la vela N+1 (antes: fill en el mismo close de la senal,
#   imposible en real). Senales en la ultima vela o con fill fuera de sesion se descartan.
# 5.10.0 (2026-08-31): unidad canonica de riesgo = FRACCION (0.02 == 2%). El motor ya no
#   divide entre 100; guardia fail-closed para riesgo > 0.5. Corrige sizing ~100x
#   infradimensionado en TODO el historico.
# 5.11.0 (2026-08-31): sizing y margen conscientes del point_value en futuros: riesgo por
#   contrato = sl_dist * point_value, nocional = precio * point_value * qty. Hasta 5.10.0
#   un MES con SL de 30 pts se dimensionaba 5x por encima del riesgo configurado.
# 5.12.0 (2026-08-31): spread real MEDIDO POR PAR (registro BingX) para ULTRA cuando no hay
#   spread medido por barra (Dukascopy). El modelo ASUMIDO de 2 bps esta calibrado sobre
#   BTC/ETH; pares como AVAX/SUI/DOGE tienen spreads reales 4-7x mayores y quedaban
#   sistematicamente subestimados. friction_model="MEASURED_PAIR" en este modo intermedio.
# 5.13.0 (2026-08-31): acumulacion real de FUNDING en perpetuos ULTRA. Hasta 5.12.0 el
#   funding nunca se cobraba en el loop (total_funding_paid_usd quedaba hardcodeado a 0.0).
#   Ahora, por cada frontera de 8h (00:00/08:00/16:00 UTC) cruzada mientras hay posicion
#   abierta en un par del registro BingX, se cobra/abona funding_mean*notional; long paga
#   al short si el rate es positivo. Nuevo campo EventBacktestResult.total_funding_usd.
# 5.14.0 (2026-08-31, F03.3): 4 familias de arquetipos EVENTO nuevas (reversion_atr,
#   squeeze_breakout, session_momentum, streak_edge), despachadas por `strategy.archetype` +
#   `archetype_params` (StrategySnapshot, campo aditivo con retrocompatibilidad de hash: sin
#   archetype_params el canonical_hash es bit a bit identico al de 5.13.0). Aditivo estricto:
#   las familias EMA/RSI/Donchian existentes no cambian ni una linea de semantica; un
#   snapshot anterior a 5.14.0 produce EXACTAMENTE las mismas operaciones que en 5.13.0. No
#   invalida certificaciones 5.13.0 (no las hay: 0 certificadas).
# 5.15.0 (2026-08-31, F02.3): reglas de prop firm OPT-IN dentro del motor (PropFirmProfile),
#   evaluadas sobre EQUITY FLOTANTE barra a barra (no PnL realizado): trailing/EOD/static
#   drawdown, limite de perdida diaria, y cierre obligatorio por hora de sesion. Aditivo
#   estricto: run_backtest(..., prop_profile=None) -- su valor por defecto -- no ejecuta ni una
#   linea de este codigo; las 15 celdas de referencia de scripts/verificacion_f02.py salen
#   identicas a 5.14.0. Sin prop_profile, ningun snapshot cambia de comportamiento.
# 5.16.0 (2026-09-01): FIX CATASTROFICO de comision en FONDEO/forex. `es_futuro` se
#   derivaba de `point_value != 1.0`, un umbral numerico que forex tambien cumple
#   (point_value=10.0, convencion "USD por pip por lote"). Heredaba asi las DOS reglas de
#   contratos CME liquidados en bolsa sin serlo: comision FIJA por unidad de qty (self.cme_fee
#   ~2.50 USD) en vez de porcentual, y cantidad forzada a entero. Con qty~4.700 (unidades en
#   la escala point_value=10 necesarias para representar ~50.000 USD de nocional a 1x), la
#   comision facturaba ~11.700 USD POR LADO: 2-3 operaciones bastaban para quebrar una cuenta
#   de 50.000 USD con PnL bruto de apenas +-100 USD por operacion. Medido en EURUSD 1h IS:
#   3 operaciones, PF 0.00, cuenta a -10.572 USD. Fix: `es_futuro` se deriva del
#   `asset_class` REAL de InstrumentRegistry (CME_FUTURES), no de un umbral sobre
#   point_value. Verificado en las 6 divisas del universo FONDEO x 4 arquetipos EVENTO
#   (5.14.0): 100-330 operaciones, PF 0.36-0.96, perdidas de 500-9.000 USD sobre 50.000 --
#   mismo orden de magnitud que ES/MES (referencia sana). No toca la ruta ULTRA (nunca
#   alcanza este bloque: `if not _es_fondeo: ... raise StopIteration`) ni los futuros CME
#   (asset_class ya era CME_FUTURES, es_futuro sigue siendo True exactamente igual que antes).
#   15/15 celdas de scripts/verificacion_f02.py identicas a 5.15.0 (ninguna es forex).
# 5.17.0 (2026-09-01, F03.3 cont., CUELLO 6): 2 familias de arquetipos EVENTO nuevas para
#   FUTUROS INTRADIA DE INDICE en 5m/15m -- opening_range_breakout (ruptura del rango de los
#   primeros `or_minutes` minutos tras la apertura de sesion RTH) y vwap_reversion (reversion
#   al VWAP anclado a sesion, se reinicia cada dia). Causa: ningun arquetipo existente opera
#   lo suficiente en futuros intradia para alcanzar las >=200 operaciones OOS del criterio 1.1
#   sellado (session_momentum: 24-27 operaciones OOS best-case). Ambas familias se despachan
#   por `strategy.archetype` + `archetype_params`, mismo patron aditivo que 5.14.0 (helpers
#   nuevos _calc_opening_range_levels/_calc_session_vwap en EventBacktestEngine; cero lineas
#   tocadas de las familias EMA/RSI/Donchian/REVERSION_ATR/SQUEEZE_BREAKOUT/SESSION_MOMENTUM/
#   STREAK_EDGE existentes). DoF real contado en services/discovery/effective_dof.py
#   (OPENING_RANGE_BREAKOUT=4, VWAP_REVERSION=3, risk_pct incluido) y vecindario perturbable
#   NO-NOOP verificado en gate_09_novelty_antifit.py (_ARCHETYPE_NEIGHBORHOOD_SPEC, paso
#   minimo forzado en enteros como el resto de familias 5.14.0). Diseno completo con
#   justificacion de ventaja esperada (no solo volumen) en
#   orchestration/reviews/diseno_arquetipos_5_17_0.md. Aditivo estricto: 15/15 celdas de
#   scripts/verificacion_f02.py identicas a 5.16.0 (el perfil `champions` que usa esa
#   verificacion no incluye estas 2 familias nuevas).
# 5.18.0 (W2.9): Sesiones conscientes de DST por vela con zoneinfo y ventanas por familia.
#   Apertura RTH (09:30 ET) en America/New_York cae a las 13:30 UTC en verano y a las 14:30 UTC
#   en invierno, corrigiendo el 33.4% de dias en horario estandar. Ventanas diferenciadas:
#   RTH (09:30-16:00 ET) para ancladas a sesion; Globex (18:00-17:00 ET) con flat 15:10 CT
#   (America/Chicago) para familias continuas de fondeo (Topstep).
# Las certificaciones anteriores NO son comparables: se marcan LEGACY_MOTOR_* (regla #26).
CURRENT_ENGINE_VERSION: str = "5.18.0"
CURRENT_ENGINE_NAME: str = "Ultrarentable V5.18.0 (Sesiones conscientes de DST por vela + ventanas por familia y flat obligatorio 15:10 CT)"
CURRENT_PIPELINE_VERSION: str = "5.4.0"
CURRENT_VALIDATION_PIPELINE_VERSION: str = "5.4.0"
VALIDATION_PIPELINE_VERSION: str = "5.4.0"
PIPELINE_VALIDATION_VERSION: str = "5.4.0"
CURRENT_POLICY_VERSION: str = "5.4.0"
CURRENT_GATE_POLICY_VERSION: str = "5.4.0"
MIN_SUPPORTED_ENGINE_VERSION: str = "1.0.0"
MINIMUM_SUPPORTED_VERSION: str = "1.0.0"
ENGINE_RELEASE_DATE: str = "2026-09-02"
CANONICAL_AUTHOR: str = "Ultrarentable Core Quantitative Team"

VERSION_HISTORY: List[Dict[str, Any]] = [
    {
        "version": "5.18.0",
        "name": CURRENT_ENGINE_NAME,
        "date": "2026-09-02",
        "status": "CURRENT_RECOMMENDED",
        "changes": [
            "W2.9 (regla #26, D10): sesiones conscientes de DST por vela con zoneinfo (America/New_York para indices CME; apertura RTH 09:30 ET cae a las 13:30 UTC en verano y 14:30 UTC en invierno, corrigiendo el 33.4% de dias en horario estandar con sesion fija).",
            "Ventana de sesion por familia: RTH 09:30-16:00 ET para ancladas a sesion (SESSION_MOMENTUM, OPENING_RANGE_BREAKOUT, VWAP_REVERSION); ventana Globex 18:00-17:00 ET con flat obligatorio a las 15:10 America/Chicago (Topstep / firmas verificadas) para REVERSION_ATR, SQUEEZE_BREAKOUT, STREAK_EDGE y resto de familias FONDEO CME.",
            "Campos aditivos opcionales en SessionWindow (market_tz, start_time_local, end_time_local, flat_time_local, flat_tz) con defaults None; hash canonico de snapshots sin campos nuevos 100% bit a bit identico a 5.17.0.",
            "Conversion por vela en EventBacktestEngine (_is_in_session_window, _session_start_minutes, _is_session_end, _calc_session_vwap, _calc_opening_range_levels) sin tablas fijas de DST, fail-closed ante market_tz invalido.",
            "9 celdas ULTRA de verificacion_f02 identicas bit a bit (ledger SHA-256 intacto); 6 celdas FONDEO actualizadas reflejando el horario local real y el flat obligatorio.",
        ],
    },
    {
        "version": "5.17.0",
        "name": "Ultrarentable V5.17.0 (Opening Range Breakout + VWAP Reversion: arquetipos intradia de futuros de indice)",
        "date": "2026-09-01",
        "status": "STALE",
        "changes": [
            "CUELLO 6 (plan FONDEO): 2 familias de arquetipos EVENTO nuevas para futuros intradia de indice en 5m/15m -- opening_range_breakout (ruptura del rango de los primeros `or_minutes` {15,30,60} minutos tras la apertura de sesion RTH, session_window.start_time_utc) y vwap_reversion (reversion al VWAP anclado a sesion, se reinicia cada dia; TP dinamico = VWAP vivo, igual patron que reversion_atr).",
            "Causa: ningun arquetipo existente opera lo suficiente en futuros intradia para las >=200 operaciones OOS del criterio 1.1 sellado (session_momentum: 24-27 operaciones OOS best-case en la campana 1h). Estimado por conteo de eventos (sin backtest) sobre ES 5m/15m Dukascopy: ORB ~1.5 eventos/dia-sesion, VWAP_REVERSION ~1.5-3.3 eventos/dia-sesion -- ambos proyectan varios cientos de operaciones sobre el tramo OOS completo.",
            "Nuevos helpers causales en EventBacktestEngine: _calc_opening_range_levels (rango sellado por dia, sin lookahead) y _calc_session_vwap (VWAP que se reinicia en la primera barra en sesion de cada dia UTC, distinto del VWAP acumulativo global de indicator_engine.py). Despacho por `strategy.archetype` + `archetype_params`, mismo patron aditivo estricto que 5.14.0 -- cero lineas tocadas de las familias EMA/RSI/Donchian/REVERSION_ATR/SQUEEZE_BREAKOUT/SESSION_MOMENTUM/STREAK_EDGE existentes.",
            "DoF real: OPENING_RANGE_BREAKOUT=4 (or_minutes + sl_atr_mult + tp_atr_mult + risk_pct), VWAP_REVERSION=3 (vwap_dev_atr_mult + sl_atr_mult + risk_pct; tp_atr_mult inerte, TP dinamico) en services/discovery/effective_dof.py.",
            "Vecindario de perturbacion (gate 9) NO-NOOP verificado por enumeracion exhaustiva de grid x delta: paso minimo forzado en enteros (or_minutes), igual criterio que el resto de familias 5.14.0.",
            "Solo FONDEO (futuros CME reales, requieren session_window de una sesion regulada): _arquetipos_5_17_0_configs(is_ultra=True) devuelve [] a proposito, ULTRA queda fuera de alcance.",
            "Diseno completo con justificacion de ventaja esperada (no solo volumen) en orchestration/reviews/diseno_arquetipos_5_17_0.md.",
            "Aditivo estricto: 15/15 celdas de scripts/verificacion_f02.py identicas a 5.16.0 (el perfil `champions` que usa esa verificacion no incluye estas 2 familias nuevas, ni ninguna de las 4 de 5.14.0).",
        ],
    },
    {
        "version": "5.16.0",
        "name": "Ultrarentable V5.16.0 (Fix: comision FONDEO/forex clasificada por asset_class, no por point_value)",
        "date": "2026-09-01",
        "status": "STALE",
        "changes": [
            "FIX CATASTROFICO: es_futuro (decide comision fija POR CONTRATO vs porcentual, y cantidad entera vs fraccionaria) se derivaba de `point_value != 1.0`. Forex (point_value=10.0, convencion USD/pip/lote) cumplia ese umbral sin ser un contrato CME, heredando comision fija de ~2.50 USD POR UNIDAD DE QTY -- con qty~4.700 eso factura ~11.700 USD por lado, suficiente para quebrar una cuenta de 50.000 USD en 2-3 operaciones (medido: EURUSD 1h IS, PF 0.00, cuenta a -10.572 USD).",
            "Fix: es_futuro = spec.asset_class == AssetClass.CME_FUTURES (dato real de InstrumentRegistry), no un umbral numerico sobre point_value.",
            "Verificado en las 6 divisas FONDEO x 4 arquetipos 5.14.0: 100-330 operaciones, PF 0.36-0.96, perdidas de 500-9.000 USD sobre 50.000 (antes: 3 operaciones, PF 0.00, cuenta quebrada). Mismo orden de magnitud que ES/MES.",
            "No afecta a ULTRA (nunca alcanza este bloque) ni a futuros CME (asset_class ya era CME_FUTURES, es_futuro identico a 5.15.0). 15/15 celdas de scripts/verificacion_f02.py identicas a 5.15.0 (ninguna celda de referencia es forex).",
        ],
    },
    {
        "version": "5.15.0",
        "name": "Ultrarentable V5.15.0 (Prop Firm Rules: Floating-Equity Trailing DD, Daily Loss, Session Cutoff)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "F02.3: reglas de prop firm OPT-IN dentro de EventBacktestEngine.run_backtest (nuevo parametro prop_profile: Optional[PropFirmProfile], default None).",
            "Trailing/EOD/static drawdown y limite de perdida diaria evaluados sobre EQUITY FLOTANTE (mark-to-market intra-barra via bar_high/bar_low), no sobre PnL realizado -- una operacion que cierra en positivo puede violar el trailing DD a mitad de camino; el motor la detecta y cierra en el precio EXACTO de ruptura.",
            "Cierre obligatorio de posiciones por hora de corte de sesion (PropFirmProfile.session_cutoff_utc), independiente del session_window propio de la estrategia.",
            "TradeRecord.prop_rule_violated y EventBacktestResult.prop_firm_busted/prop_firm_violations (todos aditivos, default None/False/[]) para que el evaluador de examenes (scripts/fondeo_examen.py) consuma la violacion sin adivinar a partir de exit_reason.",
            "consistency_pct del catalogo PROP_FIRM_CATALOG queda FUERA del motor a proposito: es una propiedad agregada de todo el ledger, se calcula mejor a posteriori.",
            "Aditivo estricto: con prop_profile=None (default) cero lineas de este codigo se ejecutan; 15/15 celdas de scripts/verificacion_f02.py identicas a 5.14.0.",
        ],
    },
    {
        "version": "5.14.0",
        "name": "Ultrarentable V5.14.0 (Event Archetype Expansion: Reversion/Squeeze/Session/Streak)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Aditivo: 4 familias de arquetipos nuevas (reversion_atr, squeeze_breakout, session_momentum, streak_edge); no altera operaciones de snapshots pre-5.14.0.",
            "StrategySnapshot.archetype_params (aditivo, retrocompatible en hash) y despacho explicito por strategy.archetype en EventBacktestEngine, separado del interprete generico de entry_rules.",
            "Perfil de busqueda 'arquetipos' en mine.py (build_candidate_search_configs) para minar solo las familias nuevas; anadidas tambien al perfil 'amplio'.",
        ],
    },
    {
        "version": "5.13.0",
        "name": "Ultrarentable V5.13.0 (Real Funding Accrual for Perpetuals)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Acumulacion real de funding en perpetuos ULTRA: se cobra/abona funding_mean*notional por cada frontera de 8h cruzada con posicion abierta.",
            "Nuevo campo EventBacktestResult.total_funding_usd; to_canonical_ledger ya no hardcodea total_funding_paid_usd=0.0.",
        ],
    },
    {
        "version": "5.12.0",
        "name": "Ultrarentable V5.12.0 (Per-Pair Measured Crypto Spread)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Spread real MEDIDO POR PAR (registro BingX) para ULTRA cuando no hay spread medido por barra.",
            "friction_model='MEASURED_PAIR' como capa intermedia entre MEASURED (por barra) y ASSUMED (2 bps generico).",
        ],
    },
    {
        "version": "5.11.0",
        "name": "Ultrarentable V5.11.0 (Point-Value-Aware Futures Sizing & Margin)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Sizing y margen conscientes del point_value en futuros: riesgo por contrato = sl_dist * point_value.",
            "Nocional/margen usa precio * point_value * qty; ULTRA (point_value=1) no cambia.",
        ],
    },
    {
        "version": "5.10.0",
        "name": "Ultrarentable V5.10.0 (Canonical Risk Unit: Fraction)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Unidad canonica de riesgo = FRACCION (0.02 == 2%); el motor ya no divide entre 100.",
            "Guardia fail-closed: riesgo por operacion > 0.5 (50%) lanza ValueError (unidad porcentaje heredada).",
        ],
    },
    {
        "version": "5.9.0",
        "name": "Ultrarentable V5.9.0 (Entry Latency: Next-Bar-Open Fills)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Latencia de entrada: la senal decidida al cierre de la vela N se ejecuta en la apertura de la vela N+1.",
            "Senales en la ultima vela del dataset o con fill fuera de sesion se descartan.",
        ],
    },
    {
        "version": "5.8.0",
        "name": "Ultrarentable V5.8.0 (Integer CME Contracts — Decision #25)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "FONDEO dimensiona en contratos CME enteros (floor); sin 1 contrato no se opera.",
        ],
    },
    {
        "version": "5.7.0",
        "name": "Ultrarentable V5.7.0 (Measured Friction: Bid/Ask Spread Execution & Per-Side Venue Fees)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Ejecucion asimetrica bid/ask con spread medido por barra (friction_model=MEASURED) cuando el dataset lo trae.",
            "Comision de futuros fija por lado; eliminado el doble cobro de slippage de entrada; point_value en slippage de entrada y cierre END_OF_DATASET.",
        ],
    },
    {
        "version": "5.6.0",
        "name": "Ultrarentable V5.6.0 (Dual-Track Engine: Event-Cross Semantics & Venue-Aware Point Value)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "Multiplicador de contrato dependiente del venue: FONDEO usa point_value CME real, ULTRA usa 1.0 (perpetuo BingX).",
            "Invalida todo backtest de futuros anterior: candidatas afectadas a LEGACY_MOTOR_SIN_POINT_VALUE.",
        ],
    },
    {
        "version": "5.5.0",
        "name": "Ultrarentable V5.5.0 (Event-Cross Signal Semantics)",
        "date": "2026-08-31",
        "status": "STALE",
        "changes": [
            "CROSS_ABOVE/CROSS_BELOW pasan de comparacion de estado a EVENTO de cruce (prev <= y actual >).",
            "Invalida certificaciones previas de senal: candidatas afectadas a LEGACY_MOTOR_SENAL_SIN_CRUCE.",
        ],
    },
    {
        "version": "5.4.0",
        "name": "Ultrarentable V5.4.0 (Dual-Track Multi-Asset 24/7 Engine: CME Micro Sizing & Asymmetric Ratchet Vault)",
        "date": "2026-08-25",
        "status": "STALE",
        "changes": [
            "Reality Lock P0 Remediation: Purga total de mocks y curvas sintéticas.",
            "Integración Fail-Closed en Gate 07 Regime Coverage.",
            "Sincronización atómica de endpoints v2 con SQLite WAL y Durable Job Queue.",
            "Linaje criptográfico inmutable con trial_id y EvidenceBundle firmado.",
        ],
    },
    {
        "version": "5.3.0",
        "name": "Ultrarentable V5.3.0 (Forensic Baseline & Reality Lock)",
        "date": "2026-08-24",
        "status": "STALE",
        "changes": ["Auditoría forense de 11 gates y segregación IS/OOS."],
    },
    {
        "version": "1.05",
        "name": "Ultrarentable V1.05 (Dimensional Purity & Geometric Compounding)",
        "date": "2026-08-18",
        "status": "LEGACY",
        "changes": ["Operación dimensional en % y múltiplos R."],
    },
    {
        "version": "1.03",
        "name": "Ultrarentable V1.03 (Incremental Versioning & Manifest)",
        "date": "2026-08-15",
        "status": "LEGACY",
        "changes": ["Version control manager y hash Merkle."],
    },
    {
        "version": "1.02",
        "name": "Ultrarentable V1.02 (Legacy SQX Integration)",
        "date": "2026-08-10",
        "status": "LEGACY",
        "changes": ["Generación base de candidatos SQX."],
    },
]

SUPPORTED_LEGACY_VERSIONS: List[str] = [
    "1.00", "1.01", "1.02", "1.03", "1.05", "2.0.0", "3.0.0", "4.0.0", "5.0.0", "5.1.0", "5.2.0", "5.3.0", "5.4.0", "5.5.0", "5.6.0", "5.7.0", "5.8.0", "5.9.0", "5.10.0", "5.11.0", "5.12.0", "5.13.0", "5.14.0"
]

GOVERNANCE_STATUS_APPROVED: str = "APPROVED"
GOVERNANCE_STATUS_CERTIFIED_CURRENT: str = "CERTIFIED_CURRENT"
GOVERNANCE_STATUS_CERTIFIED_LEGACY: str = "CERTIFIED_LEGACY"
GOVERNANCE_STATUS_STALE: str = "STALE"
GOVERNANCE_STATUS_REVALIDATION_REQUIRED: str = "REVALIDATION_REQUIRED"
GOVERNANCE_STATUS_REJECTED: str = "REJECTED"


def compute_engine_hash(version: str = CURRENT_ENGINE_VERSION, salt: str = "") -> str:
    """Calcula el hash criptográfico SHA-256 canónico del motor y sus parámetros base."""
    payload = {
        "engine_version": version,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_PIPELINE_VERSION,
        "gate_policy_version": CURRENT_GATE_POLICY_VERSION,
        "release_date": ENGINE_RELEASE_DATE,
        "author": CANONICAL_AUTHOR,
        "salt": salt,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def compute_codebase_fingerprint(root_dir: Optional[Path] = None) -> str:
    """Calcula la huella digital SHA-256 reproducible del código fuente del motor."""
    if root_dir is None:
        root_dir = Path(__file__).resolve().parent.parent

    hasher = hashlib.sha256()
    target_dirs = [
        root_dir / "services",
        root_dir / "contracts",
    ]

    files_to_hash: List[Path] = []
    for d in target_dirs:
        if d.exists() and d.is_dir():
            for p in sorted(d.rglob("*.py")):
                if "__pycache__" not in p.parts and not p.name.startswith("."):
                    files_to_hash.append(p)

    if not files_to_hash:
        return compute_engine_hash(CURRENT_ENGINE_VERSION)

    for fpath in sorted(files_to_hash, key=lambda p: str(p.relative_to(root_dir))):
        try:
            rel_path = str(fpath.relative_to(root_dir)).replace("\\", "/")
            hasher.update(rel_path.encode("utf-8"))
            hasher.update(fpath.read_bytes())
        except Exception:
            continue

    return hasher.hexdigest()


def get_current_version_info() -> Dict[str, Any]:
    """Retorna información completa del motor y versión actual."""
    fp = compute_codebase_fingerprint()
    now_iso = datetime.now(timezone.utc).isoformat()
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "active_version": CURRENT_ENGINE_VERSION,
        "pipeline_version": CURRENT_PIPELINE_VERSION,
        "validation_pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "policy_version": CURRENT_POLICY_VERSION,
        "gate_policy_version": CURRENT_GATE_POLICY_VERSION,
        "codebase_fingerprint": fp,
        "release_date": ENGINE_RELEASE_DATE,
        "author": CANONICAL_AUTHOR,
        "history": VERSION_HISTORY,
        "synced_at": now_iso,
    }


def stamp_version_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Estampa los metadatos de versión y huella en un diccionario."""
    info = get_current_version_info()
    now_iso = datetime.now(timezone.utc).isoformat()
    data["engine_version"] = info["engine_version"]
    data["engine_name"] = info["engine_name"]
    data["codebase_fingerprint"] = info["codebase_fingerprint"]
    data["stamped_at_utc"] = now_iso
    data["version_stamped_at"] = now_iso
    data["engine_ruleset_hash"] = compute_engine_hash()
    return data


def is_version_stale(
    engine_version: str,
    policy_version: Optional[str] = None,
    current_engine: str = CURRENT_ENGINE_VERSION,
    current_policy: str = CURRENT_POLICY_VERSION,
) -> bool:
    """Determina si un registro de estrategia o certificación es STALE."""
    if engine_version != current_engine:
        return True
    if policy_version is not None and policy_version != current_policy:
        return True
    return False


def is_revalidation_mandatory(
    source_engine_version: str,
    target_engine_version: str = CURRENT_ENGINE_VERSION,
) -> bool:
    """Verifica si la transición entre versiones requiere revalidación obligatoria."""
    return source_engine_version != target_engine_version


def get_engine_manifest() -> Dict[str, Any]:
    """Retorna el manifiesto oficial del motor para telemetría y auditoría."""
    return {
        "engine_version": CURRENT_ENGINE_VERSION,
        "engine_name": CURRENT_ENGINE_NAME,
        "pipeline_version": CURRENT_PIPELINE_VERSION,
        "validation_pipeline_version": CURRENT_VALIDATION_PIPELINE_VERSION,
        "policy_version": CURRENT_POLICY_VERSION,
        "gate_policy_version": CURRENT_GATE_POLICY_VERSION,
        "min_supported_version": MIN_SUPPORTED_ENGINE_VERSION,
        "release_date": ENGINE_RELEASE_DATE,
        "author": CANONICAL_AUTHOR,
        "engine_hash": compute_engine_hash(),
    }
