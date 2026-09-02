# DONE_B04

- Agente: `Claude Code (orquestador)` · Rama: `main` · Inicio: `2026-09-02T18:51:00Z` (arranque de
  la re-ejecución de determinismo del paso 3, lanzada por el orquestador en el VPS bajo
  `gobernanza_recursos`) · Fin: `2026-09-02T19:32:20Z`
- Informe: `orchestration/results/agy/B04.md`
- Ficheros tocados (debe coincidir con `git diff --name-only`; ver nota de discrepancia abajo):
  - `orchestration/results/agy/B04_leer_embudos.py` (nuevo, script de lectura efímero, TERRITORIO)
  - `orchestration/results/agy/B04.md` (nuevo, informe, TERRITORIO)
  - `orchestration/agy/DONE_B04.md` (nuevo, este fichero, TERRITORIO)
  - `orchestration/results/telemetria/embudo_FONDEO_ES_15m_reversion_20260902T185231Z.json`
    (nuevo; generado por la re-ejecución de determinismo del paso 3, TERRITORIO — telemetría de
    la re-ejecución únicamente)
  - Nota: `git diff --name-only` da **vacío** (los 4 ficheros de arriba son nuevos/*untracked*,
    no aparecen en `git diff` sin `--cached`; verificado en §8 de B04.md). `git status
    --porcelain` sí muestra 4 ficheros modificados (`apps/web/app/page.tsx`,
    `apps/web/context/AuthContext.tsx`, `apps/web/lib/firebase.ts`,
    `services/api/app/api/discovery_router.py`) y 2 ficheros nuevos de la tarea `B03`
    (`orchestration/results/agy/B03.md`, `orchestration/agy/DONE_B03.md`) — ninguno de los 6
    fue tocado por esta tarea; ya estaban en el árbol de trabajo antes de empezar (confirmado
    con `git status --porcelain` al inicio y al final, sin cambios en esos 6 ficheros entre
    ambas lecturas).
- Aceptación ejecutada por el agente: `PASA` (la salida cruda íntegra de los 4 comandos de
  `GO_B04.md` está en §8 de `orchestration/results/agy/B04.md`):
  - `"$PY" orchestration/results/agy/B04_leer_embudos.py; echo "rc=$?"` → tabla por los 5
    embudos, `ANOMALIAS=0`, `rc=0`.
  - `grep -cE "D15 (CONFIRMADA|REFUTADA)" orchestration/results/agy/B04.md` → `1`.
  - `grep -cE "AGOTADA|SIGUE|NEAR-MISS" orchestration/results/agy/B04.md` → `22` (≥2).
  - `git diff --name-only` → vacío.
- Veredicto: **D15 CONFIRMADA** (perfil `reversion`, E1: 0/20 configs con `pf_bruto>=1,00` en
  5m y en 15m, determinismo confirmado PC-vs-VPS, umbrales de `mine.py` sin cambios desde el
  31-08). Con la salvedad, no aplicable a D15 en sí pero sí a su extensión a E2 (perfil
  `arquetipos`): `SESSION_MOMENTUM` en ES 5m tiene ventaja bruta real (20/72 configs con
  `pf_bruto>=1,05`) que muere en IS mayoritariamente por coste, sobre un motor que cobra a MES
  4,17× su comisión real ya documentada en el propio proyecto (`instrument_registry.py`) —
  hallazgo de código verificado en `event_backtest_engine.py:296,302,970-972` y
  `scripts/mine.py:1039`. Por celda E2: 5m AGOTADA, 15m AGOTADA (regla literal, 6/6 familias,
  100% `sin_ventaja`); por familia: 11 de 12 combinaciones celda×familia AGOTADA en sentido
  sustantivo (`sin_ventaja_bruta` domina), salvo `SESSION_MOMENTUM` 5m = SIGUE (edge bruto real
  matado por coste). 0 near-miss en las 12 combinaciones (ningún registro de E2 alcanza
  VAL/OOS/gates).
- Lo que NO se pudo hacer y por qué (`NO DATA` donde corresponda):
  - Recalcular `pf_bruto` "a mano desde el ledger de operaciones" del motor: **NO DATA**.
    Comprobado sobre los 883 registros de los 5 embudos (E1×2, E2×2, rerun): ninguno trae la
    lista de operaciones (`trades`) que el motor genera internamente; la telemetría solo
    persiste los agregados de `_pf_bruto_y_coste()`. Se reconcilió en su lugar contra esos
    agregados (0 discrepancias, §2 de B04.md).
  - Confirmar con un caso real que W2.8 (`is_pf` para quien supera IS) funciona: **NO DATA**.
    Los 5 embudos tienen `embudo_por_etapa={'IS': N}`: nadie supera IS, así que la ausencia de
    `is_pf` en los registros de IS es coherente con W2.8 pero no la prueba positivamente (§3bis).
  - Cuantificar el efecto real de corregir el bug de comisión de MES sobre `pf_neto`: **NO DATA
    de medición directa** (re-ejecutar el motor con la comisión corregida está fuera del
    territorio y de lo permitido en este encargo); se dejó como estimación razonada con la cifra
    medida del coste actual (§2/§6 de B04.md), no como medición.
  - Levantar por escrito la suspensión D1 en `PLAN_LOCAL_FONDEO.md`: fuera del TERRITORIO de esta
    tarea (solo lectura de ese fichero); se documenta el hueco de proceso en §6 de B04.md
    (hallazgo S3 #3) para que el orquestador lo cierre por separado.
- Confirmo: sin `git` de escritura · sin `rm` · sin datos inventados · nada fuera del territorio.
