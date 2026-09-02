# GO_B23 — Motor 5.19.0: comisión por contrato del símbolo de EJECUCIÓN (MES 0,60, no ES 2,50)

> Contrato de ejecución. El agente lo lee entero, ejecuta SOLO lo que dice, y termina escribiendo
> `orchestration/agy/DONE_B23.md` + informe en `orchestration/results/agy/B23.md`. El orquestador
> (sesión Claude Code `ultrarentablepc-e2`) re-ejecuta la aceptación él mismo antes de firmar.

## Identidad
- ID: `B23` · Ola: `B` · Rama: trabajo directo en el checkout principal (`main`, sin commit) · Timebox: 60 min
- Máquina: PC de Emilio (en uso: **1 solo proceso pesado a la vez**, ver RIESGO)
- Python: `.venv/Scripts/python.exe` (el `python` del PATH está roto)

## OBJETIVO (una frase verificable)
Con motor `5.19.0`, un backtest de una estrategia cuyo `strategy.symbol` es `MES` paga **0,60 USD por
contrato y por lado** (lo que dice `services/engine/instrument_registry.py`), y uno con `ES` sigue pagando
2,50; queda demostrado con un test unitario, la versión del motor sube por regla #26 y el baseline F02 de
5.19.0 existe con su diff explicado frente a 5.18.0.

## CONTEXTO (hallazgo de B04, verificado por el orquestador en el código; no hace falta re-demostrarlo)
- `services/validation/engine/event_backtest_engine.py:296` → `cme_fee_per_contract_usd: float = 2.50`
  (default del constructor); `:302` → `self.cme_fee = ...`; `:970-972` → `_comision()` devuelve
  `self.cme_fee * qty` para TODO futuro, sin mirar el símbolo.
- `event_backtest_engine.py:835-877` ya resuelve la spec real del símbolo (`_spec = InstrumentRegistry.get(strategy.symbol)`)
  para `point_value` y `es_futuro` (fail-closed con `es_spec_verificada`). Ahí mismo hay que sacar la comisión.
- `services/engine/instrument_registry.py:78-95`: `ES/NQ/YM/GC/...` cme_fee 2.50; `MES/MNQ/MYM/M2K/MGC/MCL` 0.60.
- `scripts/mine.py:103-110` (`FONDEO_MICRO_MAP`) y `:1078-1085`: desde el 31-08 el snapshot de FONDEO lleva
  `symbol=exec_symbol` (el MICRO). Por eso, al leer la comisión de la spec del símbolo, la corrección aplica
  sola a toda campaña FONDEO. `scripts/mine.py:1039` instancia `EventBacktestEngine()` sin argumentos.
- Sobrecoste actual: 3,80 USD por operación y contrato en MES. En E2 (ES 5m) SESSION_MOMENTUM tenía 20/72
  configuraciones con PF bruto 1,053-1,114 hundidas a 0,97-1,03 neto por la fricción.
- Issue de seguimiento: #38 del repo (JOSFER78/ultrarentable). Plan: `orchestration/state/plan/bloques/F03_campana_descubrimiento.md`
  (actualización 2026-09-02 19:55).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera de aquí, solo lectura)
- `services/validation/engine/event_backtest_engine.py`
- `services/engine_version.py` (este GO lo ORDENA: bump a 5.19.0)
- `tests/test_event_backtest_comision_por_simbolo.py` (nuevo)
- `orchestration/results/verificacion_f02_5.19.0.json` (lo escribe el script F02)
- `orchestration/results/verificacion_f02_diff_5.18.0_vs_5.19.0.md` (lo escribe el script F02)
- `orchestration/results/agy/B23.md` (informe) y `orchestration/agy/DONE_B23.md`

## ENTRADAS (leer antes de tocar nada)
- `services/validation/engine/event_backtest_engine.py` líneas 285-310, 815-880, 955-985, 1290-1310.
- `services/engine/instrument_registry.py` líneas 60-110 (dataclass de la spec: nombre exacto del campo de comisión y `asset_class`).
- `services/engine_version.py` entero (formato de `VERSION_HISTORY`, `CURRENT_ENGINE_NAME`, `ENGINE_RELEASE_DATE`).
- `scripts/verificacion_f02.py` entero (qué celdas corre, cómo compara, `--out/--force`).
- `orchestration/results/verificacion_f02_diff_5.17.0_vs_5.18.0.md` (formato del diff anterior).
- `tests/test_event_backtest_deterministic.py` (estilo de test y cómo construyen un snapshot/dataset mínimo).
- `grep -rn "cme_fee_per_contract_usd\|cme_fee" services scripts tests` → listar TODOS los usos en el informe.

## TRABAJO
1. **Motor**: en el bloque donde se resuelve `_spec` (≈`:851`), leer la comisión por contrato de la spec del
   símbolo (`cme_fee` o como se llame en la dataclass; comprobarlo). Regla: para `es_futuro` (asset_class
   CME_FUTURES) **la comisión sale de la spec**; si la spec no trae comisión > 0 → **fail-closed**
   (`ValueError("NO DATA: ... sin comisión por contrato verificada")`), nunca un default silencioso.
   `_comision()` usa esa comisión por contrato. El parámetro del constructor `cme_fee_per_contract_usd`
   se conserva por compatibilidad de firma y deja de decidir la comisión de futuros CME (documentarlo en
   el docstring). Ningún otro cambio semántico. Cripto (`taker_fee`) intacto.
2. **Test** `tests/test_event_backtest_comision_por_simbolo.py`: con datos reales mínimos (mismo mecanismo que
   `test_event_backtest_deterministic.py`; PROHIBIDO inventar velas sintéticas si ese test no lo hace),
   demostrar que (a) con `symbol="MES"` la comisión cobrada por contrato y lado es 0,60, (b) con `ES` es 2,50,
   (c) el ledger de MES cambia respecto a la comisión antigua exactamente en `(2,50-0,60) × 2 lados × contratos`
   por operación (o la aserción equivalente que el ledger permita), (d) un símbolo CME sin comisión en la spec
   falla cerrado. Ejecutar SOLO: `.venv/Scripts/python.exe -m pytest tests/test_event_backtest_comision_por_simbolo.py tests/test_event_backtest_deterministic.py tests/test_canonical_backtest_and_bundle.py -q`.
   NUNCA `pytest tests/` entero.
3. **Regla #26**: `CURRENT_ENGINE_VERSION = "5.19.0"`, `CURRENT_ENGINE_NAME` nuevo, `ENGINE_RELEASE_DATE = "2026-09-02"`,
   entrada nueva al principio de `VERSION_HISTORY` (la de 5.18.0 pasa a `status` no vigente como hicieron las
   anteriores; copiar el patrón exacto del fichero). Cambios en llano y exactos (qué, dónde, cuánto).
4. **Baseline F02** (PESADO → puerta de admisión): primero `.venv/Scripts/python.exe -m services.ops.gobernanza_recursos estado`;
   luego `.venv/Scripts/python.exe -m services.ops.gobernanza_recursos ejecutar --nombre B23 -- .venv/Scripts/python.exe scripts/verificacion_f02.py`
   (si el subcomando `ejecutar` no existe en esta versión del módulo, pegar la ayuda del módulo en el informe y
   ejecutar el script directamente SOLO si `estado` dice que se puede). Después
   `.venv/Scripts/python.exe scripts/verificacion_f02.py --comparar 5.18.0 5.19.0`.
   Expectativa razonada (NO es el resultado; el resultado es lo que salga): las celdas F02 usan `ES` y `GC`
   (contrato completo, 2,50) y cripto, así que lo esperable es 15/15 idénticas; **si alguna celda cambia, explicar
   celda a celda por qué** y no maquillar nada. Si sale idéntico, decirlo y explicar por qué eso NO demuestra la
   corrección (la demuestra el test con MES) — sin inventar una celda MES nueva en F02 (fuera de territorio).

## ACEPTACIÓN (comandos exactos; el orquestador los re-ejecuta él mismo)
```bash
.venv/Scripts/python.exe -m pytest tests/test_event_backtest_comision_por_simbolo.py tests/test_event_backtest_deterministic.py tests/test_canonical_backtest_and_bundle.py -q   # todo passed
grep -n 'CURRENT_ENGINE_VERSION: str = "5.19.0"' services/engine_version.py                          # 1 línea
grep -n "cme_fee" services/validation/engine/event_backtest_engine.py                                # la comisión de futuros sale de la spec
ls orchestration/results/verificacion_f02_5.19.0.json orchestration/results/verificacion_f02_diff_5.18.0_vs_5.19.0.md
git diff --name-only ; git status --short --untracked-files=all | grep '^??'   # todo dentro de TERRITORIO
```

## RIESGO Y REGLAS ESPECÍFICAS
- Toca semántica del motor: **SÍ** → bump + baseline F02 + diff (este GO). No relajar ningún umbral.
- Ejecuta algo pesado: **SÍ** (F02) → SOLO vía `gobernanza_recursos` como en el punto 4. El PC lo está usando
  Emilio y otra tarea (build de la web) puede estar corriendo: si `estado` dice NO, esperar 2 minutos y reintentar
  hasta 5 veces; si sigue NO, informar y dejar F02 pendiente (no forzar).
- Prohibido `git add/commit/push/checkout/reset/stash`; prohibido `rm`; prohibido tocar `scripts/mine.py`,
  `instrument_registry.py`, `apps/web/**` o cualquier fichero fuera del TERRITORIO.
- Ficheros con CRLF: conservar el final de línea que tenga cada fichero.

## SALIDA
1. Working tree con los cambios (sin commit).
2. `orchestration/results/agy/B23.md`: comandos ejecutados y salida CRUDA pegada (pytest, grep, F02, comparar),
   lista de todos los usos de `cme_fee` encontrados, lo que no se pudo, veredicto propio en una frase.
3. `orchestration/agy/DONE_B23.md` (plantilla `PLANTILLA_DONE.md`).
