# REVIEW AG2-P02-007 — DECISIÓN EXTERNA

## Resultado
`FINAL_PHASE_CLOSE_ORDER`

## Auditoría
P02-007 ha cerrado los principales defectos que impedían considerar demostrada la semántica canónica bidireccional y la trazabilidad del runtime. El handoff documenta identidad consistente, ramas LONG/SHORT explícitas para BOTH, fail-closed para `max_open_positions > 1`, trazabilidad hasta EventBacktestEngine y 39/39 tests en VPS. filecite no aplica en repositorio; la evidencia primaria queda en los artefactos P02-007 de origin/main.

## Decisión
No se salta todavía a Phase 03.

Se emite una ÚLTIMA orden de cierre de Phase 02: `AG2-P02-008`.

Esta orden no pretende añadir nuevas capacidades al runtime. Su objetivo es verificar de forma independiente que Phase 02 queda internamente coherente, reproducible, versionada y apta para entregar el control a Phase 03.

## Razones para exigir cierre final
1. Verificar que el nuevo modelo declarativo `long_conditions/short_conditions` está integrado sin romper serialización, hashing, snapshots o adapters legacy.
2. Verificar que el boundary demostrado por P02-007 corresponde realmente al camino de producción y que no existe una segunda ruta canónica paralela.
3. Verificar que `UNSUPPORTED_FAIL_CLOSED` está reflejado coherentemente en contrato, runtime, tests y matriz semántica.
4. Verificar identidad exacta de dispatch/order/SHA y ausencia de documentación contradictoria.
5. Ejecutar una última prueba de reproducibilidad: mismo strategy snapshot + mismo dataset + mismas versiones/policies => mismo execution/ledger result.
6. Ejecutar un red-team final contra mocks, fallbacks, defaults, lookahead, caller-controlled provenance y duplicación de autoridad.

## Criterio de salida
Phase 02 sólo podrá quedar `APPROVED_FOR_NEXT_PHASE` si todos los claims críticos son `PROVEN`, no existen blockers y la evidencia está publicada en origin/main.

Si aparece un blocker real, la orden debe terminar `BLOCKED` o `REWORK_REQUIRED`; no puede inventarse una corrección para conseguir PASS.
