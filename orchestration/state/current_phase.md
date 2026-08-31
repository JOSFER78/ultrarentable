# FASE ACTUAL — F03: RELEASE 5.14.0 (ARQUETIPOS) + RE-CAMPAÑA (plan v4 por bloques)

> Actualización 2026-08-31 ~18:00 UTC — camino crítico hacia el goal (estrategias reales
> ULTRA / ULTRA-meta / FONDEO / FONDEO-meta):
>
> 1. **Motor honesto COMPLETO hasta 5.13.0** (F02.1 HECHO: fricción medida, latencia next-bar,
>    riesgo en fracción canónica, spread y funding reales BingX por par). F02.2 PARCIAL
>    (falta cap de apalancamiento — bloqueado por API key — y liquidación); F02.3 pendiente.
> 2. **Evidencia de campaña:** 4h/1h (18 celdas, ~36k configs) y 15m profundo → **0 certificadas
>    11/11**: familia EMA-cross/RSI/Donchian agotada frente a fricción honesta. Detención 15m
>    con motivo registrado en la cola.
> 3. **EN VUELO AHORA:** release **5.14.0** (4 familias nuevas: reversion_atr, squeeze_breakout,
>    session_momentum, streak_edge — spec `orchestration/reviews/diseno_arquetipos_5_14.md`)
>    implementándose por subagente; aceptación = identidad 5.13.0→5.14.0 en 15 celdas.
> 4. **Al aterrizar 5.14.0:** re-campaña perfil `arquetipos` cripto 15m + 4h (datos profundos
>    desde 2021 ya en disco, 0 gaps) → censo criterio 1.1 → si hay supervivientes, F04/F05/F06
>    (ULTRA y ULTRA-meta). FONDEO/FONDEO-meta esperan backfill Dukascopy (solo USA500 avanza).
> 5. **Git:** push a main AUTORIZADO expresamente (2026-08-31); commit temático al aterrizar
>    5.14.0 para no subir una release a medias.

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

1. Git: **push a main autorizado expresamente por el usuario (2026-08-31)** — commits temáticos
   con mensajes descriptivos, nunca árboles incoherentes (releases a medias), y decisión
   explícita sobre artefactos pesados. (Sustituye a la regla anterior "CERO commit/push".)
2. CERO `rm` — todo a `cuarentena/` con manifiesto SHA-256.
3. Ningún movimiento sin verificación adversarial previa (un claim REFUTADO no se ejecuta).
4. `pytest` no puede empeorar respecto al estado previo a cada movimiento.
