> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: orquestación del 2026-08-09 con supuestos MCP/SQX superados; el autopiloto real es services/background_searcher.py (docs/00_MASTER_IDEAS_Y_PLAN.md §2.2). **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

# ORQUESTACIÓN — Motor de búsqueda Ultrarentable (3 frentes)
> Fecha: 2026-08-09 · Rol: orquestador + revisor (NO ejecutar)
> Objetivo global del usuario:
>   1) ULTRA: estrategias de MILES de % verificables en backtest (kamikaze, se quema 8/10).
>   2) FONDEO-APROBAR: estrategias para aprobar exámenes de fondeo rápido.
>   3) FONDEO-MANTENER: mantener cuentas aprobadas estables con control de reglas.

## Reparto de frentes (subagentes, ejecutan; Hermes orquesta y revisa)

### Frente A — Catálogo de técnicas de StrategyQuant ✅ ENTREGADO y REVISADO
- Subagente A (deleg_6a397640) terminó.
- Entregable: `docs ayuda/tecnicas estrategias ultrarentables/06_CATALOGO_TECNICAS_STRATEGYQUANT.md`
- 26+ técnicas SQX con evidencia [WEB]/[OBS]/[VPS]; config kamikaze ULTRA y config FONDEO; pipelines.
- Revisión del orquestador: VALIDADO (alineado con doctrina KAMIKAZE.md de Obsidian).

### Frente B — Modo ULTRA vs FONDEO + configurador de búsqueda auto-asistido por IA 🔄 EN CURSO
- Subagente B (deleg_9e06a248) trabajando.
- Objetivo: corregir quality_gates para que ULTRA no filtre por DD (solo ruina real dd>=100), FONDEO sí conservador; crear configurador IA (endpoint + UI).
- Archivos que toca: quality_gates.py, optimization_loop.py, strategy_evidence.py, adversarial_validation.py, fast_engine_campaign.py, sqx_router.py, campaign_planner.py, test_quality_gates_regression.py, apps/web (configurador).
- Requisitos de aceptación: suite pytest 0 fallos + test de regresión cubre ambos modos.

### Frente C — MOTOR KAMIKAZE que consiga MILES de % (núcleo Objetivo 1) ⏳ PENDIENTE de despachar
- Depende de B (modo/configurador) para no pisar el core.
- Mandato preparado: configurar y lanzar búsquedas SQX kamikaze ULTRA según el catálogo §3
  (generación masiva, sin filtros de calidad en generación, solo ruina real, mutación alta),
  capturar candidatos, validarlos con backtests reales (miles de % verificables),
  y alimentar el configurador. Artefacto esperado: N estrategias con retornos >= 1000% IS verificables.

### Frente D — FONDEO-APROBAR (Objetivo 2) ⏳ PENDIENTE de despachar
- Depende de B (modo fondeo + configurador). Usar catálogo §4 (WFO oblg, cross-checks, DD estricto).
- Mandato preparado: configurar SQX para pasar evaluaciones prop firm (FundedNext/Bulenox u otra),
  generar/validar candidatos que cumplan DD bajo, consistencia, profit target, sin daily loss.

### Frente E — FONDEO-MANTENER con control de reglas (Objetivo 3) ⏳ PENDIENTE de despachar
- Depende de D + módulo Fondeo (plan maestro Fase 5: constraint engine, niveles de permiso, kill switch).
- Mandato preparado: control de reglas post-aprobación (daily loss lock, trailing drawdown/HWM,
  tamaño máx, sesiones, noticias, consistencia, kill switch), alertas, simulación de cuentas funded reales.

## Orden de despacho (para evitar colisiones de archivos)
1. B termina (modo/configurador) → revisar.
2. Despachar C (motor kamikaze miles %) — núcleo.
3. Despachar D (fondeo aprobar) — usa configurador.
4. Despachar E (fondeo mantener) — usa módulo fondeo.
5. Revisión integral: verificar cada entregable con evidencia empírica (tests, backtests reales, endpoints).

## Recordatorio de rol
- Hermes ORGANIZA, PREPARA mandatos y SUPERVISA/REVISA.
- Los SUBAGENTES ejecutan código. Hermes NO edita archivos de la app directamente.
