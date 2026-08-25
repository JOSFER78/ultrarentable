# ULTRARENTABLE — ADAPTIVE IMPLEMENTATION CONTROL

**Purpose:** Controlar la reconstrucción y evolución del laboratorio cuantitativo de forma estrictamente secuencial, verificable y adaptativa.

## 0. Regla fundamental

Antigravity **NO puede decidir por sí mismo que una fase está terminada**, ni activar la siguiente fase.

El ciclo obligatorio es:

`CURRENT PHASE -> IMPLEMENT -> TEST -> EVIDENCE REPORT -> EXTERNAL AUDIT -> APPROVED / REJECTED -> NEXT PHASE`

El auditor externo de este ciclo es ChatGPT a partir del estado real del repositorio y de la evidencia producida por Antigravity.

Una fase rechazada **permanece activa** y se corrige; no se salta, no se disimula y no se reinicia desde cero salvo instrucción explícita.

## 1. Jerarquía de verdad

Orden de autoridad:

1. Código ejecutado en el commit auditado.
2. Tests realmente ejecutados y sus logs.
3. Datos físicos y hashes de entrada.
4. Evidence bundles y ledgers generados por esa ejecución.
5. Estado persistido por el sistema.
6. Documentación generada por el proyecto.
7. Documentación histórica.
8. Texto de UI, mensajes, nombres o claims.

Un informe nunca puede demostrar que algo funciona si el código, los datos y la ejecución no lo respaldan.

## 2. Principios innegociables

- REAL-ONLY.
- ZERO-MOCK.
- ZERO-SIMULATION en producción, validación y reporting.
- ZERO-FALLBACKS complacientes.
- ZERO-FORCING de rentabilidad.
- ZERO-LOOKAHEAD.
- IS/Validation/OOS físicamente aislados.
- Todo resultado cuantitativo debe tener provenance.
- Todo resultado certificable debe estar ligado al commit y a los hashes de inputs/outputs.
- La UI nunca calcula ni inventa métricas certificadas.
- Una estrategia antigua no se considera válida automáticamente después de cambios del motor.
- Toda modificación relevante de engine/contracts/gates/data schema requiere revalidación de candidatos afectados.
- Ninguna metaestrategia puede ocultar el fracaso de sus componentes.
- La ausencia de evidencia significa `NO_EVIDENCE`, nunca `PASS`.

## 3. Qué significa “fase aprobada”

Una fase solo puede obtener `APPROVED` cuando:

- su alcance está implementado;
- todos los criterios obligatorios pasan;
- los tests relevantes pasan;
- los tests de regresión pasan;
- no existen fallos P0/P1 abiertos dentro del alcance;
- la evidencia es reproducible desde el commit auditado;
- no existen datos sintéticos o defaults ocultos;
- el resultado negativo, si existe, se muestra como negativo;
- el siguiente riesgo queda identificado.

`PARTIAL`, `BEST_EFFORT`, `WORKS_LOCALLY`, `UI_OK`, `TESTS_GREEN` o `CERTIFIED` no son equivalentes a `APPROVED`.

## 4. Estados de fase

- `LOCKED`: todavía no autorizada.
- `READY`: autorizada para ejecución.
- `IN_PROGRESS`: Antigravity está trabajando.
- `EVIDENCE_PENDING`: código terminado pero falta evidencia.
- `UNDER_REVIEW`: esperando auditoría externa.
- `APPROVED`: todos los gates de fase pasan.
- `REJECTED`: hay defectos que bloquean.
- `REWORK`: corrección después de rechazo.
- `BLOCKED`: falta una dependencia externa real.
- `SUPERSEDED`: el plan cambió por evidencia nueva.

## 5. Política de adaptación

El plan NO es una lista rígida de tareas. Cada fase tiene:

- hipótesis;
- contrato de entrada;
- entregables;
- pruebas;
- criterios de salida;
- ramas de decisión.

Después de cada fase, el auditor debe decidir una de estas rutas:

`APPROVE -> NEXT`
`REJECT -> REWORK`
`BLOCK -> REMOVE DEPENDENCY / WAIT FOR REAL INPUT`
`REDESIGN -> CHANGE PHASE SCOPE`
`ABANDON -> ARCHIVE HYPOTHESIS`

Cuando la evidencia contradiga el diseño esperado, se adapta el siguiente paso. **No se modifica la evidencia para encajar con el plan.**

## 6. Versionado y recertificación

Cada estrategia/candidato debe registrar como mínimo:

- `strategy_id`
- `strategy_version`
- `engine_version`
- `contract_version`
- `data_snapshot_id`
- `data_sha256`
- `code_commit_sha`
- `generation/trial_id` cuando exista
- `validation_run_id`
- `evidence_bundle_id`
- `created_at` y `validated_at` UTC

Cambio de motor, contrato, costes, reglas de ejecución, particionado o gates => la evidencia anterior no puede reutilizarse como aprobación del nuevo sistema sin una revalidación explícita.

## 7. Protocolo humano + Antigravity + ChatGPT

### Antigravity

Ejecuta exclusivamente la fase declarada como `CURRENT_PHASE` en `informes/CONTROL_STATE.md`.

No cambia `CURRENT_PHASE` a la siguiente.

Al terminar entrega:

`informes/fases/PHASE_<N>_EXECUTION_REPORT.md`

Ese informe debe contener commit SHA, archivos cambiados, comandos exactos, resultados, hashes, fallos y evidencia.

### ChatGPT

Lee el estado real del repositorio y el informe de fase, verifica coherencia, analiza riesgos y emite:

- `APPROVE`
- `REJECT`
- `BLOCK`
- `REDESIGN`

Solo tras `APPROVE` puede generarse el siguiente paquete de instrucciones para Antigravity.

### Usuario

Decide si desea aplicar la siguiente fase al repositorio después de recibir la recomendación del auditor.

## 8. Prohibiciones específicas para Antigravity

No:

- inventar datasets;
- rellenar métricas faltantes con valores plausibles;
- cambiar thresholds para “conseguir” candidatos;
- marcar candidatos aprobados por score parcial;
- usar una curva preexistente como prueba del nuevo engine;
- usar datos históricos procesados por un motor antiguo como evidencia del motor nuevo sin recertificación;
- ocultar estrategias rechazadas;
- transformar `NO_EVIDENCE` en `0`, `N/A`, `PASS` o una estimación;
- modificar tests únicamente para que pasen sin demostrar la propiedad;
- crear mocks que puedan entrar en rutas de producción o validación;
- ejecutar la siguiente fase por adelantado.

## 9. Definición de éxito del programa

El programa solo se considera completado cuando el laboratorio puede demostrar, con evidencia reproducible:

`REAL DATA -> CANONICAL STRATEGY -> DETERMINISTIC ENGINE -> TRADE LEDGER -> METRICS -> GATES -> EVIDENCE -> CERTIFICATION -> UI`

y además demostrar que una modificación del sistema invalida, cuando corresponda, la certificación antigua y fuerza la revalidación correcta.

---

**CURRENT CONTROL AUTHORITY:** este documento + `CONTROL_STATE.md`.
