#!/usr/bin/env python3
"""scripts/fondeo_examen.py — ¿Cuántos días tarda en pasar el examen, y con qué riesgo de romperlo?

Responde a la pregunta real del track FONDEO: no "cuánto gana", sino
**P(pasar en ≤N días) sujeto a P(violar una regla) < umbral**.

Método: Monte Carlo por remuestreo (bootstrap) de las operaciones REALES del backtest OOS.
Nunca se generan retornos sintéticos: se reordenan y remuestrean operaciones que ocurrieron.
Es la diferencia entre estimar la distribución de un edge real y fabricar uno.

Reglas simuladas (configurables, NO hardcodeadas como verdad universal — cada firma tiene las
suyas y hay que ponerlas):
  - objetivo de beneficio
  - pérdida diaria máxima
  - drawdown total máximo (trailing sobre el pico, que es como matan de verdad las cuentas)
  - días mínimos de operativa
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from services.portfolio.meta_strategy_engine import MetaStrategyEngine  # noqa: E402
from services.exploitation_engines.prop_firm_engine import (  # noqa: E402
    PropFirmRules, find_prop_firm,
)
from services.engine_version import CURRENT_ENGINE_VERSION  # noqa: E402

# Mes gregoriano medio REAL (365.2425/12), no un mes de 30 días arbitrario: se usa para
# derivar la ventana de "un mes" y de "6 meses" del objetivo sellado F07 a partir de días
# simulados (el simulador solo entiende días).
DIAS_POR_MES = 30.4368

_DRAWDOWN_TYPES_VALIDOS = ("TRAILING_INTRADAY", "EOD", "STATIC")


def _reglas_base_desde_firma(rules: PropFirmRules) -> Dict[str, Any]:
    """Deriva (capital, objetivo_pct, perdida_diaria_pct, dd_total_pct, drawdown_type,
    consistency_pct, firma) de un perfil REAL del catálogo
    (services/exploitation_engines/prop_firm_engine.py::PROP_FIRM_CATALOG). Fuente ÚNICA
    usada tanto por ReglasExamen.desde_firma / CicloFondeado.desde_firma como por el merge
    de overrides manuales de `main()` -- evita que las dos fases (examen y vida fondeada)
    deriven la misma firma con fórmulas distintas."""
    return {
        "capital": rules.account_size_usd,
        "objetivo_pct": rules.profit_target_usd / rules.account_size_usd * 100.0,
        "perdida_diaria_pct": (rules.daily_loss_limit_usd / rules.account_size_usd * 100.0
                               if rules.daily_loss_limit_usd is not None else None),
        "dd_total_pct": rules.max_total_drawdown_usd / rules.account_size_usd * 100.0,
        "drawdown_type": rules.drawdown_type,
        "consistency_pct": rules.consistency_pct,
        "firma": rules.firm_name,
    }


class ReglasExamen:
    """Reglas de una evaluación de prop firm. Por defecto, un perfil tipo 50k bastante común.

    IMPORTANTE: estos valores son un PUNTO DE PARTIDA razonable, no la verdad de ninguna firma
    concreta. Para operar de verdad, constrúyela con `ReglasExamen.desde_firma(rules)` a partir
    de un perfil REAL de `services.exploitation_engines.prop_firm_engine.PROP_FIRM_CATALOG`.
    """

    def __init__(self, capital: float = 50000.0, objetivo_pct: float = 8.0,
                 perdida_diaria_pct: Optional[float] = 2.0, dd_total_pct: float = 4.0,
                 dias_minimos: int = 1, drawdown_type: str = "TRAILING_INTRADAY",
                 consistency_pct: Optional[float] = None, firma: Optional[str] = None):
        self.capital = capital
        self.objetivo = capital * objetivo_pct / 100.0
        # None = la firma no impone límite diario explícito (p.ej. varias cuentas Apex):
        # se representa como "nunca se dispara" en vez de inventar un umbral.
        self.perdida_diaria = (capital * perdida_diaria_pct / 100.0
                               if perdida_diaria_pct is not None else float("inf"))
        self.dd_total = capital * dd_total_pct / 100.0
        self.dias_minimos = dias_minimos
        if drawdown_type not in _DRAWDOWN_TYPES_VALIDOS:
            raise ValueError(f"drawdown_type '{drawdown_type}' inválido; usa uno de "
                             f"{_DRAWDOWN_TYPES_VALIDOS}")
        # TRAILING_INTRADAY: el pico de referencia avanza con cada operación (incluso intradía).
        # EOD: el pico solo avanza al ABRIR cada día simulado (ancla fija durante el día).
        # STATIC: el ancla nunca se mueve, es el capital inicial del examen.
        self.drawdown_type = drawdown_type
        # % máximo del beneficio total que un solo día puede aportar (None = la firma no
        # exige consistencia). Ver la comprobación en simular_examen().
        self.consistency_pct = consistency_pct
        # Nombre real de la firma si estas reglas vienen del catálogo (solo para reporte).
        self.firma = firma

    @classmethod
    def desde_firma(cls, rules: PropFirmRules, dias_minimos: int = 1) -> "ReglasExamen":
        """Construye las reglas de examen desde un perfil REAL del catálogo
        (services/exploitation_engines/prop_firm_engine.py::PROP_FIRM_CATALOG) en vez de los
        valores genéricos por CLI."""
        base = _reglas_base_desde_firma(rules)
        return cls(capital=base["capital"], objetivo_pct=base["objetivo_pct"],
                   perdida_diaria_pct=base["perdida_diaria_pct"],
                   dd_total_pct=base["dd_total_pct"], dias_minimos=dias_minimos,
                   drawdown_type=base["drawdown_type"],
                   consistency_pct=base["consistency_pct"], firma=base["firma"])


def simular_examen(trades: np.ndarray, ops_por_dia: float, reglas: ReglasExamen,
                   max_dias: int, rng: np.random.Generator) -> Dict[str, Any]:
    """Un examen completo. Devuelve si pasó, en cuántos días, y si violó alguna regla."""
    equity = reglas.capital
    pico = reglas.capital
    # Ledger real (remuestreado) del examen, un PnL neto por día ya cerrado. Base de la
    # regla de CONSISTENCIA: propiedad agregada de TODO el ledger, no evaluable barra a
    # barra (por eso vive aquí y no en el motor -- ver PropFirmProfile en
    # event_backtest_engine.py, docstring de F02.3).
    historial_dias: List[float] = []
    objetivo_bloqueado_por_consistencia = False
    dia = 0
    while dia < max_dias:
        dia += 1
        if reglas.drawdown_type == "EOD":
            # El pico de referencia solo avanza al ABRIR el día, anclado al equity con el
            # que cerró el día anterior: dentro del día el suelo queda fijo.
            pico = max(pico, equity)
        # Numero de operaciones del dia: Poisson alrededor del ritmo real observado
        n_ops = max(0, int(rng.poisson(ops_por_dia)))
        pnl_dia = 0.0
        for _ in range(n_ops):
            pnl = float(rng.choice(trades))          # remuestreo de una operacion REAL
            equity += pnl
            pnl_dia += pnl
            if reglas.drawdown_type == "TRAILING_INTRADAY":
                pico = max(pico, equity)
            referencia = reglas.capital if reglas.drawdown_type == "STATIC" else pico
            if referencia - equity >= reglas.dd_total:
                return {"paso": False, "dias": dia, "violacion": "DD_TOTAL",
                        "equity_final": equity}
        if -pnl_dia >= reglas.perdida_diaria:
            return {"paso": False, "dias": dia, "violacion": "PERDIDA_DIARIA",
                    "equity_final": equity}
        historial_dias.append(pnl_dia)
        if equity - reglas.capital >= reglas.objetivo and dia >= reglas.dias_minimos:
            beneficio_total = sum(historial_dias)
            mejor_dia = max(historial_dias)
            consistente = (
                reglas.consistency_pct is None or beneficio_total <= 0
                or mejor_dia / beneficio_total * 100.0 <= reglas.consistency_pct
            )
            if consistente:
                return {"paso": True, "dias": dia, "violacion": None, "equity_final": equity}
            # Objetivo alcanzado en USD pero un solo día concentra demasiado beneficio: la
            # firma no certifica el paso todavía (no revienta la cuenta, retiene la
            # certificación). Se sigue operando: más días diluyen la concentración.
            objetivo_bloqueado_por_consistencia = True
    violacion_final = ("CONSISTENCIA_NO_CUMPLIDA" if objetivo_bloqueado_por_consistencia
                       else "SIN_ALCANZAR_OBJETIVO")
    return {"paso": False, "dias": max_dias, "violacion": violacion_final,
            "equity_final": equity}


def evaluar(trades: np.ndarray, ops_por_dia: float, reglas: ReglasExamen,
            multiplicador: float, iteraciones: int, max_dias: int,
            semilla: int = 7) -> Dict[str, Any]:
    """Distribución completa del examen con las operaciones escaladas por `multiplicador`."""
    rng = np.random.default_rng(semilla)
    escaladas = trades * multiplicador
    resultados = [simular_examen(escaladas, ops_por_dia, reglas, max_dias, rng)
                  for _ in range(iteraciones)]

    pasados = [r for r in resultados if r["paso"]]
    dias = sorted(r["dias"] for r in pasados)
    violaciones: Dict[str, int] = {}
    for r in resultados:
        if r["violacion"]:
            violaciones[r["violacion"]] = violaciones.get(r["violacion"], 0) + 1

    # Bucketes que NO son "romper la cuenta" (no se pierde capital, no se viola un límite de
    # riesgo): no alcanzar el objetivo en la ventana, o alcanzarlo pero sin pasar la regla de
    # consistencia (la firma retiene la certificación, no revienta la cuenta).
    NO_ES_ROTURA = ("SIN_ALCANZAR_OBJETIVO", "CONSISTENCIA_NO_CUMPLIDA")
    p_pasar = len(pasados) / len(resultados)
    p_romper = sum(v for k, v in violaciones.items() if k not in NO_ES_ROTURA) / len(resultados)
    return {
        "multiplicador": multiplicador,
        "p_pasar": round(p_pasar, 4),
        "p_romper_cuenta": round(p_romper, 4),
        "dias_mediana": dias[len(dias) // 2] if dias else None,
        "dias_p90": dias[int(len(dias) * 0.9)] if dias else None,
        "violaciones": violaciones,
    }


class CicloFondeado:
    """El negocio completo: aprobar, sobrevivir y COBRAR.

    Mandato del usuario (2026-08-31): "cuando se aprueba se deben hacer retiros, sin retiros
    no hay negocio". Una cuenta fondeada que nunca paga vale exactamente lo que costo el examen.

    Por eso el ciclo tiene DOS regimenes de riesgo distintos, y esa es la clave del modelo:

      FASE 1 - EXAMEN: agresiva. Hay que alcanzar el objetivo en pocos dias. Romper la cuenta
      cuesta un cartucho (~58 USD) y se dispara otro, asi que el riesgo alto SALE A CUENTA:
      la esperanza es positiva por encima de p_be = C_total/R_avg = 2,91%.

      FASE 2 - FONDEADA: conservadora. Aqui romper ya no cuesta un cartucho, cuesta la cuenta
      entera y todos los payouts futuros. El objetivo deja de ser crecer y pasa a ser
      SOBREVIVIR HASTA EL SIGUIENTE RETIRO, y repetir.

    El valor de una cuenta fondeada no es su beneficio: es la suma de los payouts que llega a
    cobrar antes de romperse.
    """

    def __init__(self, capital: float, umbral_retiro_pct: float = 2.0,
                 dias_entre_retiros: int = 14, reparto_trader: float = 0.90,
                 dd_total_pct: float = 4.0, perdida_diaria_pct: Optional[float] = 2.0,
                 drawdown_type: str = "TRAILING_INTRADAY",
                 consistency_pct: Optional[float] = None, firma: Optional[str] = None):
        self.capital = capital
        self.umbral_retiro = capital * umbral_retiro_pct / 100.0
        self.dias_entre_retiros = dias_entre_retiros
        self.reparto_trader = reparto_trader
        self.dd_total = capital * dd_total_pct / 100.0
        self.perdida_diaria = (capital * perdida_diaria_pct / 100.0
                               if perdida_diaria_pct is not None else float("inf"))
        if drawdown_type not in _DRAWDOWN_TYPES_VALIDOS:
            raise ValueError(f"drawdown_type '{drawdown_type}' inválido; usa uno de "
                             f"{_DRAWDOWN_TYPES_VALIDOS}")
        self.drawdown_type = drawdown_type
        self.consistency_pct = consistency_pct
        self.firma = firma

    @classmethod
    def desde_firma(cls, rules: PropFirmRules, umbral_retiro_pct: float = 2.0,
                    dias_entre_retiros: int = 14, reparto_trader: float = 0.90) -> "CicloFondeado":
        """Construye el ciclo de vida fondeada desde un perfil REAL del catálogo. El umbral
        de retiro y la cadencia de pagos no están en PropFirmRules (son política de negocio
        del trader, no una regla de riesgo de la firma), así que se mantienen configurables
        por CLI/llamador en vez de inventarse a partir del catálogo."""
        base = _reglas_base_desde_firma(rules)
        return cls(capital=base["capital"], umbral_retiro_pct=umbral_retiro_pct,
                   dias_entre_retiros=dias_entre_retiros, reparto_trader=reparto_trader,
                   dd_total_pct=base["dd_total_pct"],
                   perdida_diaria_pct=base["perdida_diaria_pct"],
                   drawdown_type=base["drawdown_type"],
                   consistency_pct=base["consistency_pct"], firma=base["firma"])


def simular_vida_fondeada(trades: np.ndarray, ops_por_dia: float, ciclo: CicloFondeado,
                          max_dias: int, rng: np.random.Generator) -> Dict[str, Any]:
    """Vida completa de una cuenta ya fondeada: cuanto cobra antes de romperse."""
    equity = ciclo.capital
    pico = ciclo.capital
    cobrado = 0.0
    retiros = 0
    dia = 0
    dias_desde_retiro = 0
    # Ledger real (remuestreado) del ciclo de pago EN CURSO -- desde el último retiro, o
    # desde el inicio de la cuenta si aún no hubo ninguno. Base de la regla de CONSISTENCIA
    # sobre el beneficio que se va a retirar (se reinicia al cobrar, igual que `beneficio`).
    historial_dias: List[float] = []

    while dia < max_dias:
        dia += 1
        dias_desde_retiro += 1
        if ciclo.drawdown_type == "EOD":
            pico = max(pico, equity)
        pnl_dia = 0.0
        for _ in range(max(0, int(rng.poisson(ops_por_dia)))):
            pnl = float(rng.choice(trades))           # remuestreo de una operacion REAL
            equity += pnl
            pnl_dia += pnl
            if ciclo.drawdown_type == "TRAILING_INTRADAY":
                pico = max(pico, equity)
            referencia = ciclo.capital if ciclo.drawdown_type == "STATIC" else pico
            if referencia - equity >= ciclo.dd_total:
                return {"cobrado": cobrado, "retiros": retiros, "dias": dia, "rota": True,
                        "equity_final": equity}
        if -pnl_dia >= ciclo.perdida_diaria:
            return {"cobrado": cobrado, "retiros": retiros, "dias": dia, "rota": True,
                    "equity_final": equity}
        historial_dias.append(pnl_dia)

        # Retiro: solo si hay beneficio acumulado suficiente y toca por calendario.
        beneficio = equity - ciclo.capital
        if beneficio >= ciclo.umbral_retiro and dias_desde_retiro >= ciclo.dias_entre_retiros:
            # Consistencia sobre ESTE ciclo de pago: si un solo día concentra demasiado del
            # beneficio a retirar, la firma retiene el pago (no revienta la cuenta) hasta que
            # más días diluyan la concentración -- se sigue operando sin resetear el ledger.
            mejor_dia = max(historial_dias) if historial_dias else 0.0
            consistente = (
                ciclo.consistency_pct is None or beneficio <= 0
                or mejor_dia / beneficio * 100.0 <= ciclo.consistency_pct
            )
            if consistente:
                pago = beneficio * ciclo.reparto_trader
                cobrado += pago
                equity -= beneficio          # el beneficio sale de la cuenta
                pico = equity                 # el trailing se recalcula desde el nuevo saldo
                retiros += 1
                dias_desde_retiro = 0
                historial_dias = []

    return {"cobrado": cobrado, "retiros": retiros, "dias": dia, "rota": False,
            "equity_final": equity}


def evaluar_negocio(trades: np.ndarray, ops_por_dia: float, ciclo: CicloFondeado,
                    mult_fondeada: float, iteraciones: int, dias_horizonte: int,
                    semilla: int = 11) -> Dict[str, Any]:
    """Cuanto dinero devuelve de verdad una cuenta fondeada, en payouts cobrados."""
    rng = np.random.default_rng(semilla)
    escaladas = trades * mult_fondeada
    res = [simular_vida_fondeada(escaladas, ops_por_dia, ciclo, dias_horizonte, rng)
           for _ in range(iteraciones)]
    cobros = sorted(r["cobrado"] for r in res)
    return {
        "mult_fondeada": mult_fondeada,
        "cobrado_medio": round(sum(cobros) / len(cobros), 0),
        "cobrado_mediana": round(cobros[len(cobros) // 2], 0),
        "cobrado_p10": round(cobros[int(len(cobros) * 0.10)], 0),
        "retiros_medios": round(sum(r["retiros"] for r in res) / len(res), 2),
        "p_romper": round(sum(1 for r in res if r["rota"]) / len(res), 4),
        "p_sin_cobrar_nada": round(sum(1 for r in res if r["cobrado"] == 0) / len(res), 4),
    }


def evaluar_rendimiento_mensual(trades: np.ndarray, ops_por_dia: float, ciclo: CicloFondeado,
                                mult_fondeada: float, iteraciones: int,
                                semilla: int = 13) -> Dict[str, Any]:
    """Rendimiento MENSUAL de la cuenta YA FONDEADA (Fase 2, régimen conservador): equity
    generada en una ventana de un mes calendario real (DIAS_POR_MES), incluyendo lo ya
    retirado en ese mes (es beneficio real materializado fuera de la cuenta, no dejarlo
    fuera subestimaría el rendimiento), como % del capital nominal de la cuenta.

    OBJETIVO SELLADO F07 (Emilio, 2026-08-31): se reporta la MEDIANA de la distribución
    Monte Carlo, NUNCA la media -- la media la infla la cola derecha de los meses
    excepcionales y miente sobre lo sostenible que es la estrategia mes a mes.
    """
    rng = np.random.default_rng(semilla)
    dias_mes = max(1, round(DIAS_POR_MES))
    escaladas = trades * mult_fondeada
    resultados = [simular_vida_fondeada(escaladas, ops_por_dia, ciclo, dias_mes, rng)
                 for _ in range(iteraciones)]
    retornos_pct = sorted(
        (r["equity_final"] + r["cobrado"] - ciclo.capital) / ciclo.capital * 100.0
        for r in resultados
    )
    n = len(retornos_pct)
    return {
        "mult_fondeada": mult_fondeada,
        "retorno_mensual_p5_pct": round(retornos_pct[max(0, int(n * 0.05))], 2),
        "retorno_mensual_mediana_pct": round(retornos_pct[n // 2], 2),
        "retorno_mensual_p95_pct": round(retornos_pct[min(n - 1, int(n * 0.95))], 2),
        "p_romper_en_el_mes": round(sum(1 for r in resultados if r["rota"]) / n, 4),
    }


def _parse_fecha_utc(valor: Any) -> Optional[datetime]:
    """Parsea una fecha en cualquiera de los formatos reales vistos en `duration_info`
    (p.ej. "2024-01-01 00:00:00 UTC" o ISO-8601). Devuelve None si no se puede parsear:
    nunca se adivina una fecha."""
    if not valor:
        return None
    texto = str(valor).strip()
    if not texto or texto.upper() == "N/A":
        return None
    texto_iso = texto.replace(" UTC", "+00:00").replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(texto_iso)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(texto, fmt)
        except ValueError:
            continue
    return None


def _span_oos_dias(duration_info: Optional[Dict[str, Any]]) -> Optional[float]:
    """Deduce el número REAL de días que abarca el periodo OOS a partir de `duration_info`
    (embebido en el scorecard de certificación o en la columna homónima de la BD).

    Prioridad (de más a menos directo, según los distintos generadores del proyecto):
      1. oos_days                         (services/api/app/factory/ultra_risk_controlled_engine.py,
                                            intelligent_quant_miner.py)
      2. oos_months * 30.4368             (services/discovery/discovery_validation_pipeline.py)
      3. out_of_sample_period.duration_days (scripts/recalibrate_sqlite_candidates.py)
      4. split_date -> end_date (rango explícito del tramo OOS)

    Fail-closed: si ninguna fuente real está disponible o es parseable, devuelve None.
    NUNCA se asume una ventana fija (p.ej. 60 días) en su lugar.
    """
    if not isinstance(duration_info, dict):
        return None

    oos_days = duration_info.get("oos_days")
    if oos_days:
        try:
            v = float(oos_days)
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass

    oos_months = duration_info.get("oos_months")
    if oos_months:
        try:
            v = float(oos_months) * 30.4368
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass

    oos_period = duration_info.get("out_of_sample_period")
    if isinstance(oos_period, dict) and oos_period.get("duration_days"):
        try:
            v = float(oos_period["duration_days"])
            if v > 0:
                return v
        except (TypeError, ValueError):
            pass

    inicio = _parse_fecha_utc(duration_info.get("split_date") or duration_info.get("oos_start"))
    fin = _parse_fecha_utc(duration_info.get("end_date") or duration_info.get("oos_end"))
    if inicio and fin and fin > inicio:
        return (fin - inicio).total_seconds() / 86400.0

    return None


def _extraer_duration_info(candidate: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """`duration_info` puede venir embebido en el scorecard (fuente viva, preferida) o como
    columna propia de la fila `candidates` (normalizaciones legacy), y en ambos casos puede
    llegar ya como dict o como texto JSON. Se prueban ambas fuentes sin adivinar contenido."""
    raw_sc = candidate.get("scorecard_json")
    if raw_sc:
        try:
            scorecard = json.loads(raw_sc) if isinstance(raw_sc, str) else raw_sc
            di = scorecard.get("duration_info") if isinstance(scorecard, dict) else None
            if isinstance(di, dict):
                return di
        except (json.JSONDecodeError, TypeError, AttributeError):
            pass

    raw_di = candidate.get("duration_info")
    if isinstance(raw_di, dict):
        return raw_di
    if isinstance(raw_di, str) and raw_di.strip():
        try:
            di = json.loads(raw_di)
            if isinstance(di, dict):
                return di
        except json.JSONDecodeError:
            pass
    return None


def _extraer_scorecard(candidate: Dict[str, Any]) -> Dict[str, Any]:
    """`scorecard_json` crudo de la fila `candidates`, ya parseado. Dict vacío si falta o es
    ilegible -- nunca lanza, los llamadores tratan "vacío" como "sin dato"."""
    raw_sc = candidate.get("scorecard_json")
    if not raw_sc:
        return {}
    try:
        sc = json.loads(raw_sc) if isinstance(raw_sc, str) else raw_sc
        return sc if isinstance(sc, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}


def reejecutar_examen_barra_a_barra(candidate: Dict[str, Any],
                                    rules: PropFirmRules) -> Optional[Dict[str, Any]]:
    """El camino honesto (F02.3): re-ejecuta el backtest OOS REAL de la candidata con el motor
    ACTUAL y `prop_profile=rules.to_engine_profile(...)`, que evalúa trailing drawdown, pérdida
    diaria y cierre de sesión sobre equity FLOTANTE (marcada a mercado barra a barra) -- lo que
    el Monte Carlo por bootstrap de `evaluar()` NO puede ver porque solo conoce el PnL neto de
    cada operación YA CERRADA (ver docstring de PropFirmProfile en event_backtest_engine.py).

    Por eso el bootstrap de este script es, como mucho, una COTA INFERIOR (optimista) de
    P(romper cuenta): una operación puede cerrar en positivo habiendo reventado el trailing
    drawdown a mitad de camino, y el bootstrap nunca lo verá.

    `scripts/mine.py` HOY solo persiste el blueprint reconstruible ("parameters": cfg crudo +
    strategy_snapshot_hash + dataset_hash en scorecard_json) para candidatas certificadas
    11/11 (rama `if verdict.is_certified` de `run_mining_pipeline`); las legacy (motor <5.15.0,
    ej. `discovery_validation_pipeline.py`) solo traen "parameters_selected", un esquema
    distinto que este re-run NO interpreta a propósito -- reconstruir un blueprint de un motor
    viejo con las kwargs del motor actual calibraría mal en silencio.

    FAIL-CLOSED (REAL-ONLY): devuelve **None** -- nunca un resultado inventado u optimista --
    si falta cualquier pieza necesaria, si el dataset en disco no coincide por SHA-256 con el
    certificado (el fichero cambió desde la certificación), o si el snapshot reconstruido NO
    reproduce el `strategy_snapshot_hash` certificado (blueprint no fiel). El llamador debe
    tratar None como "NO VERIFICADO A NIVEL DE BARRA", no como "sin violaciones".
    """
    sc = _extraer_scorecard(candidate)
    params = sc.get("parameters")
    if not isinstance(params, dict) or not params:
        return None  # candidata sin blueprint reconstruible (ej. legacy discovery_validation_pipeline)

    route = str(candidate.get("route") or sc.get("route") or "").upper()
    if route != "FONDEO":
        return None  # este re-run solo interpreta el blueprint FONDEO (funding_discovery.py)

    dataset_id = candidate.get("dataset_id") or sc.get("dataset_id")
    dataset_hash_certificado = sc.get("dataset_hash")
    strategy_hash_certificado = sc.get("strategy_snapshot_hash")
    required = ("archetype", "ema_fast", "ema_slow", "sl_atr_mult", "tp_atr_mult", "risk_pct")
    if not dataset_id or not dataset_hash_certificado or not strategy_hash_certificado:
        return None
    if any(k not in params for k in required):
        return None

    try:
        from scripts.mine import load_candles_from_file, DATA_DIR as MINE_DATA_DIR
        from services.discovery.funding_discovery import FundingDiscoveryEngine
        from services.validation.engine.event_backtest_engine import EventBacktestEngine
    except ImportError:
        return None

    dataset_file = MINE_DATA_DIR / str(dataset_id)
    if not dataset_file.exists():
        return None
    sha_real = hashlib.sha256(dataset_file.read_bytes()).hexdigest()
    if sha_real != dataset_hash_certificado:
        return None  # el dataset en disco cambió desde la certificación: no se confía

    try:
        candles = load_candles_from_file(dataset_file)
    except (ValueError, FileNotFoundError, KeyError):
        return None
    total_bars = len(candles)
    if total_bars < 100:
        return None

    # Mismo particionado cronológico 60/20/20 que run_mining_pipeline() en scripts/mine.py --
    # duplicado intencional (no import de una función interna del CLI): si mine.py cambia su
    # particionado, el check de blind_oos_bars de abajo (y/o el hash del snapshot) lo detecta
    # y este re-run cae a None en vez de evaluar una ventana que ya no es la certificada.
    idx_val = int(total_bars * 0.80)
    oos_candles = candles[idx_val:]
    di = _extraer_duration_info(candidate)
    if di and isinstance(di.get("blind_oos_bars"), int) and di["blind_oos_bars"] != len(oos_candles):
        return None  # el particionado reconstruido no reproduce la ventana certificada

    exec_symbol = str(sc.get("execution_symbol") or candidate.get("symbol") or "")
    timeframe = str(candidate.get("timeframe") or sc.get("timeframe") or "")
    try:
        snapshot = FundingDiscoveryEngine().generate_candidate_blueprint(
            strategy_id=str(candidate.get("candidate_id") or candidate.get("name")),
            symbol=exec_symbol,
            timeframe=timeframe,
            dataset_id=str(dataset_id),
            dataset_sha256=sha_real,
            ema_fast=params["ema_fast"],
            ema_slow=params["ema_slow"],
            sl_atr_mult=params["sl_atr_mult"],
            tp_atr_mult=params["tp_atr_mult"],
            risk_per_trade_pct=params["risk_pct"],
            archetype=params["archetype"],
            archetype_params=params.get("archetype_params"),
        )
    except (KeyError, TypeError, ValueError):
        return None

    if snapshot.canonical_hash != strategy_hash_certificado:
        return None  # reconstrucción no reproduce el blueprint certificado: no se confía

    initial_cap = float(rules.account_size_usd)
    try:
        prop_profile = rules.to_engine_profile(initial_cap)
    except ValueError:
        return None  # capital de la firma no coincide con el capital base del backtest

    resultado = EventBacktestEngine().run_backtest(
        snapshot, oos_candles, initial_capital_usd=initial_cap, prop_profile=prop_profile,
    )
    return {
        "verificado_equity_flotante": True,
        "engine_version_reejecucion": CURRENT_ENGINE_VERSION,
        "prop_firm_busted": bool(resultado.prop_firm_busted),
        "prop_firm_violations": list(resultado.prop_firm_violations),
        "trades_oos_reales": int(resultado.total_trades),
        "profit_factor_oos_real": float(resultado.profit_factor),
        "net_profit_oos_usd_real": float(resultado.net_profit_usd),
    }


def determinar_veredicto_sellado(cumple_bootstrap: bool,
                                 verif_flotante: Optional[Dict[str, Any]]) -> str:
    """Veredicto FINAL del objetivo sellado F07 (W4.1): combina el Monte Carlo por bootstrap
    (COTA INFERIOR optimista, ver docstring de reejecutar_examen_barra_a_barra -- remuestrea
    PnL YA CERRADO, ciego a la excursión adversa intra-operación) con la verificación honesta
    barra a barra sobre equity FLOTANTE (prop_profile, F02.3).

    FAIL-CLOSED, sin excepciones:
      - Sin verificación barra a barra (verif_flotante is None -- no hay blueprint
        reconstruible, el dataset cambió de SHA-256, o se desactivó explícitamente con
        --sin-verificacion-flotante): el veredicto es SIEMPRE "NO_EVALUABLE". Nunca "CUMPLE"
        por defecto, nunca una caída silenciosa a lo que diga el bootstrap.
      - Con verificación disponible, una cuenta que la reprodujo REVENTADA
        (prop_firm_busted=True) es SIEMPRE "NO_CUMPLE", pase lo que pase en el bootstrap: el
        dato honesto (equity flotante, marcado a mercado barra a barra) manda sobre el
        optimista (PnL neto por operación ya cerrada).
      - Solo con verificación disponible Y la cuenta sin reventar en la reproducción real se
        deja que decida el resultado económico del bootstrap (mensual mediano / P(romper)
        sobre el horizonte, calculado en evaluar_rendimiento_mensual/evaluar_negocio).

    Devuelve "CUMPLE" | "NO_CUMPLE" | "NO_EVALUABLE" -- nunca un booleano ambiguo, para que
    ningún llamador pueda confundir "no evaluado" con "evaluado y rechazado".
    """
    if verif_flotante is None:
        return "NO_EVALUABLE"
    if verif_flotante.get("prop_firm_busted"):
        return "NO_CUMPLE"
    return "CUMPLE" if cumple_bootstrap else "NO_CUMPLE"


def deducir_ops_por_dia(candidate: Dict[str, Any], n_trades: int,
                        override: Optional[float] = None) -> Optional[float]:
    """Ritmo real de operaciones/día del periodo OOS. NO se asume (p.ej. 60 días fijos):
    se deduce del span real reportado por la certificación, o se usa `override` si el
    operador lo ha pasado explícitamente por CLI a sabiendas de que no hay dato real.
    Devuelve None si no hay forma honesta de calcularlo (la candidata se marca NO_EVALUABLE)."""
    if override is not None:
        return override
    span_dias = _span_oos_dias(_extraer_duration_info(candidate))
    if span_dias is None or span_dias <= 0:
        return None
    return n_trades / span_dias


# Multiplicadores de escalado explorados. Dos rejillas separadas porque las dos fases del
# negocio usan regímenes de riesgo distintos a propósito (ver docstring de CicloFondeado):
# Fase 1 (examen) agresiva, Fase 2 (cuenta ya fondeada) conservadora -- no tiene sentido
# barrer multiplicadores agresivos en la fase que por diseño debe ser conservadora.
MULTS_EXAMEN = (1, 2, 3, 5, 8, 12, 20, 30, 45)
MULTS_FONDEADA = (1, 2, 3, 5, 8)

UMBRAL_SELLADO_MENSUAL_PCT = 20.0  # F07 sellado: >=20% mensual SOSTENIBLE, sobre la MEDIANA
UMBRAL_SELLADO_BUST_6M = 0.20      # F07 sellado: P(romper cuenta) <=20% a 6 meses


def main() -> int:
    ap = argparse.ArgumentParser(description="Optimizador de paso de examen de fondeo.")
    ap.add_argument("--symbol", help="evaluar una candidata concreta; si se omite, todas las FONDEO")
    ap.add_argument("--firma", default=None,
                    help='Perfil REAL de firma del catálogo '
                         '(services/exploitation_engines/prop_firm_engine.py::PROP_FIRM_CATALOG). '
                         'Acepta la clave exacta ("APEX_50K") o un nombre con match difuso por '
                         'tokens ("Apex 50K"). Si se omite: reglas genéricas por CLI '
                         '(capital 50000, objetivo 8%%, pérdida diaria 2%%, DD 4%% trailing).')
    ap.add_argument("--capital", type=float, default=None,
                    help="override manual explícito (por defecto: account_size_usd de --firma, "
                         "o 50000 sin --firma)")
    ap.add_argument("--objetivo-pct", type=float, default=None,
                    help="override manual explícito (por defecto: derivado de --firma, u 8%% "
                         "sin --firma)")
    ap.add_argument("--perdida-diaria-pct", type=float, default=None,
                    help="override manual explícito (por defecto: derivado de --firma -- sin "
                         "límite si la firma no lo impone --, o 2%% sin --firma)")
    ap.add_argument("--dd-total-pct", type=float, default=None,
                    help="override manual explícito (por defecto: derivado de --firma, o 4%% "
                         "sin --firma)")
    ap.add_argument("--max-dias", type=int, default=8, help="ventana del examen (usuario: 3-8 dias)")
    ap.add_argument("--iteraciones", type=int, default=4000,
                    help="iteraciones Monte Carlo del examen (Fase 1, ventana --max-dias)")
    ap.add_argument("--iteraciones-negocio", type=int, default=800,
                    help="iteraciones Monte Carlo de la vida fondeada (Fase 2: rendimiento "
                         "mensual y P(romper cuenta) del ranking del objetivo sellado F07). "
                         "Menor que --iteraciones porque simula ventanas mucho más largas "
                         "(~30 y ~183 días frente a los 3-8 del examen); en un VPS compartido "
                         "con la campaña de minería hay que acotar el coste de CPU.")
    ap.add_argument("--horizonte-meses", type=float, default=6.0,
                    help="horizonte de P(romper cuenta) del objetivo sellado F07 (sellado: 6)")
    ap.add_argument("--umbral-retiro-pct", type=float, default=2.0,
                    help="beneficio mínimo (%% del capital) para solicitar un retiro en Fase 2")
    ap.add_argument("--dias-entre-retiros", type=int, default=14,
                    help="cadencia mínima entre retiros en Fase 2")
    ap.add_argument("--reparto-trader", type=float, default=0.90,
                    help="fracción del beneficio retirado que se queda el trader")
    ap.add_argument("--ops-por-dia-override", type=float, default=None,
                    help="fuerza el ritmo de operaciones/dia para TODAS las candidatas cuando "
                         "no traen duration_info real (oos_days/oos_months/fechas OOS). Uso "
                         "explicito y a sabiendas: sin esto, esas candidatas se marcan "
                         "NO_EVALUABLE en vez de asumir una ventana inventada.")
    # --- Economia del negocio de cartuchos (docs/tradesfera/02_MATEMATICA_BANKROLL) ---
    ap.add_argument("--coste-cartucho", type=float, default=58.20,
                    help="C_total = examen + activacion. Ej: Tradeify 50K = 58,20 USD")
    ap.add_argument("--payout-medio", type=float, default=2000.0,
                    help="R_avg: beneficio neto medio retirado por cuenta que llega a cobrar")
    ap.add_argument("--bankroll", type=float, default=3800.0,
                    help="capital destinado al programa de fondeo")
    ap.add_argument("--sin-verificacion-flotante", action="store_true",
                    help="desactiva el re-run barra a barra con prop_profile (equity FLOTANTE, "
                         "F02.3) antes del Monte Carlo. Por defecto se intenta SIEMPRE: es "
                         "barato cuando no hay blueprint reconstruible (falla rápido a None, "
                         "sin tocar el motor) y solo re-ejecuta el backtest real cuando sí lo "
                         "hay. Usa este flag para depurar el bootstrap en aislamiento.")
    ap.add_argument("--salida", default="orchestration/results/fondeo_examen.json")
    args = ap.parse_args()

    # --- Reglas: catálogo real (--firma) fusionado con overrides manuales explícitos -------
    if args.firma:
        try:
            rules = find_prop_firm(args.firma)
        except ValueError as e:
            print(f"ERROR: {e}")
            return 1
        base = _reglas_base_desde_firma(rules)
        print(f"Firma: {rules.firm_name}  (perfil real de PROP_FIRM_CATALOG)")
    else:
        base = {"capital": 50000.0, "objetivo_pct": 8.0, "perdida_diaria_pct": 2.0,
                "dd_total_pct": 4.0, "drawdown_type": "TRAILING_INTRADAY",
                "consistency_pct": None, "firma": None}

    capital = args.capital if args.capital is not None else base["capital"]
    objetivo_pct = args.objetivo_pct if args.objetivo_pct is not None else base["objetivo_pct"]
    perdida_diaria_pct = (args.perdida_diaria_pct if args.perdida_diaria_pct is not None
                          else base["perdida_diaria_pct"])
    dd_total_pct = args.dd_total_pct if args.dd_total_pct is not None else base["dd_total_pct"]

    reglas = ReglasExamen(capital, objetivo_pct, perdida_diaria_pct, dd_total_pct,
                          drawdown_type=base["drawdown_type"],
                          consistency_pct=base["consistency_pct"], firma=base["firma"])
    ciclo = CicloFondeado(capital, args.umbral_retiro_pct, args.dias_entre_retiros,
                          args.reparto_trader, dd_total_pct, perdida_diaria_pct,
                          drawdown_type=base["drawdown_type"],
                          consistency_pct=base["consistency_pct"], firma=base["firma"])

    # PropFirmRules EFECTIVAS (catálogo + overrides ya fusionados arriba): la misma instancia
    # que consume reejecutar_examen_barra_a_barra() vía PropFirmRules.to_engine_profile(), para
    # que el re-run barra a barra evalúe EXACTAMENTE las reglas que usa el Monte Carlo de abajo
    # (capital, DD total, pérdida diaria), nunca un perfil distinto por accidente.
    rules_efectivas = PropFirmRules(
        firm_name=base["firma"] or "GENERICO_CLI",
        account_size_usd=capital,
        profit_target_usd=reglas.objetivo,
        max_total_drawdown_usd=reglas.dd_total,
        drawdown_type=base["drawdown_type"],
        daily_loss_limit_usd=reglas.perdida_diaria if perdida_diaria_pct is not None else None,
        consistency_pct=base["consistency_pct"],
    )

    engine = MetaStrategyEngine()
    cands = engine.load_candidates_from_db(route="FONDEO")
    if args.symbol:
        cands = [c for c in cands if str(c.get("symbol")) == args.symbol]

    if not cands:
        print("NO DATA: no hay candidatas FONDEO con retornos OOS reales en la base canónica.")
        print("La campaña de descubrimiento aún no ha producido ninguna. No se inventa nada.")
        return 1

    dias_horizonte = max(1, round(args.horizonte_meses * DIAS_POR_MES))
    print(f"Reglas del examen: capital {reglas.capital:,.0f} · objetivo {objetivo_pct:.2f}% "
          f"({reglas.objetivo:,.0f}) · pérdida diaria "
          f"{'sin límite' if perdida_diaria_pct is None else f'{perdida_diaria_pct:.2f}%'} · "
          f"DD total {dd_total_pct:.2f}% ({reglas.drawdown_type}) · consistencia "
          f"{'N/A' if reglas.consistency_pct is None else f'{reglas.consistency_pct:.0f}%'} · "
          f"ventana {args.max_dias} días")
    p_be = args.coste_cartucho / args.payout_medio
    n_intentos = int(args.bankroll // args.coste_cartucho)
    print(f"Método: {args.iteraciones:,} exámenes simulados (Fase 1) + "
          f"{args.iteraciones_negocio:,} vidas fondeadas (Fase 2, horizonte "
          f"{args.horizonte_meses:.0f} meses = {dias_horizonte} días) por remuestreo de "
          f"operaciones REALES")
    print(f"\nECONOMÍA DEL NEGOCIO (docs/tradesfera/02_MATEMATICA_BANKROLL_Y_CAPITAL_MUNICION.md):")
    print(f"  Coste por cartucho C_total : {args.coste_cartucho:,.2f} USD")
    print(f"  Payout medio R_avg         : {args.payout_medio:,.0f} USD")
    print(f"  Bankroll                   : {args.bankroll:,.0f} USD -> {n_intentos} intentos")
    print(f"  UMBRAL DE RENTABILIDAD     : p_be = C_total/R_avg = {p_be:.2%}")
    print(f"  >>> Por encima de {p_be:.2%} de probabilidad de aprobar, la esperanza YA es positiva.")
    print(f"  >>> Romper una cuenta no es una catastrofe: cuesta un cartucho y se dispara otro.")
    print(f"\nOBJETIVO SELLADO F07 (Emilio, 2026-08-31): mensual mediano >= "
          f"{UMBRAL_SELLADO_MENSUAL_PCT:.0f}% Y P(romper cuenta) a {args.horizonte_meses:.0f} "
          f"meses <= {UMBRAL_SELLADO_BUST_6M:.0%}. Se reporta la cifra REAL; si ninguna "
          f"estrategia lo cumple, no se ajustan umbrales para maquillarlo.\n")

    resultados: Dict[str, Any] = {}
    ranking: List[Dict[str, Any]] = []
    no_evaluables: List[Dict[str, Any]] = []

    for c in cands:
        trades = np.array(c["oos_returns"], dtype=float)
        cap0 = float(c.get("initial_capital_usd") or reglas.capital)
        trades = trades / cap0 * reglas.capital      # normalizar al capital del examen
        nombre = str(c.get("name"))

        # Ritmo real observado: NO se asume una ventana fija, se deduce del span OOS real
        # reportado por la certificación (duration_info). Fail-closed si no hay dato real.
        ops_por_dia = deducir_ops_por_dia(c, len(trades), override=args.ops_por_dia_override)
        if ops_por_dia is None:
            print(f"=== {nombre}  ({c.get('symbol')} {c.get('timeframe')}, "
                  f"{len(trades)} operaciones reales) === NO_EVALUABLE")
            print("  -> Sin duration_info real (oos_days/oos_months/fechas OOS) para deducir "
                  "el ritmo de operaciones/día. No se asume una ventana arbitraria (REAL-ONLY). "
                  "Usa --ops-por-dia-override si quieres forzar un valor a sabiendas.\n")
            entrada = {"mejor": None, "operaciones": len(trades), "estado": "NO_EVALUABLE",
                      "motivo": "sin duration_info real para deducir ops_por_dia"}
            resultados[nombre] = entrada
            no_evaluables.append({"nombre": nombre, **entrada})
            continue

        print(f"=== {nombre}  ({c.get('symbol')} {c.get('timeframe')}, "
              f"{len(trades)} operaciones reales, {ops_por_dia:.2f} ops/día reales) ===")

        # --- Camino honesto (F02.3, CUELLO 2): el Monte Carlo de abajo remuestrea PnL YA
        # CERRADO por operación -- no ve la excursión adversa DENTRO de un trade, que es
        # exactamente lo que revienta cuentas reales. Se intenta el re-run barra a barra con
        # prop_profile (equity FLOTANTE) como ancla de verdad; si no hay blueprint reconstruible
        # (hoy: ninguna candidata FONDEO en la BD lo tiene -- todas son legacy motor 5.4.0
        # anteriores a F02.3/F02.4, o carecen de "parameters" reconstruible) se marca
        # explícitamente NO VERIFICADO en vez de dar el bootstrap por bueno en silencio.
        if args.sin_verificacion_flotante:
            verif_flotante = None
        else:
            verif_flotante = reejecutar_examen_barra_a_barra(c, rules_efectivas)
        if verif_flotante is None:
            print("  [equity flotante] NO VERIFICADO -- sin blueprint reconstruible fiel "
                  "(o dataset/hash no coinciden) para esta candidata con el motor actual. "
                  "El P(romper cuenta) de abajo es una COTA INFERIOR optimista: el bootstrap "
                  "solo ve PnL cerrado, no la excursión adversa intra-operación.")
        else:
            estado_prop = "REVENTADA" if verif_flotante["prop_firm_busted"] else "sin reventar"
            print(f"  [equity flotante] VERIFICADO barra a barra (motor "
                  f"{verif_flotante['engine_version_reejecucion']}) sobre el histórico OOS real: "
                  f"cuenta {estado_prop} · {verif_flotante['trades_oos_reales']} operaciones "
                  f"reales · violaciones={verif_flotante['prop_firm_violations'] or 'ninguna'}")

        print(f"{'mult':>6} {'P(pasar)':>10} {'ROI/cartucho':>13} {'EV pool':>12} "
              f"{'días med':>9}  veredicto")

        # --- Fase 1 (agresiva): pasar el examen, economía del cartucho -----------------
        mejor = None
        por_mult_examen: Dict[float, Dict[str, Any]] = {}
        for mult in MULTS_EXAMEN:
            r = evaluar(trades, ops_por_dia, reglas, float(mult), args.iteraciones, args.max_dias)
            por_mult_examen[mult] = r
            # ROI unitario = p*R_avg/C_total - 1   (formula 2.4 del dossier Tradesfera)
            roi = (r["p_pasar"] * args.payout_medio / args.coste_cartucho) - 1.0
            ev_pool = n_intentos * (r["p_pasar"] * args.payout_medio - args.coste_cartucho)
            r["roi_cartucho"] = round(roi, 3)
            r["ev_pool_usd"] = round(ev_pool, 0)
            marca = "RENTABLE" if roi > 0 else "pierde dinero"
            print(f"{mult:>6} {r['p_pasar']:>10.1%} {roi:>12.1%} {ev_pool:>11,.0f}$ "
                  f"{str(r['dias_mediana'] or '-'):>9}  {marca}")
            if roi > 0 and (mejor is None or roi > mejor["roi_cartucho"]):
                mejor = r
        if mejor:
            print(f"  -> ÓPTIMO ECONÓMICO (cartucho): multiplicador {mejor['multiplicador']} · "
                  f"P(pasar)={mejor['p_pasar']:.1%} (umbral {p_be:.2%}) · "
                  f"ROI por cartucho {mejor['roi_cartucho']:.0%} · "
                  f"EV del pool {mejor['ev_pool_usd']:,.0f}$ · mediana {mejor['dias_mediana']} días")
        else:
            print(f"  -> NINGUNA configuración supera el umbral de {p_be:.2%}. Esta estrategia "
                  f"no da dinero ni como negocio de cartuchos. Se reporta tal cual.")

        # --- Fase 2 (conservadora): objetivo SELLADO F07 --------------------------------
        # Búsqueda separada de la Fase 1 (regímenes de riesgo distintos, ver docstring de
        # CicloFondeado). Entre TODOS los multiplicadores que se mantienen bajo el techo de
        # rotura del horizonte, se elige el que MAXIMIZA el rendimiento mensual mediano.
        # Nunca al revés: nunca se sacrifica el techo de rotura por más rendimiento.
        candidatas_sostenibles = []
        for mult in MULTS_FONDEADA:
            rend = evaluar_rendimiento_mensual(trades, ops_por_dia, ciclo, float(mult),
                                               args.iteraciones_negocio)
            negocio = evaluar_negocio(trades, ops_por_dia, ciclo, float(mult),
                                      args.iteraciones_negocio, dias_horizonte)
            candidatas_sostenibles.append({**rend, "p_romper_cuenta_horizonte": negocio["p_romper"]})

        elegibles = [f for f in candidatas_sostenibles
                    if f["p_romper_cuenta_horizonte"] <= UMBRAL_SELLADO_BUST_6M]
        if elegibles:
            elegida = max(elegibles, key=lambda f: f["retorno_mensual_mediana_pct"])
        else:
            # Ninguna configuración se mantiene bajo el techo de rotura sellado: se reporta
            # la escala REAL (multiplicador 1x, sin escalar) como referencia honesta -- nunca
            # se elige un multiplicador que maquille el resultado.
            elegida = next(f for f in candidatas_sostenibles if f["mult_fondeada"] == 1.0)

        mult_fondeada_elegido = elegida["mult_fondeada"]
        # Decisión ECONÓMICA del bootstrap (optimista, ciego a la excursión adversa
        # intra-operación) -- NUNCA es el veredicto final por sí sola. Ver W4.1.
        cumple_sellado_bootstrap = (
            elegida["retorno_mensual_mediana_pct"] >= UMBRAL_SELLADO_MENSUAL_PCT
            and elegida["p_romper_cuenta_horizonte"] <= UMBRAL_SELLADO_BUST_6M
        )
        # Veredicto FINAL (W4.1, fail-closed): decide con la verificación honesta barra a
        # barra, no con el bootstrap. Sin verificación -> NO_EVALUABLE, jamás CUMPLE por
        # defecto. Con verificación y cuenta reventada -> NO_CUMPLE, aunque el bootstrap
        # dijera lo contrario. Ver determinar_veredicto_sellado().
        veredicto_sellado = determinar_veredicto_sellado(cumple_sellado_bootstrap, verif_flotante)
        cumple_sellado = veredicto_sellado == "CUMPLE"

        # Días esperados / P(pasar) del examen: del mismo multiplicador usado para pasarlo
        # (óptimo cartucho si lo hay; si no, escala real 1x -- misma convención que Fase 2).
        mult_examen_elegido = mejor["multiplicador"] if mejor else 1.0
        r_examen = por_mult_examen.get(mult_examen_elegido) or por_mult_examen[1]

        veredicto = {"CUMPLE": "CUMPLE", "NO_CUMPLE": "no cumple",
                    "NO_EVALUABLE": "NO_EVALUABLE (sin verificación barra a barra)"}[veredicto_sellado]
        print(f"  -> SOSTENIBLE (objetivo sellado F07, x{mult_fondeada_elegido:g} fondeada): "
              f"mensual mediano {elegida['retorno_mensual_mediana_pct']:+.1f}% "
              f"(p5 {elegida['retorno_mensual_p5_pct']:+.1f}% / "
              f"p95 {elegida['retorno_mensual_p95_pct']:+.1f}%) · "
              f"P(romper cuenta {args.horizonte_meses:.0f}m) "
              f"{elegida['p_romper_cuenta_horizonte']:.1%} · {veredicto}")
        print()

        entrada = {
            "mejor": mejor,
            "operaciones": len(trades),
            "sostenible_f07": {
                "multiplicador_fondeada": mult_fondeada_elegido,
                "retorno_mensual_mediana_pct": elegida["retorno_mensual_mediana_pct"],
                "retorno_mensual_p5_pct": elegida["retorno_mensual_p5_pct"],
                "retorno_mensual_p95_pct": elegida["retorno_mensual_p95_pct"],
                "p_romper_cuenta_horizonte": elegida["p_romper_cuenta_horizonte"],
                "horizonte_meses": args.horizonte_meses,
                "cumple_objetivo_sellado_bootstrap": cumple_sellado_bootstrap,
                "veredicto_sellado": veredicto_sellado,
                "cumple_objetivo_sellado": cumple_sellado,
            },
            "firma": base["firma"],
            # F02.3 (CUELLO 2): resultado del re-run barra a barra con prop_profile sobre
            # equity FLOTANTE, o None si no hay blueprint reconstruible para esta candidata
            # con el motor actual (ver reejecutar_examen_barra_a_barra). Cuando es None, TODO
            # p_romper_cuenta de arriba es una COTA INFERIOR optimista, no el número honesto.
            "verificacion_equity_flotante": verif_flotante,
        }
        resultados[nombre] = entrada

        ranking.append({
            "nombre": nombre,
            "symbol": c.get("symbol"),
            "timeframe": c.get("timeframe"),
            "firma": base["firma"],
            "dias_esperados_mediana": r_examen["dias_mediana"],
            "p_pasar_examen": r_examen["p_pasar"],
            "multiplicador_examen": mult_examen_elegido,
            "p_romper_cuenta": elegida["p_romper_cuenta_horizonte"],
            "horizonte_meses": args.horizonte_meses,
            "rendimiento_mensual_mediano_pct": elegida["retorno_mensual_mediana_pct"],
            "rendimiento_mensual_p5_pct": elegida["retorno_mensual_p5_pct"],
            "rendimiento_mensual_p95_pct": elegida["retorno_mensual_p95_pct"],
            "multiplicador_fondeada": mult_fondeada_elegido,
            "cumple_objetivo_sellado_bootstrap": cumple_sellado_bootstrap,
            "veredicto_sellado": veredicto_sellado,
            "cumple_objetivo_sellado": cumple_sellado,
            "verificado_equity_flotante": verif_flotante is not None,
            "prop_firm_busted_verificado": (verif_flotante or {}).get("prop_firm_busted"),
        })

    # Ranking ORDENADO (item F07): primero quien CUMPLE de verdad (verificado barra a barra,
    # no reventado, y económicamente sostenible), luego NO_CUMPLE, y al final NO_EVALUABLE
    # (sin verificación honesta -- ninguna candidata sin verificar puede colarse por delante
    # de una candidata verificada que no cumple, aunque su bootstrap se vea mejor). Dentro de
    # cada grupo, por rendimiento mensual mediano descendente y, a igualdad, menor P(romper).
    _PRIORIDAD_VEREDICTO = {"CUMPLE": 0, "NO_CUMPLE": 1, "NO_EVALUABLE": 2}
    ranking.sort(key=lambda f: (_PRIORIDAD_VEREDICTO[f["veredicto_sellado"]],
                                -f["rendimiento_mensual_mediano_pct"],
                                f["p_romper_cuenta"]))

    if ranking:
        print("=" * 100)
        print(f"RANKING (objetivo sellado F07: mensual mediano >= "
              f"{UMBRAL_SELLADO_MENSUAL_PCT:.0f}% · P(romper cuenta) <= "
              f"{UMBRAL_SELLADO_BUST_6M:.0%} a {args.horizonte_meses:.0f} meses)")
        print("=" * 100)
        print(f"{'#':>3} {'estrategia':<30} {'días':>6} {'P(pasar)':>9} {'mensual med.':>13} "
              f"{'P(romper)':>10}  veredicto")
        _VEREDICTO_TXT = {"CUMPLE": "CUMPLE", "NO_CUMPLE": "no cumple",
                         "NO_EVALUABLE": "NO_EVALUABLE (sin verif. barra a barra)"}
        for i, fila in enumerate(ranking, 1):
            veredicto_txt = _VEREDICTO_TXT[fila["veredicto_sellado"]]
            dias_txt = str(fila["dias_esperados_mediana"] or "-")
            print(f"{i:>3} {fila['nombre'][:30]:<30} {dias_txt:>6} "
                  f"{fila['p_pasar_examen']:>9.1%} "
                  f"{fila['rendimiento_mensual_mediano_pct']:>+12.1f}% "
                  f"{fila['p_romper_cuenta']:>10.1%}  {veredicto_txt}")
        n_verificadas = sum(1 for f in ranking if f["verificado_equity_flotante"])
        if n_verificadas < len(ranking):
            print(f"\nAVISO METODOLÓGICO (F02.3, CUELLO 2, W4.1): {len(ranking) - n_verificadas}/"
                  f"{len(ranking)} candidatas del ranking SIN verificar barra a barra sobre "
                  "equity flotante -- se marcan NO_EVALUABLE (nunca CUMPLE) y su "
                  "p_romper_cuenta es una COTA INFERIOR optimista (bootstrap ciego a la "
                  "excursión adversa intra-operación), no el riesgo real. "
                  "Motivo: scripts/mine.py hoy solo persiste el blueprint reconstruible "
                  "(\"parameters\") para candidatas certificadas 11/11 con el motor actual; "
                  "ninguna candidata FONDEO en la BD lo cumple todavía (todas motor 5.4.0, "
                  "anteriores a F02.3).")
        n_cumple = sum(1 for f in ranking if f["cumple_objetivo_sellado"])
        if n_cumple:
            print(f"\n{n_cumple}/{len(ranking)} estrategias CUMPLEN el objetivo sellado.")
        else:
            peor_pero_mejor = ranking[0]
            print(f"\nNINGUNA estrategia cumple el objetivo sellado. La mejor real: "
                  f"'{peor_pero_mejor['nombre']}' con "
                  f"{peor_pero_mejor['rendimiento_mensual_mediano_pct']:+.1f}% mensual mediano "
                  f"y P(romper cuenta)={peor_pero_mejor['p_romper_cuenta']:.1%} a "
                  f"{args.horizonte_meses:.0f} meses. Se reporta tal cual: no se ajustan "
                  "umbrales para que algo pase (doctrina F07).")
        print()

    salida = {
        "ranking": ranking,
        "no_evaluables": no_evaluables,
        "objetivo_sellado_f07": {
            "rendimiento_mensual_mediano_pct_minimo": UMBRAL_SELLADO_MENSUAL_PCT,
            "p_romper_cuenta_maxima": UMBRAL_SELLADO_BUST_6M,
            "horizonte_meses": args.horizonte_meses,
            "medido_sobre": "mediana de la distribución Monte Carlo, nunca la media",
        },
        "aviso_metodologico_equity_flotante": (
            "El Monte Carlo por bootstrap remuestrea PnL YA CERRADO por operación; no ve la "
            "excursión adversa DENTRO de un trade. p_romper_cuenta es una COTA INFERIOR "
            "optimista salvo que 'verificacion_equity_flotante' en detalle_por_estrategia sea "
            "no-nulo (re-run barra a barra con prop_profile sobre equity flotante, F02.3)."
        ),
        "detalle_por_estrategia": resultados,
    }

    destino = ROOT / args.salida
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(salida, indent=2, ensure_ascii=False, default=str),
                       encoding="utf-8")
    print(f"Resultados en {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
