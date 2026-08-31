# FASE ACTUAL — BALANCE 2026-08-31 ~18:45 UTC (plan v4 por bloques)

> **PAUSA ORDENADA (18:50 UTC).** Cómo retomar en la próxima sesión:
> 1. La release **5.14.0 ya está en el árbol** (motor pineado, manifest y test de gobernanza
>    actualizados, fix del lookahead del TP de reversion_atr aplicado en
>    `event_backtest_engine.py:879`). Al pausar estaba corriendo la verificación de identidad
>    (`.venv/bin/python scripts/verificacion_f02.py`); si no dejó JSON de 5.14.0 en
>    `orchestration/results/`, re-ejecutarla y comparar con 5.13.0 (`--comparar`): las 15
>    celdas deben salir IDÉNTICAS. Falta también el smoke de las 4 familias
>    (`orchestration/results/smoke_arquetipos_5_14_0.md` aún no existe).
> 2. Con identidad + smoke verdes: commit temático de la 5.14.0, reword de los mensajes
>    "wer"/"werwe" (aún no publicados), `git merge -s ours origin/main` (análisis hecho: cero
>    contenido único en origin; push ~307 MB, ningún blob >100 MB) y **push a main**.
> 3. Después: re-campaña perfil `arquetipos` (encolar + trabajar), censo 1.1.
> Servicios: API :8000 activa; web Next.js lanzada en dev en :3000; sqx.service activo.

> Fuente de verdad por fase: `state/plan/bloques/Fxx_*.md`. Índice: `state/plan_maestro.md`.
> Ejecución: Hermes (orquestador) + subagentes de Claude, EN PARALELO. **Antigravity queda
> retirado del todo (orden expresa 2026-08-31): no se espera ni se integra nada suyo.**

## HECHO (hoy, con evidencia)

| Qué | Evidencia |
| :--- | :--- |
| F00 limpieza C–G + DB_PATH unificado (SSOT `services/api/app/config.py::STATE_DB_PATH`) | `cuarentena/*/MANIFEST*`, bloque F00 |
| F01 censo criterio 1.1: **0 supervivientes de 728**; regla #26 aplicada | `orchestration/results/censo_f01.md` |
| F02.1 motor honesto **5.7.0 → 5.13.0** (spread medido, comisión por lado, latencia next-bar-open, riesgo=FRACCIÓN, point_value, spread+funding reales BingX) | `orchestration/results/verificacion_f02_diff_*.md` (ledger a ledger) |
| F03.1 backfill profundo Binance **COMPLETADO**: 18 datasets 15m/5m desde 2021, 0 gaps | `data/binance_backfill_profundo.log` + manifiestos |
| F03.2 cola gobernada con heartbeat, anti-duplicados y `cancelar --motivo` | `scripts/cola_mineria.py`; cola: 20 COMPLETED / 7 CANCELLED |
| F03.3 campañas honestas 4h/1h (18 celdas, ~36k configs) y 15m profundo: **0 certificadas** → diagnóstico: familia EMA/RSI/Donchian agotada | bloque F03; `orchestration/results/cola_mineria.jsonl` |
| Diseño 5.14.0 sellado (4 familias nuevas de arquetipos) e implementación de señales en HEAD | `orchestration/reviews/diseno_arquetipos_5_14.md` |
| QA del orquestador sobre 5.14.0: entradas de las 4 familias causales y de evento correcto; 1 defecto hallado (lookahead en TP dinámico de reversion_atr) y pasado al agente que cierra la release | este documento; fix en curso |
| SQX: 2.035 .sqx de ToImprove materializados a disco + **export CSV de métricas HECHO** (2.035 filas, 44 columnas) | `data/sqx_exports/toimprove_2026-08-31.csv` |
| Registro de fricción BingX (9 pares, spread+funding, capturado 13:43Z) | `data/registry/bingx_friction.json` |

## EN VUELO (subagentes en paralelo, ahora mismo)

1. **Cierre release 5.14.0** (agente): fix del TP dinámico + bump `CURRENT_ENGINE_VERSION`
   5.13.0→5.14.0 + VERSION_HISTORY + pin de tests + verificación de identidad 5.13.0→5.14.0
   (15 celdas IDÉNTICAS = aceptación) + smoke real de las 4 familias.
2. **Análisis divergencia git** (agente read-only): main local ahead 8 / behind 2 de
   `origin/main`; los 2 de atrás son commits viejos de Antigravity deshechos en local.
   Verifica que descartar su contenido no pierde nada y estima el tamaño del push
   (datasets ~1 GB en `data/normalized/`, ningún blob puede superar 100 MB).
3. **Backfill Dukascopy** (nohup externo): solo `USA500IDXUSD` avanza (~1.155 .bi5);
   los otros 6 proxies + forex siguen a cero. Días de descarga. FONDEO bloqueado hasta esto.

Coordinación: hay una segunda sesión de Claude (01-ultrarentable-9a) en el repo, avisada y en
espera; los commits `60fd76bf8 "werwe"` y `5fcfea9ce` los hizo el usuario u otra vía (la
identidad git "Hermes User" es compartida). Reparto: esta sesión lleva 5.14.0, push,
re-campaña y SQX.

## PENDIENTE (en orden, camino crítico al goal ULTRA / ULTRA-meta / FONDEO / FONDEO-meta)

1. **Aterrizar 5.14.0** (identidad + smoke verdes) → commit temático + reconciliar divergencia
   con origin y **push a main** (autorizado expresamente; commits temáticos, nunca releases a
   medias).
2. **Re-campaña perfil `arquetipos`**: cripto 15m + 4h con datos profundos (encolar + trabajar
   con la cola gobernada, concurrencia 2).
3. **Censo criterio 1.1** sobre el resultado (sin relajar NADA). Si hay supervivientes →
   F04 (mejora inteligente) → F05 (envolvente ULTRA) → F06 (meta-router) = ULTRA y ULTRA-meta.
4. **Carril SQX**: cruzar el CSV de métricas con los 2.035 .sqx; parser AST → validación con
   motor propio (11 gates). Materia prima adicional para F04.
5. **FONDEO**: espera backfill Dukascopy verificado → campaña TRADFI → F07 exámenes prop =
   FONDEO y FONDEO-meta. Antes: F02.3 (trailing DD intradía, reglas prop).
6. F02.2 restante: cap apalancamiento real BingX (bloqueado: requiere API key del usuario) y
   liquidación con margen aislado.
7. Fase I restantes de F00: unificación 0.4 (entradas de minería) y 0.6 (dos motores de
   backtest); fusión learning_store (F04).

## Reglas vigentes

1. Git: push a main **autorizado** (2026-08-31) — commits temáticos descriptivos; decidir con
   criterio los artefactos pesados; nunca subir árboles incoherentes.
2. CERO `rm` — todo a `cuarentena/` con manifiesto SHA-256.
3. REAL-ONLY: cero mocks, cero datos sintéticos; criterio 1.1 SELLADO (no se relaja).
4. Regla #26: todo cambio que altere operaciones sube versión de motor; nada se borra.
5. Multiagentes simultáneos para lo mecánico; el orquestador analiza, investiga y prueba.
