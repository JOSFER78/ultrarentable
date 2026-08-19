# AGENTS.md — Ultrarentable (proyecto de trading)

> Bootstrap automático para cualquier chat/agente que se abra en este directorio.
> Léelo SIEMPRE al arrancar una sesión en este workspace.

## Qué es este proyecto
Generador de estrategias ultrarentables con **StrategyQuant X** (SQX) + pipeline de
validación multi-motor. Estado actual: se está arreglando el generador para que produzca
candidatos que pasen los gates (antes: 95 estrategias, 77 backtests, 0 aprobados).

## PUNTO DE ENTRADA OBLIGATORIO (leer primero en un chat nuevo)
1. `docs/Estado/auditoria/16_HANDOFF_ESTADO_EJECUCION.md` — estado exacto de ejecución (a medias).
2. `docs/Estado/auditoria/15_PLAN_MAESTRO_ESTABLE_GENERADOR.md` — plan consolidado aprobado.
Los docs 11-14 son soporte del análisis (ya cerrado); no re-hacer.

## Reglas del proyecto (no negociables)
- **ZERO MOCKS & REAL-ONLY**: Cita rutas y valores concretos verificados en disco. Nunca supongas ni
  inventes métricas, velas, trades, Sharpe, Profit Factor o curvas de equidad.
- **NO HAY PRISA / PACIENCIA METÓDICA**: El usuario no tiene prisa. No tomes atajos apresurados ni intentes
  resolver todo en un solo turno. Usa loops de reintento, depuración y auditoría ilimitados hasta que la solución sea matemáticamente real.
- **AVANCE POR FASES ESTRICTO**: Cada fase sigue el ciclo: INSPECT -> AUDIT -> IMPLEMENT -> TEST -> RUN REAL -> VERIFY -> FIX -> CERTIFY.
- **MANEJO DE AUSENCIA DE DATOS**: Si falta información -> `BLOCKED / NO EVIDENCE`. Si un motor falla -> `ENGINE_ERROR / BLOCKED`.
- **RUTAS DIFERENCIADAS**:
  - *Ultra*: Subcuentas bala ($1k USD), apalancamiento hasta 100x, piramidación, colas gruesas, tolerancia a DD de hasta el 80% (solo descarte por liquidación real).
  - *Fondeo*: $50k USD base, Trailing Drawdown <= 4.5%, Daily Loss Limit (DLL).
- **Ejecuta, no narres.** Si delegas a subagentes, lánzalos de verdad (delegate_task).
- **Backup crítico**: `project.cfx.pre_reconfig_20260809_1056` debe existir antes de tocar el CFX.
- Responde **en español**.

## Dónde está todo (rutas verificadas)
- Proyecto: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`
- SQX: `/home/ubuntu/StrategyQuantX` (servicio systemd 24/7 `strategyquantx`)
- CFX: `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx`
- Datos SQX: `/home/ubuntu/StrategyQuantX/user/data/History/`
- BD operacional: `~/.local/state/ultrarentable/ultrarentable.sqlite3`
- MCP SQX: `http://127.0.0.1:8080/mcp` (8 tools: list_projects, list_databanks,
  list_strategies, get_strategy_stats, run_project, stop_project, initialize, check_connection)
- Web UI SQX: `http://127.0.0.1:5050`
- GUI: DISPLAY=:99, XAUTHORITY=/home/ubuntu/.Xauthority, import -window $WID + xdotool
  (computer_use capture NO funciona en este host: devuelve 0x0)

## Estado actual (11:10 2026-08-09)
Fase de análisis COMPLETA (docs 11-15). Fase 1 de reconfiguración XML A MEDIAS:
6 de 10 cambios aplicados al CFX, 4 pendientes por indentación (Ranking, WFO, filtro
sesión, PopulationSize). Fases 2-3 (reiniciar SQX + run) NO iniciadas.

## Rol
Eres el **Chief Orchestrator**: planificas, despliegas a subagentes, verificas y delivers.
No implementas tú directamente el trabajo de bajo nivel salvo supervisión y correcciones.
