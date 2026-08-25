# ORDER AG2-P01-001 — LOCKED

## Status

`LOCKED`

> Esta orden **no es ejecutable todavía**. Solo pasa a `ISSUED` cuando la revisión externa haya aprobado formalmente `AG2-P00-001` y `01_CONTROL_STATE.md` haya sido actualizado por el revisor.

## Target

`PHASE 01 — DATA & DATASET CHAIN OF CUSTODY`

## Trigger de arranque

Antigravity 2.0 debe iniciar esta orden automáticamente en el siguiente ciclo de su watcher (~3 minutos) **únicamente** cuando:

- `ACTIVE_ORDER_ID = AG2-P01-001`;
- `02_CURRENT_ORDER.md` contenga esta orden;
- `status: ISSUED`;
- `CURRENT_PHASE = 01`;
- `PHASE_STATUS = READY`;
- exista una revisión externa `APPROVED` de `AG2-P00-001` en el historial de control.

No requiere intervención manual del usuario.

## Misión

Convertir la cadena de datos en una infraestructura científicamente reproducible: cada backtest, validación, OOS, WFO, forward o metaestrategia debe poder identificar exactamente los bytes de datos usados, su origen, transformación, cobertura temporal y estado de aislamiento.

No optimizar estrategias todavía salvo lo necesario para demostrar la cadena de datos.

## Subagentes obligatorios

Antigravity debe orquestar, como mínimo:

1. `DATA / CHAIN-OF-CUSTODY`
2. `QUANT / TEMPORAL-INTEGRITY`
3. `EXECUTION / DATA-CONSUMER`
4. `VALIDATION / IS-VAL-OOS`
5. `RED-TEAM / DATA-LEAKAGE`
6. `PROVENANCE / HASHES`
7. `RELIABILITY / SNAPSHOT-RECOVERY`
8. `UI/API / DATA-PROVENANCE` cuando las rutas visibles dependan de datasets

Un subagente que implemente una modificación no puede ser el único verificador de esa modificación.

## Alcance obligatorio

### 1. Inventario físico

Para cada dataset realmente consumido por el pipeline:

- fuente/origen;
- proveedor o endpoint cuando exista;
- activo/instrumento;
- timeframe;
- exchange/session/calendar;
- timezone y normalización UTC;
- rango temporal;
- número de filas/barras;
- columnas y tipos;
- gaps/anomalías;
- duplicados;
- orden temporal;
- snapshot identity;
- SHA-256 cuando sea computable;
- formato físico;
- ruta física;
- dependencia de transformación.

### 2. Chain of custody

Crear o verificar un manifiesto de dataset que permita reconstruir:

`SOURCE -> RAW SNAPSHOT -> NORMALIZED SNAPSHOT -> VALIDATION INPUT -> RUN`

Ninguna transformación puede sobrescribir silenciosamente el snapshot anterior.

### 3. Particiones

Verificar separación física y lógica de:

- `IS`
- `VALIDATION`
- `BLIND_OOS/HOLDOUT`
- forward/paper cuando corresponda

Detectar cualquier ruta que permita a Research, Discovery o Mutation contaminar el holdout.

### 4. Temporal integrity

Probar:

- timestamps monotónicos;
- timezone consistency;
- duplicate timestamp handling;
- missing bar policy;
- session boundaries;
- daylight-saving transitions cuando sean relevantes;
- no-lookahead en la preparación de datos;
- imposibilidad de leer datos futuros desde una vista histórica.

### 5. Dataset version governance

Relacionar cada snapshot con:

`dataset_snapshot_id`
`dataset_version`
`dataset_sha256`
`source_id`
`created_at_utc`
`coverage_start`
`coverage_end`
`schema_version`
`normalization_version`

### 6. Consumer audit

Localizar todos los consumidores reales de datos:

- discovery;
- canonical strategy;
- compiler/runtime;
- universal engine;
- validation fabric;
- WFO/OOS;
- research;
- forward;
- portfolio/meta-strategy;
- API/UI.

Verificar que ninguno pueda cargar silenciosamente otro dataset o fallback.

### 7. Real-only

Prohibido introducir fixtures, synthetic data, random data o placeholders en rutas operativas para “hacer pasar” la fase.

Los fixtures permitidos únicamente para tests unitarios aislados deben estar claramente aislados y jamás poder confundirse con evidencia científica.

### 8. Performance / scalability

La solución debe poder manejar el universo de ULTRA sin hardcodear activos ni temporalidades y debe permitir que FONDEO consuma exclusivamente futuros definidos por su registry/policy.

No fijar una lista rígida de símbolos o temporalidades dentro de la lógica general.

### 9. Firebase / historical learning

Si learning histórico referencia datasets, mantener provenance hasta el snapshot original. No modificar ni recrear datos históricos de Firebase como sustitución del original.

## Tests / evidencia obligatorios

Ejecutar comandos reales descubiertos en el repo para:

- tests de ingestión/normalización;
- integridad temporal;
- manifests/hashes;
- aislamiento IS/Validation/OOS;
- consumer-path checks;
- leakage/zero-mock scans;
- typecheck/build si la capa UI/API lo requiere;
- reproducibilidad de carga del mismo snapshot.

Registrar comandos exactos, exit codes y artefactos generados.

## Entregables

Crear y publicar en GitHub:

`.agents/informe&seguimiento/03_HANDOFF_AG2-P01-001.md`

Además deben quedar versionados en GitHub todos los archivos de implementación, tests, manifests y evidencia que formen parte del resultado de la fase y que sean apropiados para el repositorio.

## GITHUB HANDOFF — REGLA OBLIGATORIA

Al terminar la fase, Antigravity **NO debe limitarse a dejar archivos en su workspace local**.

Debe garantizar que el estado completo de la fase quede reflejado en GitHub:

1. código cambiado;
2. tests creados/modificados;
3. manifests de datasets;
4. evidence/hashes que deban ser versionados;
5. `03_HANDOFF_AG2-P01-001.md`;
6. estado de control actualizado según las reglas;
7. commit SHA final;
8. cualquier documento de seguimiento necesario.

El handoff debe identificar el commit final que contiene ese estado.

Si no puede publicar un artefacto concreto por razones de tamaño/seguridad, debe registrar exactamente dónde quedó, cómo se identifica y por qué no puede versionarse; nunca debe declarar la fase completa como si GitHub contuviera toda la evidencia.

## No avanzar

Al terminar:

- no empezar Fase 02;
- no crear la siguiente orden;
- no aprobarse;
- no cambiar autoridad de fase salvo por orden externa.

Estado final esperado:

`READY_FOR_REVIEW`

o

`BLOCKED`
