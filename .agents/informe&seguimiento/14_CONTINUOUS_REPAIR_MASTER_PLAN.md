# ULTRARENTABLE — CONTINUOUS REPAIR MASTER PLAN
## Programa incremental de estabilización, reparación y verificación continua

**Repositorio oficial:** `JOSFER78/ultrarentable`  
**Rama de control:** `main`  
**Directorio de gobernanza:** `.agents/informe&seguimiento/`  
**Fuente de órdenes:** GitHub `origin/main`  
**Orquestador:** Antigravity 2.0 + subagentes  
**Revisor externo:** ChatGPT  
**Doctrina:** `REAL-ONLY · ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · EVIDENCE-GATED`

---

# 1. OBJETIVO

Este documento establece el programa de reparación continua del sistema completo.

No pretende arreglar todo en un único commit. El objetivo es llegar a un repositorio que:

```text
ARRANCA
→ ES REPRODUCIBLE
→ TIENE UNA ÚNICA FUENTE DE VERDAD
→ NO INVENTA DATOS
→ NO PROMOCIONA CANDIDATOS A CERTIFICADOS
→ MANTIENE VERSIONES Y PROVENANCE
→ EJECUTA EL MOTOR REAL
→ EXPONE LA EVIDENCIA REAL EN LA WEB
→ PUEDE RECUPERARSE
→ PUEDE INVESTIGAR 24/7
```

La reparación será **incremental y acumulativa**. Cada bloque debe dejar el sistema en un estado igual o mejor que el anterior.

---

# 2. REGLA OPERATIVA PRINCIPAL

Antigravity **NO ejecuta este documento como una fase gigante**.

Este documento es un mapa de reparación.

La única tarea ejecutable es la que ChatGPT publique en:

```text
.agents/informe&seguimiento/00_DISPATCH.md
.agents/informe&seguimiento/01_CONTROL_STATE.md
.agents/informe&seguimiento/02_CURRENT_ORDER.md
```

El ciclo es:

```text
CHATGPT REVISA
    ↓
selecciona el siguiente bloque pendiente
    ↓
publica UNA orden
    ↓
NUEVO dispatch_id
    ↓
CRON DE ANTIGRAVITY
    ↓
SUBAGENTES
    ↓
IMPLEMENTACIÓN
    ↓
PRUEBAS
    ↓
EVIDENCIA
    ↓
PUSH main
    ↓
HANDOFF
    ↓
STOP
    ↓
CHATGPT REVISA
    ↓
continúa / rework / bloquea / siguiente bloque
```

Nunca se ejecutan dos bloques simultáneamente salvo tareas explícitamente indicadas dentro de la misma orden.

---

# 3. REGLA DE ORO: REPARAR POR CAPAS

No saltar directamente a generación masiva, estrategias, metaestrategias o fondeo si las capas inferiores no son fiables.

Orden de dependencia:

```text
LAYER 0 — REPOSITORY / CONTROL
        ↓
LAYER 1 — STARTUP / BUILD
        ↓
LAYER 2 — DEPENDENCIES / CONFIG
        ↓
LAYER 3 — API / DATABASE / REAL DATA
        ↓
LAYER 4 — CANONICAL DOMAIN / VERSIONING
        ↓
LAYER 5 — EXECUTION / LEDGER
        ↓
LAYER 6 — VALIDATION / EVIDENCE
        ↓
LAYER 7 — WEB / API PROVENANCE
        ↓
LAYER 8 — DISCOVERY
        ↓
LAYER 9 — RESEARCH / LEARNING
        ↓
LAYER 10 — PORTFOLIO / META
        ↓
LAYER 11 — ULTRA
        ↓
LAYER 12 — FONDEO FUTURES
        ↓
LAYER 13 — 24/7 / RESILIENCE
```

Si una capa inferior falla, la siguiente queda bloqueada.

---

# 4. PROGRAMA DE REPARACIÓN

## R0 — CONTROL Y REPRODUCIBILIDAD

### Objetivo
Garantizar que cualquier agente sabe exactamente qué repositorio, commit, orden y entorno está trabajando.

### Revisar

```text
Git remote
main
working tree
control files
order genealogy
dispatch uniqueness
commit provenance
```

### Salida

```text
CONTROL_GREEN
```

### Bloqueadores

```text
remote mismatch
stale order
multiple active orders
local-only control state
```

---

# R1 — ARRANQUE DEL REPOSITORIO

### Objetivo
La aplicación debe instalar y arrancar desde cero en un entorno limpio.

### Web

```text
npm ci
npm --workspace apps/web run typecheck
npm --workspace apps/web run build
npm --workspace apps/web run dev
```

### API

```text
Python environment
imports
FastAPI startup
DB initialization
health endpoint
```

### Evidencia

```text
node version
npm version
python version
install output
build output
startup output
HTTP status
```

### Regla
No se permite usar `node_modules` heredado ni artefactos del PC del desarrollador para declarar éxito.

---

# R2 — DEPENDENCIAS Y CONFIGURACIÓN

### Objetivo
Eliminar dependencia accidental del entorno.

### Auditar

```text
package.json
package-lock.json
pyproject / requirements
.env.example
Next config
PostCSS
Tailwind
TypeScript
path aliases
ports
CORS
API proxy
platform-specific dependencies
```

### Comprobaciones

```text
Windows paths = 0
machine-specific paths = 0
undeclared runtime deps = 0
untracked required env vars = 0
```

---

# R3 — API Y BASE DE DATOS

### Objetivo
La API debe devolver estados reales y fallar honestamente.

### Auditar

```text
FastAPI routers
Pydantic contracts
SQLite schema
migrations
DB initialization
404 / 422 / 500 semantics
health endpoints
```

### Prohibiciones

```text
fake success
empty-object success
silent exception swallowing
fabricated metrics
fallback certification
```

### Regla
Si el backend no puede obtener evidencia, devuelve:

```text
NO_EVIDENCE
UNAVAILABLE
BLOCKED
```

según el caso.

---

# R4 — DATA / DATASET CHAIN OF CUSTODY

### Objetivo
Todo backtest y certificación deben comenzar en un dataset identificable y físicamente verificable.

### Debe existir

```text
dataset_id
type
venue
instrument_id
timeframe_id
start/end
record count
raw source
raw hash
normalized hash
manifest
coverage
gap count
duplicate count
ordering
```

### Prohibiciones

```text
synthetic dataset
fake hash
missing source
silent fallback
fuzzy instrument replacement
```

---

# R5 — CANONICAL STRATEGY Y VERSIONADO

### Objetivo
Una estrategia debe tener una sola representación canónica.

### Revisar

```text
strategy_id
strategy_version
strategy_hash
canonical AST
compiler version
execution policy version
lineage
parent hash
mutation hash
```

### Regla
Una nueva versión nunca hereda certificación automáticamente.

---

# R6 — EXECUTION FABRIC

### Objetivo
La estrategia canónica debe convertirse en ejecución determinista sin reinterpretación oculta.

### Debe demostrarse

```text
LONG
SHORT
BOTH
entry
exit
SL
TP
trailing
session
EOD
sizing
risk
fees
slippage
fills
positions
```

### Cadena obligatoria

```text
CanonicalStrategy
→ ExecutableInstruction
→ Runtime Adapter
→ Universal Engine
→ Event Stream
→ Execution Ledger
→ Metrics
```

No se acepta un adaptador de prueba que nunca llegue al engine real.

---

# R7 — LEDGER / MÉTRICAS / EVIDENCE

### Objetivo
Toda métrica visible debe derivar de una evidencia física.

### Debe poder reproducirse

```text
same strategy hash
+ same dataset hash
+ same engine version
+ same execution policy
= same ledger hash
= same metrics
```

### Revisar

```text
determinism
hashes
trade ledger
equity curve
PF
ROI
DD
Sharpe
OOS
```

---

# R8 — VALIDATION / GATES

### Objetivo
Que los gates sean compuertas reales y no decoración.

### Cada gate necesita

```text
input
rule
threshold
observed value
PASS/FAIL/BLOCKED/NO_EVIDENCE
evidence reference
evidence hash
run id
policy version
```

Un gate sin evidencia no es PASS.

---

# R9 — WEB / UI / PROVENANCE

### Objetivo
La web se convierte en renderer de la realidad del backend.

### Principio

```text
UI ≠ cálculo cuantitativo
UI ≠ certificación
UI ≠ generación de resultados
```

### Debe hacer

```text
fetch canonical API
render status
render evidence
render provenance
render failures honestly
```

### Prohibido

```text
candidate → approved fallback
PF > X → certified
hardcoded dataset
hardcoded hash
fake KPI
synthetic equity curve
fallback capital
fallback timestamps
```

---

# R10 — API / UI CONTRACT TESTING

### Objetivo
Evitar que backend y frontend evolucionen por separado.

### Añadir

```text
contract tests
response schema tests
status semantics tests
404/422 tests
NO_EVIDENCE tests
certification state tests
```

Cada modificación del contrato debe romper CI si la UI no puede consumirlo.

---

# R11 — DISCOVERY FACTORY

Sólo después de R0–R10 verdes.

Aquí comienza el laboratorio inteligente descrito en el plan maestro:

```text
SQX
→ campaigns
→ fast filter
→ Discovery Score
→ Strategy Genome
→ clustering
→ diversity
→ trial accounting
→ OOS
→ robustness
→ research
```

### Objetivo
Buscar familias de edge, no simplemente la estrategia con mayor ROI.

### Debe existir

```text
candidate
promising
research
incubation
certified
```

separados.

---

# R12 — RESEARCH / LEARNING LOOP

### Objetivo
Aprender qué búsquedas generan evidencia robusta.

### El sistema aprende

```text
fertility
novelty
robustness
regime survival
execution survival
mutation success
family success
```

### No aprende

```text
“esta estrategia tuvo +500%, genera más iguales”
```

---

# R13 — PORTFOLIO / META-STRATEGY

### Objetivo
Explorar combinaciones después de demostrar estrategias individuales y su procedencia.

### Debe medir

```text
correlation
tail correlation
drawdown concurrence
exposure overlap
risk budget
combined ledger
portfolio hash
```

Nunca:

```text
average returns
```
como sustituto del backtest combinado real.

---

# R14 — ULTRA

### Universo
Registry-driven, sin hard-code de cripto ni temporalidad.

### Objetivo
Investigar asimetría extrema, incluyendo estrategias capaces de superar +1000% **si los datos y la evidencia lo permiten**.

### Nunca

```text
forzar +1000%
seleccionar sólo ganadoras
recortar drawdowns ficticiamente
modificar costes para llegar al target
```

`+1000%` sólo aparece como resultado observado de una ejecución válida.

---

# R15 — FONDEO FUTURES

### Universo
**SOLO FUTUROS.**

### Separar

```text
EVALUATION
FUNDED
```

### Evaluation
Optimizar:

```text
P(pass)
expected attempts
expected evaluation cost
time to target
breach probability
```

### Funded
Optimizar:

```text
risk of ruin
payout survival
daily loss
trailing/static DD
consistency
exposure
```

### Registry obligatorio

```text
firm
product
account
rules
instrument list
session
news
overnight
daily loss
max loss
profit target
consistency
payout
cost
policy version
effective dates
source hash
```

---

# R16 — 24/7 / RESILIENCE

Sólo después de estabilizar el sistema.

### Debe tener

```text
durable jobs
leases
heartbeat
checkpoint
idempotency
retry
dead letter
watchdog
restart
recovery
remote evidence
```

Una caída no puede duplicar ejecuciones ni perder el lineage.

---

# 5. ORDEN DE REPARACIÓN ACTUAL

La primera orden vigente es `AG2-RECOVERY-001`.

Debe cerrar primero:

```text
R0
R1
R2
R3
R9
R10
```

No pasar todavía a Discovery, Ultra o Fondeo.

Después de la revisión de Recovery-001, ChatGPT decide el siguiente bloque exacto.

---

# 6. MÉTODO DE CADA ORDEN

Cada nueva orden debe contener obligatoriamente:

```text
OBJECTIVE
WHY
SCOPE
OUT OF SCOPE
SUBAGENTS
STEP-BY-STEP PLAN
FILES / MODULES
TEST PLAN
EXPECTED EVIDENCE
FAIL CONDITIONS
DELIVERY FORMAT
STOP CONDITION
```

### Para tareas complejas

Antigravity debe trabajar así:

```text
SUBAGENTS
↓
RECONCILIATION
↓
IMPLEMENTATION
↓
INDEPENDENT VERIFICATION
↓
TESTS
↓
RED TEAM
↓
EVIDENCE PACKAGE
```

No aceptar “hecho” basado sólo en el mensaje del agente.

---

# 7. CRITERIO DE PROGRESO

No mediremos progreso por:

```text
número de commits
número de tests verdes
número de archivos modificados
```

Se mide por:

```text
BLOCKERS CLOSED
CONTRACTS PROVEN
REAL EXECUTION PROVEN
DATA PROVEN
PROVENANCE PROVEN
REPRODUCIBILITY PROVEN
UI HONEST
```

---

# 8. MATRIZ DE ESTADOS

Cada componente debe poder estar en:

```text
UNKNOWN
AUDITING
BROKEN
REPAIRING
PROVEN
BLOCKED
DEFERRED
CERTIFIED_CURRENT
STALE
```

Nunca usar:

```text
GREEN
DONE
100%
```

sin evidencia asociada.

---

# 9. NO REGRESIÓN

Antes de cerrar cada orden:

```text
TESTS DE CAPA MODIFICADA
+
TESTS DE CAPAS DEPENDIENTES
+
SMOKE TEST
+
GIT PARITY
```

Una reparación que rompe otra capa no se acepta como reparación.

---

# 10. CICLO CONTINUO

El programa no termina cuando localhost funciona.

Después de estabilizar la aplicación:

```text
STARTUP
→ DATA
→ CANONICAL
→ ENGINE
→ EVIDENCE
→ WEB
→ DISCOVERY
→ RESEARCH
→ PORTFOLIO
→ ULTRA
→ FONDEO
→ 24/7
```

Cada nueva funcionalidad vuelve a pasar por la misma cadena de evidencia.

---

# 11. REGLA FINAL

> **Nunca arreglar para que parezca funcionar. Arreglar hasta que pueda demostrarse que funciona.**

Y:

> **Cada resultado cuantitativo debe poder contestar: qué estrategia, qué versión, qué datos, qué engine, qué costes, qué policy, qué ledger y qué evidencia lo produjeron.**
