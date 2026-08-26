# ORDER AG2-R0-BOOTSTRAP — FIRST CONTINUOUS REPAIR BLOCK

## STATUS
`ISSUED`

## OBJECTIVE
Establecer una base ejecutable y reproducible: instalación limpia, web compilable, API arrancable, localhost verificable y control de dependencias. No se implementa funcionalidad cuantitativa nueva.

## SOURCE OF TRUTH
GitHub `JOSFER78/ultrarentable` / `main`.

## STRICT SCOPE
SOLO bootstrap/recovery del repositorio actual:
- Node/npm/workspace/lockfile
- apps/web
- FastAPI import/startup básico
- configuración de entorno necesaria para arrancar
- smoke tests y documentación de arranque

NO:
- Discovery
- StrategyQuant
- Genome
- Gates
- Robustness
- Research
- Meta-Strategy
- ULTRA
- FONDEO
- cambios de estrategia/riesgo

## SUBAGENTS OBLIGATORIOS
1. RECON — entrypoints, scripts y dependencias reales.
2. NODE/DEPENDENCY — instalación limpia y lockfile.
3. NEXT — typecheck/build/dev server.
4. FASTAPI — import/startup/health.
5. E2E — navegador/HTTP localhost y proxy.
6. ZERO-MOCK — escaneo de rutas UI/startup.
7. RED-TEAM — fallos de arranque y configuraciones ocultas.
8. LEAD — reconciliación independiente.

El lead NO puede ser el único verificador.

## EXECUTION PLAN
### 0. CONTROL
Leer `00_DISPATCH.md`, `01_CONTROL_STATE.md`, `02_CURRENT_ORDER.md` y este archivo desde `origin/main`. Si no coinciden exactamente: `BLOCKED`.

### 1. CLEAN INSTALL
Registrar Node/npm. Ejecutar instalación limpia usando el lockfile. Prohibido reutilizar `node_modules` externo. Registrar `git status` y SHA.

### 2. WEB
Ejecutar:
- `npm ci` (o equivalente exacto según el lockfile)
- `npm --workspace apps/web run typecheck`
- `npm --workspace apps/web run build`
- `npm --workspace apps/web run dev`

Demostrar proceso vivo y HTTP real en `http://localhost:3000`.

### 3. API
Arrancar FastAPI en modo local, sin activar `ULTRARENTABLE_AUTONOMOUS_RUNTIME`. Demostrar import/startup y endpoint de versión/salud.

### 4. PROXY/E2E
Verificar que la web alcanza `/api/*` mediante el rewrite real hacia el backend. Sin fake server, fake response ni fallback sintético.

### 5. ZERO-MOCK SCAN
Buscar en las rutas alcanzables desde la home:
- `Math.random`
- dataset/hash fabricado
- timestamp fabricado
- capital cuantitativo por defecto
- candidate→certified fallback
- fake API success

Cualquier caso que afecte a resultados o confianza de producción = `BLOCKED` hasta eliminarlo o aislarlo explícitamente como fixture de test.

### 6. REPAIR
Todo blocker del alcance se corrige y se vuelve a probar desde instalación limpia.

### 7. EVIDENCE
Crear:
- `.agents/informe&seguimiento/R0_AGENT_LEDGER.md`
- `.agents/informe&seguimiento/R0_RECONCILIATION.md`
- `.agents/informe&seguimiento/03_HANDOFF_AG2-R0-BOOTSTRAP.md`

Cada subagente debe aportar comandos, exit codes, archivos revisados/cambiados y conclusión.

### 8. DELIVERY
En `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`:
`git status` → `git add` → `git commit` → `git pull --rebase origin main` → `git push origin main` → `git fetch origin main` → verificar SHA remoto.

## ACCEPTANCE
Sólo:
- `READY_FOR_NEXT_REPAIR`
- `BLOCKED`

No se autoriza R1 ni Phase 03 dentro de esta orden.

## ABSOLUTE
ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · REAL-ONLY · EVIDENCE-GATED

## STOP
Después de publicar el handoff y verificar `origin/main`, STOP absoluto. No seleccionar ni crear la siguiente orden.