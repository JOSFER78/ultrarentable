# DIRECT-R0-BOOTSTRAP — FIRST CONTINUOUS REPAIR BLOCK

## STATUS
`ACTIVE_DIRECT_REPAIR`

## EXECUTION OWNER
`EXTERNAL_REVIEWER`

Antigravity is not required for this block. The reviewer edits the repository directly on GitHub `main` and verifies every claim that can be verified from the available execution infrastructure.

## OBJECTIVE
Establecer una base ejecutable y reproducible antes de continuar con cualquier capa cuantitativa:
- web portable y compilable;
- FastAPI importable y arrancable;
- localhost/proxy correctamente conectados;
- dependencias coherentes con lockfile;
- UI evidence-only;
- cero mocks/fallbacks cuantitativos en rutas productivas;
- CI reproducible;
- documentación de ejecución coherente.

## STRICT SCOPE
Sólo bootstrap/recovery. No implementar todavía Discovery, Gates, Robustness, Research, Meta-Strategy, ULTRA o FONDEO.

## DIRECT EXECUTION PLAN
### R0.1 REPOSITORY AUTHORITY
- GitHub `JOSFER78/ultrarentable/main` es la única fuente de verdad.
- El código y `.agents/informe&seguimiento/` deben apuntar al mismo estado.
- No se considera válido ningún resultado sólo existente en un workspace local.

### R0.2 WEB TOOLCHAIN
- validar `package.json`, `package-lock.json`, workspace y Next config;
- eliminar dependencias específicas de una máquina/arquitectura cuando rompan reproducibilidad;
- mantener `npm ci` como instalación reproducible;
- `typecheck` y `build` deben ser gates de CI.

### R0.3 BACKEND TOOLCHAIN
- validar `pyproject.toml` y dependencias;
- compilar fuentes Python;
- ejecutar tests mediante CI;
- separar modo local de workers autónomos 24/7.

### R0.4 WEB/API BOUNDARY
- Next proxy configurable mediante `ULTRARENTABLE_API_URL`;
- backend local por defecto en `127.0.0.1:8000`;
- UI debe mostrar `NO_EVIDENCE`/error honesto si API real no responde;
- ninguna página puede fabricar métricas.

### R0.5 ZERO-MOCK QUANTITATIVE PATHS
Auditar y eliminar o aislar fail-closed cualquier helper que fabrique:
- dataset ids;
- SHA256;
- timestamps históricos;
- barras;
- capital inicial;
- slippage/comisiones;
- PF/ROI/DD;
- certificaciones.

No se permite que una ruta productiva pueda generar una respuesta cuantitativa sintética.

### R0.6 CI
Debe existir CI para:
- instalación limpia web;
- typecheck;
- build;
- instalación Python del proyecto;
- compileall;
- pytest.

### R0.7 EVIDENCE
Registrar en `.agents/informe&seguimiento/`:
- `R0_DIRECT_REPAIR.md`
- `R0_RECONCILIATION.md`
- exactos commits y archivos tocados;
- cualquier comprobación que no haya podido ejecutarse por limitación de infraestructura.

## ACCEPTANCE
Sólo:
- `READY_FOR_NEXT_REPAIR` cuando el bloque esté realmente demostrado;
- `BLOCKED` cuando falte una prueba crítica.

R1 permanece bloqueado hasta cerrar R0.

## ABSOLUTE
ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED
