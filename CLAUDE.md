# ULTRARENTABLE — contexto para Claude (cualquier sesión/IDE)

Trading algorítmico dual-track: **ULTRA** (perpetuos cripto BingX, convexidad con balas 1R) y
**FONDEO** (futuros CME para prop firms). Ejecuta Hermes (orquestador Claude) con subagentes
en paralelo; Antigravity está retirado del proyecto (2026-08-31).

## Estado del proyecto — LEER PRIMERO

1. `orchestration/state/current_phase.md` — foto actual + nota de pausa/reanudación.
2. `orchestration/state/plan_maestro.md` — índice del plan v4 con la tabla de fases.
3. `orchestration/state/plan/bloques/Fxx_*.md` — fuente de verdad de cada fase (frontmatter
   YAML con estado). Al avanzar una fase: editar SU bloque y reflejar la fila del índice.
   Nunca reescribir el plan entero ni crear planes paralelos; lo sustituido va a
   `orchestration/state/archive/`.

## Reglas invariantes (selladas; detalle en plan/bloques/REGLAS_INVARIANTES.md)

- **REAL-ONLY / zero-mocks**: nada sintético; evidencia en disco con SHA-256.
- **Criterio 1.1 SELLADO** (no se relaja): ≥200 trades OOS, PF OOS ≥1.25, OOS/IS ≥0.5,
  11 gates con evidencia, DSR+, persistencia por mitades OOS.
- **Regla #26**: todo cambio que altere operaciones del motor sube `CURRENT_ENGINE_VERSION`
  (SSOT: `services/engine_version.py`); certificaciones con motor viejo → LEGACY, nunca borrar.
  Gobernanza: `scripts/gobernanza_regla26.py`.
- **Nunca `rm`**: todo a `cuarentena/` con manifiesto SHA-256.
- **Git**: push a main AUTORIZADO expresamente por Emilio para este repo — commits temáticos
  descriptivos con trailer de Claude, nunca árboles incoherentes (releases a medias).
- **Carga del VPS (4 cores)**: no simultanear procesos pesados; `nice -n 19` / `ionice -c 3`;
  la web SIEMPRE en build de producción, no `next dev`. Ojo: `ultrarentable-discovery.service`
  y `sqx.service` resucitan tras reinicio (enabled) y saturan la máquina.
- **Multiagentes**: subagentes simultáneos para lo mecánico; el orquestador analiza, decide
  y verifica.

## SSOT técnicos

- Motor de backtest: `services/validation/engine/event_backtest_engine.py`
  (versión en `services/engine_version.py`; verificación entre versiones:
  `scripts/verificacion_f02.py --comparar A B` → 15 celdas de referencia).
- BD canónica: `services/api/app/config.py::STATE_DB_PATH` (fuera del repo).
- Minería gobernada: `scripts/cola_mineria.py` (encolar/trabajar/estado/cancelar) sobre
  `services/queue/durable_job_queue.py`. NO usar pipelines de discovery directos.
- Datasets: `data/normalized/*.json` + manifiesto (conteo válido = en disco, no la BD).
- Fricción BingX: `data/registry/bingx_friction.json` (¡unidades mixtas documentadas dentro!).

## Servicios locales

- Web (Next.js): `apps/web` → `npm run build && npm run start -- -p 3000` (producción).
- API FastAPI: `:8000` (systemd `ultrarentable-api.service`).
- SQX headless: `:5050` (`sqx.service`); cliente `services/sqx_bridge/sqx_client.py`
  (fire-and-verify: los timeouts HTTP no cancelan la operación en SQX).

## Comunicación

Responder a Emilio en español, directo y orientado a la acción: qué se hizo y cómo verificarlo.
