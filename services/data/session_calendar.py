"""services/data/session_calendar.py
Calendario de sesion para auditoria de cobertura de datos de mercado.

Cripto (BingX, Binance) cotiza 24/7: cualquier hueco entre barras consecutivas es una anomalia
real, sin excepcion. CME, forex y sus proxies (Dukascopy) SOLO operan en horario de sesion:
cierran el fin de semana, tienen una pausa diaria de mantenimiento, y ademas pierden sesion
completa (o parte de ella) los dias de festivo del mercado. Medir su cobertura contra un
calendario continuo 24/7 hace que un dataset perfecto marque ~68.5% (CME) o ~71.4% (forex) de
cobertura y jamas pueda ser `is_valid` -- ver
`orchestration/results/desbloqueo_tradfi_calidad_datos.md`, que documenta el bloqueo real que
esto causo sobre el carril TRADFI.

Este modulo REUTILIZA los umbrales pausa_diaria/fin_de_semana ya validados empiricamente por
`scripts/herramientas/consolidar_dukascopy.py::classify_gap` (en vez de duplicarlos: se
importan directamente sus constantes y su funcion) y anade encima una capa de deteccion de
FESTIVO que ese script no hace -- alli un festivo cae en su bolsa "anomalo", documentado
explicitamente como tal en su propio docstring ("anomalo: el resto (festivos, fines de semana
alargados por un festivo pegado, huecos de datos reales)").

La deteccion de festivo NO usa una lista de fechas fija (caducaria cada ano y nadie la
actualizaria): se deduce por la FORMA del hueco (duracion + dia de la semana en el que
empieza/termina), calibrada sobre datos reales de USA500IDXUSD 15m 2023-2026
(`data/normalized/ds_dukascopy_usa500idxusd_15m_consolidated_manifest.json`, proxy de ES/MES),
donde los 36 huecos "anomalo" que dejaba el consolidador se agrupan en EXACTAMENTE tres bandas,
sin un solo caso intermedio:

  - 5.0h-8.75h  (26 casos): cierre parcial/adelantado por festivo (MLK, Presidents Day,
    Memorial Day, Juneteenth, 4 de Julio, Labor Day, viernes de Accion de Gracias...).
  - 26h-29h     (5 casos):  festivo entre semana que no cae pegado al fin de semana
    (Navidad/Ano Nuevo cuando caen en martes/miercoles).
  - 74h         (5 casos):  fin de semana alargado por un festivo pegado (Good Friday, Navidad/
    Ano Nuevo cuando caen en viernes/lunes).

Fuera de esas tres bandas (incluida la zona muerta 8.75h-20h, donde no aparece NINGUN caso real
en los datos calibrados) el hueco se deja como "anomalo": se prefiere infravalorar festivos poco
frecuentes (quedan contando como cobertura perdida) a enmascarar un hueco de datos real como si
fuera un festivo. Este es un limite conocido y deliberado del heuristico: un apagon real de
datos de duracion parecida a un cierre por festivo (p.ej. ~6h en un martes cualquiera) se
clasificaria como festivo. La alternativa -- una lista de fechas de festivos mantenida a mano --
caduca cada ano; este heuristico no.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Tuple

from scripts.herramientas.consolidar_dukascopy import (
    PAUSA_DIARIA_MAX_HOURS,
    WEEKEND_END_WEEKDAYS,
    WEEKEND_MAX_HOURS,
    WEEKEND_MIN_HOURS,
    WEEKEND_START_WEEKDAYS,
    classify_gap as _classify_session_gap,
)

# Venues que cotizan 24 horas / 7 dias. Todo lo que no este aqui (CME, forex, Dukascopy y
# cualquier otro venue TradFi) se audita contra el calendario de sesion de mas abajo, nunca
# contra un calendario 24/7.
CRYPTO_VENUES = frozenset({"BINGX", "BINANCE"})

# --- Bandas de festivo, calibradas empiricamente (ver docstring del modulo) -----------------
HOLIDAY_SHORT_CLOSURE_MIN_HOURS = PAUSA_DIARIA_MAX_HOURS  # estrictamente mas que una pausa normal
HOLIDAY_SHORT_CLOSURE_MAX_HOURS = 10.0                    # cierre parcial/adelantado por festivo
HOLIDAY_MIDWEEK_MIN_HOURS = 20.0                          # festivo entre semana (dia completo)
HOLIDAY_MIDWEEK_MAX_HOURS = WEEKEND_MIN_HOURS             # hasta el umbral de fin de semana
HOLIDAY_WEEKEND_MAX_HOURS = WEEKEND_MAX_HOURS + 34.0      # fin de semana + festivo pegado (~94h)

GapType = str  # "contiguo" | "pausa_diaria" | "fin_de_semana" | "festivo" | "anomalo"


def is_24_7_venue(venue: str) -> bool:
    """True si `venue` opera de forma continua (cripto): alli cualquier hueco es anomalo."""
    return (venue or "").strip().upper() in CRYPTO_VENUES


def classify_gap(venue: str, prev_ts_ms: int, next_ts_ms: int) -> Tuple[GapType, float]:
    """Clasifica un hueco entre dos barras consecutivas segun el calendario de sesion de `venue`.

    Devuelve (tipo, horas). Para venues 24/7 el tipo es siempre 'anomalo': no existe cierre de
    sesion que explique un hueco en un mercado que nunca cierra (asi el calculo de cobertura de
    cripto queda IDENTICO al de antes de este modulo). Para el resto se reutiliza
    `consolidar_dukascopy.classify_gap` (pausa_diaria/fin_de_semana/anomalo) tal cual, y lo que
    esa funcion deje en 'anomalo' se reclasifica como 'festivo' si su forma coincide con una de
    las tres bandas calibradas arriba.
    """
    if is_24_7_venue(venue):
        hours = (next_ts_ms - prev_ts_ms) / 3_600_000.0
        return "anomalo", hours

    gap_type, hours = _classify_session_gap(prev_ts_ms, next_ts_ms)
    if gap_type != "anomalo":
        return gap_type, hours

    if HOLIDAY_SHORT_CLOSURE_MIN_HOURS < hours <= HOLIDAY_SHORT_CLOSURE_MAX_HOURS:
        return "festivo", hours

    if HOLIDAY_MIDWEEK_MIN_HOURS <= hours < HOLIDAY_MIDWEEK_MAX_HOURS:
        return "festivo", hours

    if WEEKEND_MAX_HOURS < hours <= HOLIDAY_WEEKEND_MAX_HOURS:
        prev_dt = datetime.fromtimestamp(prev_ts_ms / 1000.0, tz=timezone.utc)
        next_dt = datetime.fromtimestamp(next_ts_ms / 1000.0, tz=timezone.utc)
        if prev_dt.weekday() in WEEKEND_START_WEEKDAYS and next_dt.weekday() in WEEKEND_END_WEEKDAYS:
            return "festivo", hours

    return "anomalo", hours
