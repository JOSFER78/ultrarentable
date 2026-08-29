# DECISIONES_LOG.md — registro append-only (nunca editar hacia atrás)

Formato: `## YYYY-MM-DD HH:MM — D<N>: <decisión> — contexto, alternativas, quién`.

---

## 2026-08-29 16:35 — D1: Se crea la carpeta documental `estrategias_um/` y se migra toda la evidencia desde /tmp
**Contexto:** un día de investigación intensiva dejó informes en /tmp (volátil) y ORDENAR. Mandato del usuario: dejar todo organizado y permanente en la carpeta del proyecto.
**Decisión:** estructura según diseño del escribano (docs/ de verdad, evidencia/ fechada inmutable, scripts/), dentro de `01 Ultrarentable/estrategias_um/`. Evidencia migrada con verificación diff (cfx_actual y mcprobe íntegros, 26 MB).
**Quién:** orquestador L1 (aplicando diseño del subagente ESCRIBANO).

## 2026-08-29 16:35 — D2: Pausa de experimentación; se congelan los parches del embudo hasta aprobar el plan
**Contexto:** dos parches MC aplicados hoy no curaron la mortalidad (el motor sirvió su config en memoria y nunca recargó los parches); el usuario ordenó parar de probar y planificar.
**Decisión:** cero mutaciones al motor sin plan aprobado. Los hallazgos quedan documentados: fusible = BadStrategyException (trades==0 por-sim), sospechoso residual RandomizeStartingBar, umbrales WF contradictorios (80 Build vs 65 Improve).
**Quién:** mandato directo del usuario 2026-08-29 ~15:55 UTC.

## 2026-08-29 16:35 — D3: Los archivos de idioma y el JAR plugin revelan el mecanismo del fusible — queda registrado como HECHO con evidencia
**Contexto:** rastreo del fusible "Filtro automático: sin transacciones".
**Decisión:** registro del mecanismo verificado (javap + Spanish.csv L1889 + English.csv "Automatic filter" L3367): el fusible dispara por-sim cuando el backtest de una simulación acaba con OrdersList.size()==0. No se tocará AutomaticDismissal global; la corrección será por configuración de las sims (RandomizeStartingBar y similares) en ventana de parada, tras aprobación del plan.
**Quién:** orquestador L1 + subagente detective (deleg_c54fdd7a).

## 2026-08-29 16:35 — D4: El banco legacy "Last generation" se reconoce como EL semillero real (91-93 crudas) y se declara su captura como PRIMERA acción de la FASE 1
**Contexto:** rename a medias de bancos: config.xml renombró a "LastGeneration" pero el runtime escribe en el nombre legacy con espacio; improve_cycle.sh cuenta el banco nuevo (0 eterno) → meta-ciclo muerto.
**Decisión:** capturar (copy + export CSV) el semillero legacy ANTES de cualquier recarga de config (que lo vaciaría), como primer paso de la FASE 1 del PLAN_PIPELINE.md.
**Quién:** orquestador L1 (verificado por API a las 15:31 y 16:17).

## 2026-08-29 17:10 — D5: MANDATO PERMANENTE — el sistema funciona SOLO, 24/7, con autorreparación
**Contexto:** recordatorio explícito del usuario: "recuerda que el sistema funciona solo, 24/7 con auto reparación".
**Decisión:** todo componente del pipeline (motor SQX, lazo de mejora, watchdogs, web/API) debe: (1) auto-arrancarse (systemd/cron), (2) auto-recuperarse de fallos (restart+health-check+reintento), (3) degradar con estado honesto (NO DATA/ERROR) sin colgarse, (4) requerir intervención humana SOLO para decisiones de negocio. Cualquier pieza nueva del plan se diseña con esta regla; las piezas existentes se auditan contra ella (improve_cycle sin cron, sqx_autostart sin cablear = PENDIENTES conocidas, PLAN_PIPELINE FASE 1-2).
**Quién:** usuario (verbatim), registrado por orquestador L1.

## 2026-08-29 17:45 — D6: Cirugía web /estrategias COMPLETADA y verificada punta a punta
**Contexto:** 05_WEB_EVAL.md dio veredicto PARCIAL con P0 (extracción SQX apuntando a 8080 muerto). Ejecutado con subagentes en 2 tandas (P1 estados ✓, UI-nueva ✓, build-prod ✓, P0 escribió código pero murió verificando ×2).
**Decisión y verificación REAL (por orquestador):** el backend vivo en :8000 era un proceso zombi de las 02:09 con código viejo; muerto con PID exacto (4074143) y re-arrancado (proc_556bf3b44037). Tras reinicio: databanks reales desde 5050 (10 bancos, 'Last generation'=96) y extract devuelve SUCCESS con next_step honesto. La extracción usa DATABANK='Results' hardcodeado — PENDIENTE FASE 1: apuntar al semillero correcto (o selector ya creado en UI).
**Quién:** subagentes (fix código) + orquestador L1 (verificación final y reinicio backend).
