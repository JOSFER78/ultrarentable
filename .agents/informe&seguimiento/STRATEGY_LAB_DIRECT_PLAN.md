# ULTRARENTABLE — STRATEGY LAB DIRECT PLAN

## PRIORIDAD ACTUAL

Antes de FONDEO, firmas, metaestrategias o ejecución, el sistema debe conseguir una cadena de estrategias **real y reproducible**:

```text
SOURCE
→ EXTRACT
→ NORMALIZE
→ PROVENANCE
→ STRUCTURAL VERIFY
→ REAL DATA BIND
→ CANONICAL BACKTEST
→ OOS / ROBUSTNESS
→ DIAGNOSE FAILURE
→ ORGANIC MUTATION
→ FULL RE-TEST
→ CERTIFICATION
```

## DOCTRINA

- ZERO-MOCK
- ZERO-SIMULATION
- ZERO-FORCING
- ZERO-LOOKAHEAD
- REAL-ONLY
- EVIDENCE-GATED

No se puede fabricar una estrategia para llenar el catálogo. No se puede fabricar dataset, hash, capital, curva, métrica ni certificado.

## 1. EXTRACCIÓN

Objetivo: importar exactamente lo que produjo StrategyQuant X, sin reinterpretarlo como resultado validado.

Cada extracción debe conservar:

- engine/source;
- project;
- databank;
- strategy name;
- raw statistics;
- exact canonical source hash;
- símbolo y timeframe sólo si existen explícitamente;
- dataset reference/hash sólo si existen explícitamente.

La extracción se guarda como `EXTRACTED_UNVERIFIED`.

## 2. NORMALIZACIÓN

Convertir la estrategia a la representación canónica sin perder el original.

Debe conservarse:

- source payload;
- canonical DSL/AST;
- strategy hash;
- source lineage;
- version.

La normalización no puede añadir valores ausentes.

## 3. DATASET BINDING

Una estrategia extraída no se puede backtestear hasta asociarla a un dataset real aprobado compatible con:

`venue + instrument + timeframe + date range + checksum`

No se permite inferir dataset por símbolo ni sustituirlo por otro.

## 4. BACKTEST CANÓNICO

La primera ejecución siempre es una reproducción del candidato original.

No modificar parámetros para conseguir mejor resultado.

Registrar:

- strategy hash;
- dataset hash;
- engine version;
- execution policy;
- ledger hash;
- evidence bundle;
- IS / VAL / BLIND OOS;
- costes y fills.

## 5. DIAGNÓSTICO

Cuando falla:

```text
WHY FAILED?
```

clasificar el fallo en:

- overfit;
- data dependency;
- regime dependency;
- execution fragility;
- excessive complexity;
- low sample;
- concentrated returns;
- cost sensitivity;
- other proven cause.

## 6. MEJORA ORGÁNICA

Sólo después del diagnóstico se puede proponer una mutación.

Reglas:

- una hipótesis por mutación principal;
- mínimo cambio necesario;
- parent hash obligatorio;
- child hash nuevo;
- mutation id;
- trial accounting;
- nunca tocar el blind holdout para diseñar la mutación;
- volver a ejecutar desde cero.

Una mutación que empeora no se “arregla” iterando hasta que gane sin contabilizar trials.

## 7. DIVERSIDAD

No conservar 1.000 variantes de la misma idea sólo porque tengan PF similar.

Registrar behavioral genome y agrupar por:

- entry/exit family;
- holding time;
- volatility response;
- regime affinity;
- drawdown shape;
- return concentration;
- correlation profile.

## 8. CERTIFICACIÓN

Sólo cuando exista evidencia completa y vigente:

```text
CERTIFIED_CURRENT
```

Una estrategia extraída o un candidato prometedor nunca equivale a certificada.

## 9. ULTRA

ULTRA buscará convexidad extrema y familias que puedan producir retornos extraordinarios, incluso +1000%, pero el objetivo nunca será usado para forzar una aceptación.

## 10. FONDEO

No se trabaja todavía aquí. Cuando el Strategy Lab sea estable, FONDEO se implementará como pista independiente y **SOLO FUTUROS**, con políticas por firma/producto/cuenta/fecha.

## ESTADO

La primera implementación directa de este plan es la nueva superficie `/api/v2/strategy-lab` y la página `/estrategias` evidence-first.
