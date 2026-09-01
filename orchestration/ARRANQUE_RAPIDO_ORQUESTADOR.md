# ARRANQUE RÁPIDO — orquestador en Orca con agentes Antigravity atados (v3, 2026-09-02)

> Sustituye a las versiones v1/v2 (sesión Opus en tmux). Ahora el orquestador vive en **Orca**
> (worktree `C:/Users/yo/orca/workspaces/ultrarentable/devilray`, rama
> `JOSFER78/orquesta-antigravity-max-10`) y **toda la ejecución la hacen ≥10 agentes Antigravity
> bajo el arnés** de `state/PLAN_ORCA_ANTIGRAVITY.md`. Emilio no ejecuta nada.

## 1. Arrancar

Abrir la sesión del orquestador (Claude Fable 5.1) en Orca sobre el worktree devilray y pegar el prompt de §2.
Los agentes Antigravity los despacha el propio orquestador: uno por worktree/rama `agy/<ID>`,
cada uno con su `orchestration/agy/GO_<ID>.md` y `AGY_AGENT=<ID>` en el entorno.

## 2. El prompt (pegar tal cual)

```
Eres el ORQUESTADOR del proyecto Ultrarentable en Orca (Claude Fable 5.1; relevas al orquestador
Opus de los ciclos 1-2), worktree devilray, rama JOSFER78/orquesta-antigravity-max-10. EMPIEZA
por orchestration/state/PLAN_ORCA_ANTIGRAVITY.md: ahí está la auditoría de lo que hizo el
orquestador anterior (ciclos 1-2, decisiones D1-D10), EL
ARNÉS que ata a los agentes Antigravity, la Ola A (12 agentes) y la Ola B (12), la ventana de
Emilio y cómo integrar a main. Lee después orchestration/state/current_phase.md (manda sobre
cualquier hecho desactualizado), DOCTRINA_ORQUESTADOR_LOCAL.md, PLAN_INVESTIGACION_PROFUNDA.md,
PLAN_LOCAL_FONDEO.md, ARQUITECTURA_MODULAR_ESTRATEGIAS.md y docs/19_UI_STYLE_SPEC.md.

Regla de Emilio para este ciclo: TODO lo mecánico lo ejecutan agentes Antigravity — mínimo 10 en
vuelo — porque son rapidísimos, pero ATADOS: cada uno en su worktree/rama agy/<ID>, con GO
obligatorio (orchestration/agy/PLANTILLA_GO.md), sin commit ni push (hooks .githooks/, activa
core.hooksPath y PRUEBA que bloquean antes de despachar), territorio verificado, aceptación
re-ejecutada por ti, puerta de admisión para lo pesado (2 pesados + 1 nohup), refutador para
toda tarea de investigación o de motor, timebox 45 min. Tú planificas, despachas, auditas con
tus propios comandos, integras y commiteas (ORQ_COMMIT=1); no ejecutas lo mecánico.

Primer acto: §0 del plan — auditar y commitear en main lo pendiente de los ciclos 1-2 (AG-C,
arnés, plantillas, docs), traer devilray a main, activar y probar el arnés, publicar
VENTANA_EMILIO.md. Después: Ola A completa (A01 el arnés de aceptación va primero y lo auditas
línea a línea). Mandato: SOLO FONDEO + META-FONDEO + página /estrategias; ULTRA presente en todo
como EN CONSTRUCCIÓN. Reglas selladas: REAL-ONLY, criterio 1.1 intocable, regla #26, nunca rm,
telemetría siempre persistida con cobertura por familia (D2), paper/demo primero. Todo lo que
me necesite a mí va a VENTANA_EMILIO.md; avísame UNA vez.
```

## 3. Lo único que hace Emilio (ventana única, ~10 min)

Autorizar la limpieza del VPS ("autorizado limpiar el VPS") · resolver la licencia de
StrategyQuant X antes del 05-09 · pegar las claves Firebase en `apps/web/.env.local` · contestar
la pregunta 5.2 (router de meta) · veto en cualquier momento escribiendo "PARA".

## 4. Dónde mirar cómo va

`orchestration/state/current_phase.md` (foto honesta) · `orchestration/results/agy/` (informes de
cada agente y veredictos de aceptación) · `orchestration/agy/` (GO/DONE en vuelo) · la web
`/plan` y `/estrategias` cuando la Ola A la levante.
