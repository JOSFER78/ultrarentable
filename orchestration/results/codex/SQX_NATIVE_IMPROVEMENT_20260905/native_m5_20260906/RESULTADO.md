# Recuperación y comprobación del motor — 2026-09-06

La evaluación real de Strategy 1.17.118 (MNQ M5) se recuperó sin repetir la búsqueda ni el recálculo de StrategyQuant. El evaluador anterior rechazaba una orden pendiente cancelada de SQX y dejaba bloqueada la siguiente mejora.

La corrección separa operaciones ejecutadas y órdenes pendientes canceladas. Solo acepta estas últimas con indicadores nativos explícitos y beneficio, comisión y deslizamiento finitos e iguales a cero. Conserva sus registros completos, incluido MAE, y el hash del CSV original. Los estados ambiguos y movimientos económicos desconocidos siguen bloqueando la evaluación. Las métricas nativas deben cuadrar con las operaciones ejecutadas.

| Métrica nativa | Original | Variante |
|---|---:|---:|
| Beneficio IS | 32.536,14 | 32.586,64 |
| Beneficio OOS | 15.789,66 | 15.526,66 |
| Operaciones ejecutadas IS / OOS | 688 / 183 | 689 / 183 |
| Profit factor OOS | 1,35 | 1,35 |
| Retorno / caída OOS | 3,64 | 3,58 |

**Resultado: variante descartada, cero candidatas para la siguiente validación.** Empeoran el beneficio y el retorno/caída fuera de muestra. Además, la variante conserva 95 operaciones IS y 18 OOS incompatibles con las sesiones comprobadas. Cada CSV contiene una orden pendiente cancelada adicional que no cuenta como operación ejecutada.

La conciliación verificó identidad de la fuente, finalización nativa, hashes y estado pendiente antes de actuar. Archivó 25 archivos y liberó exclusivamente el proyecto temporal terminado; conservó la evidencia en disco y cerró la reclamación que bloqueaba nuevos trabajos. El informe de recuperación registra `recovered_without_native_rerun=true` y `active_claim_exists=false`.

Se desplegaron el evaluador corregido y la publicación del estado de error más reciente del programador. Se conservaron copias previas y se verificó que sus hashes coinciden con los locales. Pasaron **104 pruebas de tests/sqx_runtime en 42,671 segundos**, incluyendo el paquete M5 real y el rechazo de alteraciones en los indicadores, muestras y cantidades de las órdenes canceladas.

Tras la recuperación se arrancó el servicio a las 08:14:50 UTC. Eligió automáticamente Strategy 4.8.127, buscó salidas alternativas y recalculó original y dos variantes. El ciclo completo terminó a las 08:17:09 UTC con `COMPLETED_NOT_FUNDING_CERTIFIED`, 27 archivos archivados y ninguna reclamación activa. La primera variante empeoró beneficio, profit factor y retorno/caída IS; la segunda no alcanzó la mejora mínima del 5 % del peor retorno/caída de desarrollo. Ambas conservan incompatibilidades de sesión y se descartaron: cero candidatas para la siguiente fase.

El servicio terminó con `Result=success`; que un servicio de ejecución única quede inactivo después es normal. El temporizador horario quedó activo con siguiente ejecución prevista a las 09:17:09 UTC. Este arranque manual de comprobación demuestra un ciclo completo después de la corrección, no recuperación autónoma ante cualquier fallo.

A las 08:17:53 UTC la generación MYM M5 acumulaba 34.137 intentos, 5.854 más que en la muestra de las 08:08:48 UTC. Son cifras de actividad, no estrategias aprobadas. La selección conserva como máximo cinco exportaciones por lote y la mejora compara como máximo dos variantes.

Evidencia del segundo ciclo: [evaluación](auto_improvement_79c19175b55190d448bf/assessment.json), [archivo verificado](auto_improvement_79c19175b55190d448bf/archive_verified.json). El SHA-256 de la evaluación descargada coincide con el registrado por el motor: `1081aa6153330c9dc8c3d704e54d89ebd662773d612745cdf8c4f734efbd667d`. Esta segunda comprobación local verifica el informe; no se descargó ni reprodujo localmente todo su paquete.

## Límites vigentes

- No hay ninguna estrategia acreditada para fondeo. El diagnóstico de ventanas de 1–5 días no certifica aprobación.
- MNQ instalado procede de un alias CFD: falta demostrar comportamiento con datos del futuro real, costes y reproducción intradía independientes, calendario completo y reglas fechadas del examen.
- Los datos IS/OOS consultados para escoger variantes son datos de desarrollo; se necesitan datos finales intactos.
- A las 08:45 UTC se completó la migración de los 30 proyectos canónicos y sus 30 configuraciones de respaldo para desactivar PTPercent, conservando SLPercent. Se comprobaron dos configuraciones exportadas por SQX después de arrancar. Las estrategias antiguas con objetivos porcentuales siguen excluidas de esta receta. [Evidencia de migración y reanudación](../pt_migration_20260906/RESULTADO.md).
- La mejora nativa explora salidas de estructuras compatibles, con un máximo de dos variantes. No es todavía un mejorador universal ni garantiza encontrar una mejora útil.

Evidencia: [evaluación](auto_improvement_faff40442f5b192e7ce6/assessment.json), [recuperación](auto_improvement_faff40442f5b192e7ce6/reconciliation_result.json), [archivo verificado](auto_improvement_faff40442f5b192e7ce6/archive_verified.json).

SHA-256 de evaluación: `0a0bbd09bc429c9b76d2f87e5ed2bd664e406216b8223ae13c8833e3781f107c`.

SHA-256 del evaluador desplegado: `e1f5bb97fa72847784466cf61288524baa7d6d0b6bb835acff32f042b108d8bc`.

SHA-256 del programador desplegado: `d10eb875e35b6843bc7b8f2fae8528970c484989b097b3a50ba9a72c955bb947`.
