"""orchestration/results/agy/A09_muestreo.py
Muestreo de dias en invierno (enero) y verano (julio) sobre la sesion y el ledger de ES.
Verifica:
1. Hora UTC de apertura en invierno (14:30 UTC) vs verano (13:30 UTC).
2. Hora UTC del flat obligatorio a las 15:10 CT (21:10 UTC invierno, 20:10 UTC verano).
3. No hay operaciones abiertas tras el flat 15:10 CT ni velas fuera de sesion tratadas como activas.
"""

from __future__ import annotations

import datetime as d
import json
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from contracts.canonical_strategy import SessionWindow
from services.discovery.funding_discovery import resolve_session_window
from services.validation.engine.event_backtest_engine import EventBacktestEngine


def main() -> int:
    sw_rth = resolve_session_window("ES", "SESSION_MOMENTUM")
    sw_globex = resolve_session_window("ES", "TREND_FOLLOWING")

    print("=== 1. VERIFICACION DE SESION RTH (America/New_York 09:30-16:00, flat 15:10 CT) ===")
    print(f"sw_rth: market_tz={sw_rth.market_tz}, start_local={sw_rth.start_time_local}, end_local={sw_rth.end_time_local}, flat_local={sw_rth.flat_time_local}, flat_tz={sw_rth.flat_tz}")

    dias_invierno = [
        d.date(2023, 1, 16),  # Lunes (MLK day calendar / regular session test date)
        d.date(2023, 1, 17),  # Martes
        d.date(2023, 1, 18),  # Miércoles
    ]

    dias_verano = [
        d.date(2023, 7, 17),  # Lunes
        d.date(2023, 7, 18),  # Martes
        d.date(2023, 7, 19),  # Miércoles
    ]

    print("\n--- Muestreo Invierno (Enero 2023, EST = UTC-5) ---")
    for dia in dias_invierno:
        # Horas UTC clave a probar:
        # 13:30 UTC = 08:30 EST (Pre-mercado -> debe ser False para RTH)
        # 14:15 UTC = 09:15 EST (Pre-mercado -> False)
        # 14:30 UTC = 09:30 EST (Apertura RTH -> True)
        # 20:00 UTC = 15:00 EST / 14:00 CST (Dentro de sesion -> True)
        # 21:00 UTC = 16:00 EST / 15:00 CST (Fin RTH -> True / boundary)
        # 21:10 UTC = 16:10 EST / 15:10 CST (Flat obligatorio Topstep -> False / Session End)
        # 22:00 UTC = 17:00 EST / 16:00 CST (Post-mercado -> False)
        t_pre = d.datetime(dia.year, dia.month, dia.day, 13, 30, tzinfo=d.timezone.utc)
        t_open = d.datetime(dia.year, dia.month, dia.day, 14, 30, tzinfo=d.timezone.utc)
        t_mid = d.datetime(dia.year, dia.month, dia.day, 18, 0, tzinfo=d.timezone.utc)
        t_flat = d.datetime(dia.year, dia.month, dia.day, 21, 10, tzinfo=d.timezone.utc)
        t_post = d.datetime(dia.year, dia.month, dia.day, 22, 0, tzinfo=d.timezone.utc)

        in_pre = EventBacktestEngine._is_in_session_window(t_pre, sw_rth)
        in_open = EventBacktestEngine._is_in_session_window(t_open, sw_rth)
        in_mid = EventBacktestEngine._is_in_session_window(t_mid, sw_rth)
        in_flat = EventBacktestEngine._is_in_session_window(t_flat, sw_rth)
        end_flat = EventBacktestEngine._is_session_end(t_flat, sw_rth)
        in_post = EventBacktestEngine._is_in_session_window(t_post, sw_rth)

        print(f"Día {dia} (Invierno EST):")
        print(f"  13:30 UTC (08:30 EST): in_session={in_pre} (esperado: False)")
        print(f"  14:30 UTC (09:30 EST): in_session={in_open} (esperado: True)")
        print(f"  18:00 UTC (13:00 EST): in_session={in_mid} (esperado: True)")
        print(f"  21:10 UTC (15:10 CST): in_session={in_flat} is_session_end={end_flat} (esperado: in=False, end=True)")
        print(f"  22:00 UTC (17:00 EST): in_session={in_post} (esperado: False)")

    print("\n--- Muestreo Verano (Julio 2023, EDT = UTC-4) ---")
    for dia in dias_verano:
        # Horas UTC clave a probar:
        # 12:30 UTC = 08:30 EDT (Pre-mercado -> False)
        # 13:30 UTC = 09:30 EDT (Apertura RTH -> True)
        # 18:00 UTC = 14:00 EDT (Dentro de sesion -> True)
        # 20:00 UTC = 16:00 EDT / 15:00 CDT (Fin RTH -> True / boundary)
        # 20:10 UTC = 16:10 EDT / 15:10 CDT (Flat obligatorio Topstep -> False / Session End)
        # 21:00 UTC = 17:00 EDT (Post-mercado -> False)
        t_pre = d.datetime(dia.year, dia.month, dia.day, 12, 30, tzinfo=d.timezone.utc)
        t_open = d.datetime(dia.year, dia.month, dia.day, 13, 30, tzinfo=d.timezone.utc)
        t_mid = d.datetime(dia.year, dia.month, dia.day, 18, 0, tzinfo=d.timezone.utc)
        t_flat = d.datetime(dia.year, dia.month, dia.day, 20, 10, tzinfo=d.timezone.utc)
        t_post = d.datetime(dia.year, dia.month, dia.day, 21, 0, tzinfo=d.timezone.utc)

        in_pre = EventBacktestEngine._is_in_session_window(t_pre, sw_rth)
        in_open = EventBacktestEngine._is_in_session_window(t_open, sw_rth)
        in_mid = EventBacktestEngine._is_in_session_window(t_mid, sw_rth)
        in_flat = EventBacktestEngine._is_in_session_window(t_flat, sw_rth)
        end_flat = EventBacktestEngine._is_session_end(t_flat, sw_rth)
        in_post = EventBacktestEngine._is_in_session_window(t_post, sw_rth)

        print(f"Día {dia} (Verano EDT):")
        print(f"  12:30 UTC (08:30 EDT): in_session={in_pre} (esperado: False)")
        print(f"  13:30 UTC (09:30 EDT): in_session={in_open} (esperado: True)")
        print(f"  18:00 UTC (14:00 EDT): in_session={in_mid} (esperado: True)")
        print(f"  20:10 UTC (15:10 CDT): in_session={in_flat} is_session_end={end_flat} (esperado: in=False, end=True)")
        print(f"  21:00 UTC (17:00 EDT): in_session={in_post} (esperado: False)")

    print("\n=== 2. MUESTREO DE OPERACIONES DEL LEDGER REPRODUCIDO (A09_celda.json) ===")
    celda_path = REPO_ROOT / "orchestration" / "results" / "agy" / "A09_celda.json"
    if celda_path.exists():
        cdata = json.loads(celda_path.read_text(encoding="utf-8"))
        trades = cdata.get("trades", [])
        print(f"Total trades en celda ES 4h c1: {len(trades)}")
        print("Primeros 5 trades del ledger:")
        for idx, tr in enumerate(trades[:5], 1):
            print(f"  Trade {idx}: entry_bar={tr['entry_bar']} exit_bar={tr['exit_bar']} side={tr['side']} pnl={tr['net_pnl_usd']:.2f} exit_reason={tr['exit_reason']}")
        print("Ultimos 5 trades del ledger:")
        for idx, tr in enumerate(trades[-5:], len(trades)-4):
            print(f"  Trade {idx}: entry_bar={tr['entry_bar']} exit_bar={tr['exit_bar']} side={tr['side']} pnl={tr['net_pnl_usd']:.2f} exit_reason={tr['exit_reason']}")

    print("\n=== 3. VERIFICACION DE FIN DE SEMANA Y FESTIVOS ===")
    # Sabado (dia 5 de semana)
    t_sat = d.datetime(2023, 1, 21, 15, 0, tzinfo=d.timezone.utc)
    in_sat_rth = EventBacktestEngine._is_in_session_window(t_sat, sw_rth)
    in_sat_globex = EventBacktestEngine._is_in_session_window(t_sat, sw_globex)
    print(f"Sábado 2023-01-21 15:00 UTC: in_session_rth={in_sat_rth} (esperado: False), in_session_globex={in_sat_globex} (esperado: False)")

    # Domingo antes de las 18:00 ET (23:00 UTC invierno)
    t_sun_early = d.datetime(2023, 1, 22, 18, 0, tzinfo=d.timezone.utc)
    # Domingo reapertura Globex 18:00 ET (23:00 UTC invierno)
    t_sun_open = d.datetime(2023, 1, 22, 23, 0, tzinfo=d.timezone.utc)
    in_sun_early = EventBacktestEngine._is_in_session_window(t_sun_early, sw_globex)
    in_sun_open = EventBacktestEngine._is_in_session_window(t_sun_open, sw_globex)
    print(f"Domingo 2023-01-22 18:00 UTC (13:00 EST): in_session_globex={in_sun_early} (esperado: False)")
    print(f"Domingo 2023-01-22 23:00 UTC (18:00 EST): in_session_globex={in_sun_open} (esperado: True)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
