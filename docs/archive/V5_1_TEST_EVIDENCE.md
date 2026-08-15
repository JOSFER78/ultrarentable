# Evidencia de Pruebas — Autopiloto Total BingX (v5.1)

## 1. Verificación desde Instalación Limpia

Script ejecutado: [`scripts/verify_clean_install.py`](file:///c:/Users/yo/Desktop/WORKSPACE/projects/ultrarentable/scripts/verify_clean_install.py)

```text
============================= test session starts =============================
platform win32 -- Python 3.11.8, pytest-9.1.1, pluggy-1.6.0
collected 32 items

services/api/tests/test_autopilot.py::test_autopilot_start_with_empty_payload_returns_202 PASSED
services/api/tests/test_autopilot.py::test_autopilot_status_and_decisions PASSED
services/api/tests/test_autopilot.py::test_autopilot_lifecycle_pause_resume_stop PASSED
services/api/tests/test_autopilot.py::test_leverage_trials_recorded_without_fake_500_percent PASSED
services/api/tests/test_captured_artifacts.py::test_active_normalized_dataset_has_real_raw_chain_and_closed_candles PASSED
services/api/tests/test_dsl.py (13 tests) PASSED
services/api/tests/test_factory.py (6 tests) PASSED
services/api/tests/test_fast_engine.py (3 tests) PASSED
services/api/tests/test_local_storage.py PASSED
services/api/tests/test_zip_structure.py PASSED

================== 28 passed, 4 skipped in 7.29s ===================
```

## 2. Verificación del Build Web Next.js

Comando ejecutado: `npm run web:build`

```text
✓ Compiled successfully in 7.6s
  Running TypeScript ...
  Finished TypeScript in 12.2s ...
  Collecting page data using 7 workers ...
✓ Generating static pages using 7 workers (12/12) in 1075ms
```
