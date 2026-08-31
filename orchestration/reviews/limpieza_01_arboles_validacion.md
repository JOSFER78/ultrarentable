# LIMPIEZA 0.1 — Los dos árboles de validación: VEREDICTO

> ⚠️ **SUPERADO E INCORRECTO EN PARTE (2026-08-31, auditoría adversarial de 16 agentes).**
> Este documento afirma que `services/validation/engines/` "no lo ejecuta nadie": es FALSO —
> `validation_router.py:158-160,266` lo importa a nivel de módulo y lo ejecuta en el endpoint
> `POST /validate-11-gates` montado en `main.py`. Ejecutar la acción nº1 propuesta aquí tumbaría
> `ultrarentable-api`. La conclusión vigente está en la síntesis F00 (ambos árboles VIVOS, son
> implementaciones distintas; ninguno puede moverse en bloque). No usar este documento como base.

**Auditor:** Hermes · **Fecha:** 2026-08-31 · **Método:** solo lectura, evidencia con grep/find

## El hallazgo

No son dos copias del mismo árbol. Son **dos implementaciones distintas de los 11 gates**,
con nombres distintos, y ambas presentes en el repo:

| Gate | Árbol A · `services/validation/engines/` | Árbol B · `services/api/app/validation/gates/` |
| :-- | :--- | :--- |
| 01 | `gate_01_ingest_sanity.py` | `gate_01_data_ingest.py` |
| 05 | `gate_05_monte_carlo_stress.py` | `gate_05_monte_carlo.py` |
| 08 | `gate_08_deflated_sharpe.py` | `gate_08_dsr_ratio.py` |
| 09 | `gate_09_novelty_antioverfit.py` | `gate_09_novelty_antifit.py` |
| 11 | `gate_11_ensemble_synergy.py` | `gate_11_nautilus_event.py` |

## Cuál certifica de verdad: el ÁRBOL B

Evidencia, en orden de contundencia:

1. **El único orquestador vive en B:**
   `services/api/app/validation/gates/gate_pipeline_orchestrator.py`.
   Es el que expone `evaluate_all_gates`. En A no existe equivalente.
2. **`scripts/mine.py` usa B:** importa `GatePipelineOrchestrator` de ese árbol.
3. **La evidencia física en disco tiene los nombres de B.** En
   `data/evidence/UR_ULTRA_NQ_4H/` los ficheros son `gate_01_data_ingest.json`,
   `gate_09_novelty_antifit.json`… es decir, los generó B.
4. **Los gates de A no los ejecuta nadie.** `services/validation/validation_router.py` los cita
   como cadenas de texto (`"module_path": "services/validation/engines/gate_01_ingest_sanity.py"`)
   dentro de un catálogo descriptivo que devuelve un endpoint. **No hay `importlib` ni
   despacho dinámico**: son metadatos, no ejecución. Fuera de eso, solo los importan
   `engines/__init__.py` y los tests.

## Matiz importante: `services/validation/` NO está muerto

Solo lo está su subcarpeta `engines/`. El resto del árbol A está vivo y es necesario:

| Componente vivo en A | Quién lo usa |
| :--- | :--- |
| `validation_router.py` | `services/api/app/main.py` (montado en `/api/v2/validation`) |
| `prop_firm_risk_engine.py` | tests de fondeo |
| `evidence_bundle_service.py` | ciclo de evidencias |
| `candidate_registry.py` | registro de candidatos |
| `quant_validation_fabric.py` | tejido de validación |
| `engine/event_backtest_engine.py` | motor de backtest (modificado en el changeset auditado) |

## El problema real, y no es solo ruido

`/api/v2/validation` **anuncia los engines del árbol A como si fueran el motor de certificación**,
cuando quien certifica es B. Cualquiera que consulte la API —una persona, la web, un agente futuro—
concluirá que el sistema valida con unos gates que en realidad no se ejecutan nunca.
No es código muerto inofensivo: es **documentación que miente desde un endpoint**.

## Acción propuesta (no ejecutada aún)

1. `services/validation/engines/gate_*.py` (11 ficheros) → `cuarentena/gates_implementacion_paralela/`
   con manifiesto SHA-256. Cero borrados.
2. Ajustar `engines/__init__.py` y los tests que los importan.
3. **Corregir `validation_router.py`** para que su catálogo apunte a los gates reales del árbol B.
   Esto es lo más urgente de los tres: mientras no se haga, la API miente.
4. Dejar constancia en el SSOT de que el pipeline canónico es
   `services/api/app/validation/gates/gate_pipeline_orchestrator.py`, sin ambigüedad.

**Nota de gobernanza:** el punto 2 toca ficheros `gate_*.py`, que por doctrina (§13.2) exigen
fase auditada. Se ejecutará con esa formalidad, no de tapadillo.
