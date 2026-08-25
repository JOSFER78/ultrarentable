# ANTIGRAVITY — GATED PHASE RUNBOOK

## Modo de ejecución obligatorio

Estás trabajando en `JOSFER78/ultrarentable`.

Tu misión no es completar todo el plan. Tu misión es ejecutar **EXCLUSIVAMENTE** la fase indicada por:

`informes/CONTROL_STATE.md`

Antes de modificar código:

1. Lee `informes/00_ADAPTIVE_IMPLEMENTATION_CONTROL.md`.
2. Lee `informes/01_ADAPTIVE_MASTER_PLAN.md`.
3. Lee `informes/CONTROL_STATE.md`.
4. Lee el archivo de instrucciones de la fase actual.
5. Inspecciona el código real necesario para esa fase.

## Regla de bloqueo

Nunca:

- cambies el número de `CURRENT_PHASE`;
- marques una fase como `APPROVED`;
- generes instrucciones de la siguiente fase dentro del reporte;
- declares certificación global del sistema;
- reutilices un evidence bundle como prueba de una versión incompatible;
- rellenes datos ausentes;
- inventes un resultado esperado.

Tu única autoridad para considerar desbloqueada una fase es un cambio explícito del archivo `CONTROL_STATE.md` realizado después de una auditoría externa.

## Regla específica de descubrimiento

ULTRARENTABLE no busca “la estrategia con mayor ROI”. Cuando una fase afecte al Discovery Engine debes preservar la separación entre:

`DISCOVERY_SCORE != CERTIFICATION_STATUS`

Discovery debe producir hipótesis diversas y priorizar investigación; jamás convertir un score de descubrimiento en aprobación.

En discovery son obligatorios, cuando estén dentro del alcance de la fase:

- Strategy Genome / behavioral fingerprint;
- clustering y deduplicación por comportamiento;
- campañas especializadas de búsqueda;
- trial accounting y genealogy;
- separación exploration/exploitation;
- research budget por familia/campaña;
- aprendizaje de fertility, novelty y robustness;
- filtros en cascada antes de los gates caros;
- preservación de candidatos rechazados y sus razones.

No está permitido solucionar una baja tasa de aprobación relajando gates, cambiando thresholds arbitrariamente o generando más variantes casi idénticas del mismo genome.

## Durante la implementación

Trabaja sobre el código real del repositorio.

Prioridad:

`correctness > reproducibility > evidence > research diversity > performance > convenience`

Mantén cambios pequeños y trazables. No hagas refactors masivos que no sean necesarios para la fase.

No borres tests que fallen para ocultar el problema. No rebajes asserts. Si un test contradice la arquitectura, documenta el conflicto antes de modificarlo.

## Pruebas

Ejecuta primero las pruebas más cercanas a tu cambio y después la regresión global disponible.

Guarda:

- comandos exactos;
- exit codes;
- resumen de resultados;
- errores completos relevantes;
- hashes o IDs de datos;
- commit SHA final;
- en fases de discovery: número de trials, familias, genomes, duplicados, candidatos retenidos/rechazados y distribución del presupuesto.

Cuando una prueba no pueda ejecutarse por una dependencia externa real, informa `BLOCKED` y explica la dependencia. No simules el resultado.

## Reporte obligatorio

Al terminar la fase crea:

`informes/fases/PHASE_<NN>_EXECUTION_REPORT.md`

El reporte debe incluir exactamente estas secciones:

1. Scope
2. Baseline commit
3. Final commit
4. Files changed
5. Architecture impact
6. Commands executed
7. Test results
8. Real data/evidence used
9. Hashes/IDs
10. Discovery statistics, when applicable
11. Defects found
12. Residual risks
13. What was NOT proven
14. Proposed phase result (`READY_FOR_REVIEW` only)

No escribas `APPROVED` en tu reporte.

## Criterio de honestidad

Si el resultado es malo, escríbelo.

Si no hay candidatos, escríbelo.

Si no hay diversidad suficiente, escríbelo.

Si una familia produce muchos candidatos pero casi ningún superviviente robusto, repórtalo como señal de investigación, no como motivo para relajar los gates.

Si una métrica no puede demostrarse, usa `NO_EVIDENCE`.

Si el código compila pero el comportamiento real no está probado, el comportamiento queda `UNVERIFIED`.

Si documentación y ejecución contradicen, reporta la contradicción.

## Final de una fase

Cuando el reporte esté completo, detente.

No empieces la siguiente fase.

La siguiente acción será una revisión externa del reporte y del commit. Solo después de una decisión externa podrá desbloquearse otro paquete de instrucciones.
