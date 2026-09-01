# CONTRATO W2.9 — Motor 5.18.0: sesiones conscientes de DST y ventana por familia (regla #26)

> Emitido por el ORQUESTADOR LOCAL el 2026-09-01 (ciclo 2), a partir del expediente
> `orchestration/results/forense_familias_ES15m.md` (carril FORENSE), **cuyas tres mediciones
> clave reprodujo el orquestador con sus propios comandos** antes de emitir este contrato:
> volumen real en 83.377/83.377 barras (0 ceros); pico de `tick_count` a las **14:30 UTC el
> 16-ene-2023** y a las **13:30 UTC el 17-jul-2023**; **381 de 1.141 días (33,4 %)** en horario
> estándar (UTC−5). Decisión del orquestador: **D10**.
>
> Estado: **PENDIENTE DE DESPACHO** (se despacha cuando el semáforo de 2 agentes tenga hueco;
> Emilio usa el PC). Modelo del agente: Sonnet 5. El orquestador re-ejecuta la aceptación.

## 1. Objetivo (qué tiene que ser verdad al terminar)

1. La ventana de sesión de una estrategia FONDEO se expresa en **hora local del mercado**
   (`America/New_York` para índices CME; `America/Chicago` para el cierre obligatorio de
   Topstep) y el motor la convierte a UTC **por vela, con `zoneinfo`**, de modo que la apertura
   RTH (09:30 ET) cae a las 13:30 UTC en verano y a las **14:30 UTC en invierno**.
2. La ventana se adjunta **según la familia**, no a las 6 por igual:
   - `SESSION_MOMENTUM`, `OPENING_RANGE_BREAKOUT`, `VWAP_REVERSION` (ancladas a sesión): RTH
     09:30-16:00 ET, `close_at_eod=True`.
   - `REVERSION_ATR`, `SQUEEZE_BREAKOUT`, `STREAK_EDGE`: ventana **Globex** completa (18:00 ET
     del día anterior → cierre obligatorio), **NO `None`**. Motivo verificado (I4 §1.1, fuente
     Topstep, cita literal: *"All positions must be closed by 3:10 PM CT every weekday"*): en
     fondeo no existe el overnight libre; lo honesto es operar la sesión completa con **flat
     obligatorio a las 15:10 America/Chicago** (`close_at_eod=True`). La propuesta del FORENSE
     de dejar `session_window=None` simularía un producto que ninguna firma verificada ofrece.
3. Todo lo anterior bajo la **regla #26**: `CURRENT_ENGINE_VERSION` pasa a **5.18.0** con entrada
   de changelog en `services/engine_version.py` (mismo estilo que 5.5.0-5.17.0), y se genera el
   **nuevo baseline** de `scripts/verificacion_f02.py` con `--out` (NUNCA sobrescribir el de
   5.17.0), con la comparación celda a celda documentada.

## 2. Territorio de escritura (y solo este)

- `services/discovery/funding_discovery.py` (`resolve_session_window`, `generate_candidate_blueprint`).
- `services/validation/engine/event_backtest_engine.py` (`_is_in_session_window`,
  `_session_start_minutes`, `_is_session_end`, `_calc_session_vwap`, `_calc_opening_range_levels`).
- `contracts/canonical_strategy.py::SessionWindow` — **solo campos ADITIVOS opcionales**
  (`market_tz`, `start_time_local`, `end_time_local`, `flat_time_local`, `flat_tz`), con
  `None` por defecto; el `canonical_hash` de un snapshot sin esos campos debe ser **bit a bit
  idéntico** al de 5.17.0 (demostrarlo con un test, patrón de 5.14.0).
- `services/engine_version.py` (bump + changelog).
- `tests/test_motor_5_18_sesiones_dst.py` (nuevo) y `tests/test_session_window_*.py` si hacen falta.
- `orchestration/results/verificacion_f02_5.18.0.json` (nuevo, vía `--out`) y
  `orchestration/results/W29_motor_5_18_informe.md` (tu informe).

Prohibido: tocar `scripts/mine.py`, cualquier gate, `services/api/`, datasets, y el baseline
`verificacion_f02_5.17.0.json`. Si necesitas algo fuera, lo pides en `peticiones_al_orquestador`.

## 3. Requisitos de diseño (no negociables)

- **Retrocompatibilidad**: un `SessionWindow` con solo `start_time_utc`/`end_time_utc` (los de
  hoy) se sigue interpretando exactamente igual que en 5.17.0. La conversión por zona horaria
  solo se activa cuando `market_tz` está informado.
- **Valores por producto**: los defaults de `resolve_session_window` se convierten a su
  equivalente local **de verano** (los actuales se derivaron asumiendo EDT): CME índices
  "13:30-20:00 UTC" → "09:30-16:00 America/New_York". Las demás ramas (la de "07:00-20:00" y la
  24/7) se dejan como están **a menos que** documentes con evidencia a qué producto sirven y cuál
  es su hora local real; si no lo puedes verificar, no las toques y dilo.
- **Cierre obligatorio** (`flat_time_local="15:10"`, `flat_tz="America/Chicago"`) para toda
  estrategia FONDEO de producto CME, independientemente de la familia. Es la regla de Topstep
  (única verificada junto con TradeDay); MFFU/Apex/TPT/Tradeify quedan `NO VERIFICABLE` en I4 y
  se aplica la conservadora. Cuando `PROP_FIRM_CATALOG` v2 (carril FONDEO) exponga
  `flat_time` por firma, el examen F07 podrá sobrescribirlo; hoy no.
- **Nada de tablas de DST propias**: `zoneinfo.ZoneInfo`, resuelto por la fecha de cada vela.
- **Fail-closed**: si `market_tz` no es una zona válida ⇒ excepción explícita, nunca "UTC por
  defecto".
- **Anti-lookahead**: nada de lo anterior puede usar información de la vela `i` para decidir
  la sesión de la vela `i` de forma distinta a como ya lo hace 5.17.0 (misma vela, mismo `dt`).

## 4. Aceptación (el orquestador la re-ejecuta literalmente)

1. `./.venv/Scripts/python.exe -m pytest -q tests/test_motor_5_18_sesiones_dst.py` verde, con
   al menos estos casos: (a) 16-ene-2023 09:30 ET ⇒ 14:30 UTC dentro de sesión y 13:30 UTC
   fuera; (b) 17-jul-2023 09:30 ET ⇒ 13:30 UTC dentro; (c) snapshot sin campos nuevos ⇒
   `canonical_hash` idéntico al de 5.17.0 (valor fijado en el test); (d) `market_tz` inválido ⇒
   excepción; (e) familia A/B/D recibe ventana Globex + flat 15:10 CT; familia C/ORB/VWAP recibe
   RTH.
2. `grep -n "CURRENT_ENGINE_VERSION" services/engine_version.py` ⇒ `"5.18.0"`.
3. `./.venv/Scripts/python.exe scripts/verificacion_f02.py --out orchestration/results/verificacion_f02_5.18.0.json`
   termina con exit 0 y 15 celdas OK (ninguna `SIN DATOS`). El baseline 5.17.0 conserva su
   sha256 `c1c3a7bbff230922302d8ff42d47cf73e58ff2a912a97fa685198e714ffe15c8`.
4. Comparación 5.17.0 → 5.18.0 en tu informe: las **9 celdas ULTRA idénticas** (ledger SHA-256
   igual; no tienen `session_window`). Para las **6 celdas FONDEO** (ES 4h ×3, GC 4h ×3): tabla
   celda a celda con `trades`, `PF`, `net_profit` antes/después y **la explicación mecánica de
   cada diferencia** (qué velas entran/salen de sesión por el desplazamiento de invierno, qué
   cierres EOD se mueven). Una celda FONDEO idéntica también se explica (p. ej. barras de 4h que
   no cruzan la frontera). Si alguna celda ULTRA cambia: **PARA y repórtalo**, no lo justifiques.
5. `git status --short` no muestra cambios fuera del territorio de §2.
6. Tu informe declara sin adornos lo que no pudiste verificar (`no_pude`).

## 5. Consecuencias que el orquestador asume (no son trabajo tuyo)

- Toda campaña FONDEO corrida con 5.17.0 (E1 ES 5m, E2 ES 15m) queda etiquetada "sesión sin
  DST" y se **repite** con 5.18.0 (E2b) antes de afirmar nada sobre las familias ancladas a
  sesión. Las conclusiones de `forense_telemetria_2026-09-01.md` §6.b sobre coste/ATR no
  dependen de la sesión y siguen en pie.
- 0 certificadas afectadas (no hay ninguna).
