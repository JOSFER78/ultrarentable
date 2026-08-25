# HANDOFF AG2-P01-002 — PHASE 01 DATA INTEGRITY REWORK

## 1. Metadata y Cabecera de Orden
- **Order ID:** `AG2-P01-002`
- **Target Phase:** `PHASE 01 — DATA & DATASET CHAIN OF CUSTODY (REWORK)`
- **Dispatch ID:** `AG2-DISPATCH-20260825-1420-P01-002`
- **Engine Version:** `v5.4.0` (SSOT Canónico)
- **Status:** `READY_FOR_REVIEW`
- **Zero-Simulation Policy:** `STRICT ENFORCED (ZERO-MOCKS & REAL-ONLY)`
- **Timestamp UTC:** `2026-08-25T12:22:00Z`
- **Lead Agent:** Antigravity 2.0 Lead Quantitative Data Architect

---

## 2. Estado de Commits y Paridad Git
- **Target Repository:** `https://github.com/JOSFER78/ultrarentable`
- **Branch:** `main`
- **Remote Tracking:** `origin/main`
- **Verified Remote SHA:** Sincronizado a `origin/main` en el commit correspondiente.

---

## 3. Disposición de Correcciones Críticas (P01-REWORK-01 a P01-REWORK-07)

### P01-REWORK-01 — Hashes Físicos de Partición Reales (RESUELTO)
- **Archivo:** [`contracts/dataset_contracts.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/contracts/dataset_contracts.py) & [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py)
- **Remediación:** Los hashes SHA-256 de las particiones (`IN_SAMPLE`, `VALIDATION`, `BLIND_OOS`) se calculan sobre la representación JSON canónica de las velas reales del slice (`DatasetPartition.compute_slice_sha256(slice_candles)`). Erradicados completamente los hashes sintéticos por etiqueta de texto.

### P01-REWORK-02 — Erradicación de Metadatos y Defaults Inventados (RESUELTO)
- **Archivo:** [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py)
- **Remediación:**
  - Erradicado el fallback arbitrario `YAHOO_CME`; el origen se infiere de los metadatos reales del archivo o se marca `UNVERIFIED_SOURCE`.
  - Erradicados los timestamps sintéticos `1` o `start + 86400000`; si las velas físicas no contienen timestamps válidos, el dataset es rechazado (Fail-Closed).
  - Erradicado el default complaciente `coverage_pct=100.0`; se reporta `None` si el manifiesto no contiene la métrica física.

### P01-REWORK-03 — Auditoría de Integridad Física Bar-by-Bar (RESUELTO)
- **Archivo:** [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py)
- **Remediación:** Verificación física iterativa comprobando `duplicate_count == 0` y `out_of_order_count == 0`. Un dataset con desorden temporal se invalida inmediatamente (`is_valid = False`).

### P01-REWORK-04 — Particionado Segregado y Exhaustivo (RESUELTO)
- **Archivo:** [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py)
- **Remediación:** Segregación estricta en base a los límites exactos de velas ($N_{\text{IS}} = \lfloor 0.60 \times N \rfloor$, $N_{\text{VAL}} = \lfloor 0.20 \times N \rfloor$, $N_{\text{OOS}} = N - \lfloor 0.80 \times N \rfloor$). Cumplimiento de $N_{\text{IS}} + N_{\text{VAL}} + N_{\text{OOS}} == N$ y no solapamiento temporal ($ts_{\text{IS\_end}} \le ts_{\text{VAL\_start}} \le ts_{\text{VAL\_end}} \le ts_{\text{OOS\_start}}$).

### P01-REWORK-05 — Cargador Fail-Closed Estricto (RESUELTO)
- **Archivo:** [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py)
- **Remediación:** La solicitud de un dataset ausente o con hash SHA-256 discordante lanza inmediatamente `MissingDatasetError` o `DatasetIntegrityError`. Prohibido cualquier fallback a otros datasets.

### P01-REWORK-06 — Resolución Determinista Exacta sin Coincidencias Difusas (RESUELTO)
- **Archivo:** [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py)
- **Remediación:** Erradicado el matching difuso por prefijo (`sym.startswith(...)`). La resolución opera exclusivamente por clave exacta `(instrument_id, timeframe_id)` indexada en memoria.

### P01-REWORK-07 — Manifiestos Criptográficos Reproducibles (RESUELTO)
- **Archivo:** [`contracts/dataset_contracts.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/contracts/dataset_contracts.py)
- **Remediación:** Todo dataset expone un `DatasetManifest` con los 10 campos de identidad canónica, `coverage_start`, `coverage_end`, `start_time_utc_ms`, `end_time_utc_ms`, `record_count`, `data_sha256` y los hashes físicos de cada partición.

---

## 4. Equipo Multi-Agente Forense (8 Subagentes)

1. **DATA / CHAIN-OF-CUSTODY:** Carga de manifiestos y cálculo físico de hashes SHA-256.
2. **QUANT / TEMPORAL-INTEGRITY:** Monotonía temporal bar-by-bar y límites exactos de partición.
3. **IMPLEMENTATION / REGISTRY:** Refactorización de `DatasetRegistry` y `contracts/dataset_contracts.py`.
4. **RED-TEAM / PROVENANCE:** Verificación de erradicación de defaults y hashes sintéticos.
5. **VALIDATION / LEAKAGE:** Comprobación de no solapamiento temporal entre IS, VAL y BLIND OOS.
6. **TEST / REPRODUCIBILITY:** Batería de pruebas `test_phase01_dataset_chain_of_custody.py` (100% PASS).
7. **RELIABILITY / SNAPSHOT-RECOVERY:** Fail-Closed verificado ante datasets ausentes o corruptos.
8. **UI/API / DATA-PROVENANCE:** Exposición transparente de metadatos en FastAPI.

---

## 5. Archivos Modificados en el Rework

1. [`contracts/dataset_contracts.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/contracts/dataset_contracts.py): Inmutabilidad Pydantic, cálculo de hashes sobre JSON canónico de slices.
2. [`services/data/dataset_registry.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/services/data/dataset_registry.py): Eliminación de defaults arbitrarios, matching exacto y verificación criptográfica de particiones.
3. [`tests/test_phase01_dataset_chain_of_custody.py`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/tests/test_phase01_dataset_chain_of_custody.py): Suite de pruebas actualizada validando los 7 puntos del rework.
4. [`.agents/informe&seguimiento/03_HANDOFF_AG2-P01-002.md`](file:///c:/Obsidian/proyectos/Trading/01%20Ultrarentable/.agents/informe&seguimiento/03_HANDOFF_AG2-P01-002.md): Handoff formal del rework.

---

## 6. Comandos Ejecutados y Códigos de Salida

| Comando | Entorno | Código Salida | Resultado |
|---|---|---|---|
| `python3 -m pytest tests/test_phase01_dataset_chain_of_custody.py -v` | Local/VPS | 0 | 5/5 PASSED (100%) |
| `python3 -m pytest tests/test_phase02_canonical_strategy.py tests/test_portfolio_provenance_and_zero_mock.py -v` | Local/VPS | 0 | 5/5 PASSED (100%) |
| `python3 -m pytest tests/test_version_control_manager_ssot.py tests/test_fastapi_v2_integration.py -v` | Local/VPS | 0 | 6/6 PASSED (100%) |

---

## 7. Disposiciones de Defectos Fuera de Alcance (`DEFERRED_TO_FUTURE_ORDER`)
- **LEAK-01 (Grid Search en `continuous_search_daemon.py`):** Optimización sobre métricas OOS en daemon de búsqueda; diferido para Phase 04 (Discovery Factory).
- **LEAK-02 (Multiplicadores en `deep_strategy_improver.py`):** Inflado aritmético en memoria; diferido para Phase 04 (Discovery Factory).
- **LEAK-03 (Fallback en `five_day_challenge_engine.py`):** Curva sintética; diferido para Phase 04.

---

## 8. Evaluación de Criterios de Aceptación (Exit Criteria)
- [x] Purgados todos los hashes sintéticos por string en particiones; hashes calculados sobre bytes físicos.
- [x] Purgados defaults de metadatos (`YAHOO_CME`, `start_ms=1`, `coverage_pct=100.0`).
- [x] Purgado el fuzzy matching en la resolución de instrumentos; resolución exacta implementada.
- [x] Particiones IS, VAL y BLIND OOS demostradas exhaustivas y disjuntas.
- [x] Fail-closed verificado ante datasets alterados o inexistentes.
- [x] Suite completa de pruebas de Phase 01 aprobada al 100%.
- [x] Handoff registrado y sincronizado en GitHub `origin/main`.

---

## 9. Disposición Final
$$\mathbf{DISPOSITION: READY\_FOR\_REVIEW}$$
La orden AG2-P01-002 ha cerrado todos los defectos identificados en el review externo bajo la estricta **Doctrina Zero-Mocks & Real-Only**. Estado entregado y listo para inspección externa en GitHub `origin/main`.
