# FASE ACTUAL — F03 AMPLIACIÓN DE DATOS + F02.2 PENDIENTE (plan v4 por bloques)

> Actualización 2026-08-31 ~13:30 UTC: F00 C–G ejecutadas (cuarentenas con manifiesto, bug
> `gates_passed` corregido); F01 censo HECHO (0 supervivientes de 728, re-barrido idempotente);
> F02.1 HECHO (motor 5.6.0→5.11.0, cinco releases verificadas, pytest en línea base 28);
> F03 tramo cripto 4h/1h COMPLETADO: 18 celdas, ~36k configs, **0 certificadas** — diagnóstico:
> muestra OOS insuficiente a 4h/1h; la ampliación es de DATOS (backfill profundo Binance 15m/5m
> lanzado; Dukascopy TRADFI en curso). En vuelo: captura fricción BingX (F02.2) e inventario
> DB_PATH (F00 Fase I-5).

# (histórico de la mañana, sigue abajo)

> Plan: `state/plan_maestro.md` (índice) + `state/plan/bloques/` (un fichero por fase, fuente de
> verdad de cada una). Doctrina: `DOCTRINA_ORQUESTADOR.md §14 y §15`.
> El anterior `current_phase.md` (Fase 2 de la v3, metodología Antigravity) está archivado en
> `state/archive/current_phase_2026-08-31_v3_fase2_ingesta.md`. Antigravity está fuera del camino
> crítico.

## Qué está pasando ahora (2026-08-31)

- **F00 Limpieza — EN_CURSO.** Auditoría read-only con verificación adversarial de las subfases
  0.1–0.4 (árboles de validación duplicados, servicios muertos, BD canónica, entrada de minería).
  Los movimientos a `cuarentena/` se ejecutan solo con claims CONFIRMADOS y manifiesto SHA-256.
- **F00.5 — RESUELTO:** `ultrarentable-discovery.service` detenido con éxito (estado: `inactive`).
- **F03.1 Datos — EN_CURSO en paralelo:** backfill Dukascopy + M1 cripto. `USARUSSIDXUSD` (RTY)
  sigue SIN VERIFICAR.
- **F01 Censo — HECHO (2026-08-31):** regla #26 aplicada (120 filas 5.5.0 → legacy con
  auditoría), censo 1.1 con **0 supervivientes de 728**, gobernanza de versiones sincronizada a
  5.6.0 (SSOT + manifiesto + tests 11/11 verdes). Informe: `orchestration/results/censo_f01.md`.
  Herramientas nuevas: `scripts/gobernanza_regla26.py`, `scripts/censo_f01.py`.
- **Siguiente al cerrar F00:** F02 fricción medida en el motor (spread por barra, ejecución
  asimétrica, latencia, funding/liquidación ULTRA, trailing DD intradía FONDEO) y F03.2 cola de
  minería gobernada.

## Reglas de esta fase

1. CERO `git commit` / `git push` — todo queda en el working tree para revisión del usuario.
2. CERO `rm` — todo a `cuarentena/` con manifiesto SHA-256.
3. Ningún movimiento sin verificación adversarial previa (un claim REFUTADO no se ejecuta).
4. `pytest` no puede empeorar respecto al estado previo a cada movimiento.
