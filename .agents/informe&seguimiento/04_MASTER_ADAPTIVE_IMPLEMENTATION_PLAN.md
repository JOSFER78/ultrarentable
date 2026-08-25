# ULTRARENTABLE — MASTER ADAPTIVE IMPLEMENTATION PLAN
## Plan maestro científico, técnico y operativo para Antigravity 2.0

**Proyecto:** `JOSFER78/ultrarentable`  
**Control operativo:** `.agents/informe&seguimiento/`  
**Watcher:** Antigravity 2.0 aproximadamente cada 3 minutos  
**Modelo:** una fase/orden activa, evidencia, auditoría externa, siguiente orden  
**Doctrina:** REAL-ONLY · ZERO-MOCK · ZERO-SIMULATION · ZERO-FORCING · ZERO-LOOKAHEAD · EVIDENCE-GATED

> **MUY IMPORTANTE:** este documento es el plan maestro. No autoriza por sí mismo la ejecución de ninguna fase. La única fase ejecutable es la que figure en `01_CONTROL_STATE.md` y en `02_CURRENT_ORDER.md`.

---

# 0. MISIÓN REAL DE ULTRARENTABLE

ULTRARENTABLE no tiene como objetivo fabricar curvas bonitas ni acumular estrategias con alto ROI de backtest.

Tiene dos laboratorios de investigación claramente separados:

```text
                    ULTRARENTABLE
                          │
             ┌────────────┴────────────┐
             │                         │
          TRACK ULTRA              TRACK FONDEO
             │                         │
     TODOS LOS ACTIVOS            SOLO FUTUROS
     Y TEMPORALIDADES              DE PROP FIRMS
             │                         │
     ASIMETRÍA / CONVEXIDAD        APROBAR + COBRAR
             │                         │
       +1000% objetivo              Sprint rápido
       de investigación             bajo reglas reales
```

## ULTRA

Buscar de forma agresiva, pero científicamente, estrategias/campañas capaces de producir resultados extremos y asimétricos, incluyendo la posibilidad de **+1000% o más**, siempre que sobrevivan datos reales, costes, slippage, OOS, robustez, régimen, ejecución y riesgo de ruina apropiado.

`+1000%` es un **objetivo de investigación**, nunca una condición que permita relajar filtros.

## FONDEO

Buscar estrategias exclusivamente para **evaluaciones y cuentas fondeadas de futuros**.

Nada de Forex/CFD/cripto dentro del track FONDEO.

El sistema debe ser capaz de trabajar con los futuros permitidos por cada firma/producto/política vigente y seleccionar riesgo para maximizar la probabilidad de aprobar rápidamente sin confundir el riesgo de una evaluación barata con el riesgo de una cuenta ya fondeada.

---

# 1. REGLA ABSOLUTA: ANTIGRAVITY NO AVANZA SOLO

El sistema de desarrollo funciona así:

```text
CHATGPT / AUDITOR EXTERNO
        │
        ▼
AUDITA REPOSITORIO + EVIDENCIA
        │
        ├── APPROVE
        ├── REJECT
        ├── BLOCK
        └── REDESIGN
        │
        ▼
PUBLICA NUEVO CONTROL / ORDEN
        │
        ▼
CRON DE ANTIGRAVITY (~3 min)
        │
        ▼
ANTIGRAVITY 2.0 ORQUESTA SUBAGENTES
        │
        ▼
IMPLEMENTA / TESTEA / DOCUMENTA
        │
        ▼
HANDOFF + EVIDENCIA
        │
        ▼
STOP ABSOLUTO
        │
        └──────────────→ NUEVA AUDITORÍA
```

Antigravity nunca puede:

- aprobar su propia fase;
- cambiar `CURRENT_PHASE` hacia delante;
- emitir certificación final por sí mismo;
- inventar evidencia;
- crear una estrategia ficticia para demostrar que el laboratorio funciona;
- suavizar gates porque sobreviven pocos candidatos;
- utilizar el holdout para diseñar una mutación y después certificarla con el mismo holdout;
- ejecutar una fase futura “para adelantar trabajo”.

---

# 2. EL CRON DE 3 MINUTOS

El watcher de Antigravity no es un planificador autónomo. Es un **detector de órdenes**.

Cada ciclo:

```text
1. leer .agents/informe&seguimiento/
2. leer 00_CONTROL_PROTOCOL.md
3. leer 01_CONTROL_STATE.md
4. leer 02_CURRENT_ORDER.md
5. comprobar order_id + issued_at
6. si no existe una orden nueva → no inventar trabajo
7. si existe → ACKNOWLEDGED
8. ejecutar exclusivamente la orden
9. usar subagentes
10. generar HANDOFF
11. marcar READY_FOR_REVIEW o BLOCKED
12. STOP
```

Debe existir siempre exactamente **una orden activa**.

---

# 3. ANTIGRAVITY 2.0 COMO ORQUESTADOR MULTIAGENTE

Antigravity no debe actuar como un programador monolítico.

Para cada fase debe:

```text
DEFINIR SUBTAREAS
→ ASIGNAR SUBAGENTES
→ INVESTIGAR EN PARALELO
→ RECONCILIAR DISCREPANCIAS
→ IMPLEMENTAR
→ HACER VERIFICAR POR OTROS SUBAGENTES
→ EJECUTAR TESTS REALES
→ EMPAQUETAR EVIDENCIA
→ STOP
```

## Roles disponibles

### RECON / ARCHITECTURE
Mapea código, contratos, dependencias, rutas y fuentes de verdad.

### QUANT ENGINE
Audita cálculo, eventos, costes, sizing, fills, ledger y determinismo.

### DATA / EVIDENCE
Comprueba datasets, snapshots, hashes, procedencia y separación temporal.

### VALIDATION / GATES
Audita los 11 gates y sus evidencias.

### VERSION / CERTIFICATION
Comprueba lineage, hashes, policy versions y expiración de certificaciones.

### DISCOVERY RESEARCH
Genome, clustering, campañas, fertility, exploration/exploitation, trial accounting.

### RESEARCH / REPROGRAMMING
Autopsias, hipótesis, mutaciones, experimentos y revalidación ciega.

### RED TEAM / OVERFITTING GUARDIAN
Busca bypasses, mocks, leakage, selección múltiple, lookahead y falsos positivos.

### LEARNING / FIREBASE
Recuperación de memoria histórica y LearningStore.

### RELIABILITY / 24x7
Jobs, leases, heartbeat, checkpoint, retry, idempotency, watchdog y resume.

### UI / API PROVENANCE
Comprueba que UI es renderer y que todos los datos visibles tienen origen canónico.

Ningún subagente que implemente una propiedad puede ser el único verificador de esa misma propiedad.

---

# 4. ARQUITECTURA DE LA WEB: ANTI-ROT

La aplicación debe estabilizarse como una plataforma duradera antes de seguir añadiendo funcionalidades.

## Objetivo

```text
ONE DOMAIN MODEL
ONE STRATEGY SSOT
ONE VERSION LINEAGE
ONE EXECUTION FABRIC
ONE EVIDENCE CHAIN
ONE LEARNING STORE
ONE POLICY SYSTEM
ONE API AUTHORITY
ONE UI RENDERER
```

## Prohibiciones

- duplicar cálculos entre páginas;
- duplicar estrategia en frontend y backend;
- hardcodear métricas en UI;
- hardcodear activos o temporalidades en lógica central;
- hardcodear rulesets de firmas;
- endpoint que rellena missing values;
- certificación inferida por color/card/score de UI;
- página que presente una certificación vieja como actual;
- estados globales desconectados del backend canónico;
- migrations informales;
- schema sin versionado;
- rutas huérfanas o módulos muertos que parezcan parte del sistema.

## Capas

```text
UI
 ↓
Canonical API
 ↓
Domain / Evidence
 ↓
Validation / Portfolio / Research
 ↓
Execution Fabric
 ↓
Universal Engine
 ↓
Real Data
```

La UI no debe tener lógica de certificación.

---

# 5. SINGLE SOURCE OF TRUTH

## Estrategia

```text
strategy_id
strategy_version
strategy_hash
```

## Dataset

```text
data_snapshot_id
data_source_id
instrument_id
timeframe_id
session_policy_id
data_sha256
coverage_manifest
```

## Ejecución

```text
execution_bundle_id
engine_version
execution_policy_version
ledger_hash
```

## Validación

```text
validation_run_id
gate_policy_version
evidence_bundle_id
```

## Certificación

```text
certification_snapshot_hash
policy_version
status
```

---

# 6. VERSIONADO: NUNCA SOBRESCRIBIR UNA ESTRATEGIA

Ejemplo:

```text
SQX strategy v1
       │
       ├── Research mutation → v2
       ├── Execution repair  → v3
       ├── Regime repair     → v4
       └── Current candidate → v5
```

Una nueva versión no hereda la certificación del padre.

Debe volver a pasar por:

```text
CANONICAL STRATEGY
→ CURRENT ENGINE
→ CURRENT DATA POLICY
→ CURRENT EXECUTION POLICY
→ CURRENT VALIDATION
→ CURRENT GATES
→ NEW EVIDENCE
```

## Cambio material = invalidación potencial

```text
strategy rules       → full revalidation
AST/compiler         → full revalidation
engine               → affected evidence invalidated
execution/cost       → affected evidence invalidated
risk                 → risk revalidation
data policy          → affected data validation
Gates                → policy re-evaluation
portfolio logic      → affected meta evidence invalidated
UI only              → no quantitative invalidation
```

Estados visibles:

```text
CERTIFIED_CURRENT
CERTIFIED_LEGACY
STALE
REVALIDATION_REQUIRED
REVALIDATING
FAILED_CURRENT_POLICY
```

---

# 7. UNIVERSO DE MERCADOS — CERO HARD-CODING

## 7.1 ULTRA: UNIVERSO GLOBAL CONFIGURABLE

ULTRA no queda restringido a criptomonedas, Forex ni a una lista cerrada de símbolos.

La investigación debe poder incorporar cualquier instrumento para el que exista:

1. una fuente de datos real aprobada;
2. un instrumento identificable;
3. histórico suficiente;
4. modelo de ejecución/costes razonable;
5. reglas de mercado conocidas;
6. capacidad de reproducir el resultado.

La registry debe soportar categorías como:

```text
Forex
Futuros
Índices
Commodities
Metales
Energía
Cripto spot/perpetual
Rates/Bonds
ETFs u otros instrumentos compatibles
Cross-asset relationships
```

Las temporalidades también son **registry-driven**, no hardcoded.

El motor puede soportar desde granularidad intradía hasta diaria/semanal cuando el dataset y el engine lo permitan.

Nuevo mercado/timeframe = nueva entrada de registry + dataset manifest + policy + tests, no nueva rama de código escondida.

## 7.2 FONDEO: SOLO FUTUROS

El track FONDEO queda exclusivamente limitado a futuros.

Ejemplos de familias posibles, siempre sujetos a la política real de la empresa/firma:

```text
Equity Index Futures
NQ / MNQ
ES / MES
YM / MYM
RTY / M2K

Energy
CL / MCL
NG / otros si la firma los permite

Metals
GC / MGC
SI / otros si la firma los permite

Rates / Treasury Futures
según producto permitido

FX Futures
6E / 6B / 6J / etc., cuando la firma los permita

Otros CME/mercados regulados
según policy actual
```

**No incluir en FONDEO:**

```text
Forex spot/CFD
Crypto perpetuals
CFDs
```

El sistema no debe hardcodear “NQ/ES solamente”. Debe tener un **Futures Instrument Registry** y un **Firm Policy Registry**.

---

# 8. FONDEO: EL MODELO CORRECTO DE RIESGO

La evaluación y la cuenta fondeada son dos problemas diferentes.

```text
             FONDEO
                │
       ┌────────┴────────┐
       │                 │
   EVALUACIÓN         FUNDED
       │                 │
 riesgo agresivo      riesgo defensivo
 para maximizar       para preservar
 probabilidad de      capital y payouts
 aprobación           reales
```

## Evaluación

Como el coste de una evaluación puede ser pequeño respecto al capital nominal anunciado por la firma, el sistema debe poder estudiar una política **agresiva pero bounded** para intentar aprobar rápidamente.

No se utilizará un número fijo universal como “80 €” para el algoritmo. El coste real de la evaluación será un parámetro económico de la cuenta.

El sistema puede comparar:

```text
coste de evaluación
probabilidad de aprobar
expected number of attempts
expected cost of failures
probabilidad de breach
tiempo esperado para aprobar
```

El objetivo es maximizar la **probabilidad/eficiencia de aprobación**, no simplemente sobrevivir durante meses sin acercarse al target.

## Funded

Una estrategia que pasa una evaluación con riesgo extremo puede ser inadecuada después.

La cuenta fondeada necesita otra política:

```text
preservar drawdown
preservar payout eligibility
reducir risk-of-ruin
adaptar sizing
cumplir consistencia
cumplir daily loss
cumplir trailing/static drawdown
```

El mismo strategy_hash puede tener dos **risk policy contexts**:

```text
EVALUATION_POLICY
FUNDED_POLICY
```

pero la estrategia no cambia silenciosamente.

---

# 9. FONDEO: POLÍTICAS POR FIRMA, CUENTA Y FECHA

Nunca existirán reglas universales de “fondeo”.

Registry mínima:

```text
firm_id
firm_name
product_id
account_type
account_size
platform
instrument_registry
session_policy
news_policy
overnight_policy
weekend_policy
position_limit
margin_policy
daily_loss_policy
max_loss_policy
trailing/static_drawdown
profit_target
consistency_rule
minimum_days
payout_policy
reset/cancel policy
cost
fee
policy_version
effective_from
effective_to
source_url
source_retrieved_at
source_hash
```

Antes de validar una estrategia de FONDEO el sistema debe resolver:

```text
FIRM
+ PRODUCT
+ ACCOUNT
+ DATE
→ APPLICABLE POLICY
```

Una estrategia puede ser:

```text
PASS en firm A / account X / policy v3
FAIL en firm B / account Y / policy v7
```

Eso no es una contradicción: son contratos distintos.

---

# 10. OBJETIVO FONDEO: APROBAR RÁPIDO SIN CONFUNDIR “APROBAR” CON “GANAR”

El laboratorio debe estudiar especialmente la probabilidad de completar una evaluación en ventanas cortas como:

```text
1 día
2 días
3 días
4 días
5 días
```

pero no debe tratar “5 días” como obligación universal.

La suficiencia de una muestra depende de:

```text
elapsed time
closed trades
signal opportunities
market regime coverage
execution observations
rule compliance
```

El sistema puede extender la investigación si la muestra es insuficiente.

Nunca acorta la muestra porque el backtest sea bonito.

---

# 11. FONDEO: RIESGO ADAPTATIVO PARA EVALUACIÓN

La investigación puede comparar perfiles de riesgo:

```text
LOW
MEDIUM
AGGRESSIVE
VERY_AGGRESSIVE
```

El algoritmo debe optimizar una función que combine:

```text
P(pass)
×
P(survive)
×
P(payout | pass)
−
expected evaluation cost
−
expected breach cost
```

Sujeto a las reglas reales de la cuenta.

**Nunca utilizar un riesgo superior al permitido por el contrato.**

La agresividad debe provenir de la asignación y timing de riesgo permitidos, no de violar reglas.

---

# 12. DISCOVERY FACTORY — EL GRAN CAMBIO ESTRUCTURAL

No hacer:

```text
GENERATE
→ FILTER
→ REPAIR
```

Hacer:

```text
GENERATE
→ DIVERSIFY
→ DISCOVER
→ CHEAP SCREEN
→ BACKTEST
→ DISCOVERY SCORE
→ CLUSTER
→ SELECT
→ VALIDATE
→ ROBUSTNESS
→ RESEARCH
→ MUTATE
→ RE-DISCOVER
→ LEARN
```

## Discovery Score

Debe existir separado de Certification.

Conceptualmente:

```text
research_value =
 edge
 + robustness
 + novelty
 + cross-regime survival
 + execution survival
 + portfolio value
 - complexity
 - trial burden
 - fragility
 - concentration
 - evidence gaps
```

La fórmula exacta debe evolucionar con evidencia, pero nunca convertirse en “ROI ranking”.

---

# 13. STRATEGY GENOME

Cada estrategia debe poseer un fingerprint que permita saber si se están descubriendo ideas nuevas o 100.000 variaciones del mismo sistema.

Dimensiones posibles:

```text
entry family
exit family
trend logic
mean reversion logic
breakout logic
volatility logic
holding time
market
instrument
session
risk profile
leverage profile
pyramiding profile
regime affinity
trade distribution
equity shape
drawdown shape
return concentration
exposure fingerprint
correlation fingerprint
```

Se utiliza para:

- deduplicación;
- clustering;
- novelty;
- research budget;
- exploration/exploitation;
- family analysis.

No para certificar directamente.

---

# 14. CAMPAÑAS DE DESCUBRIMIENTO

El motor debe dividir la búsqueda en campañas especializadas.

## ULTRA / GENERAL

```text
Trend
Breakout
Momentum
Mean Reversion
Volatility
Regime
Session
Microstructure
Cross-Asset
Lead-Lag
Relative Strength
Convexity
Campaign mechanics
Tail capture
```

El sistema puede descubrir nuevas familias.

## FONDEO / FUTURES ONLY

```text
Index trend
Index breakout
Opening range
Momentum
Mean reversion
Volatility expansion
RTH session behavior
Overnight-to-RTH relationships
Macro/event response
Futures term/relative relationships where data supports them
Cross-contract relationships
Trend + pullback
Range / breakout transition
```

No campañas de FX spot ni cripto dentro del track FONDEO.

---

# 15. EXPLORATION VS EXPLOITATION

La fábrica debe mantener dos presupuestos:

```text
EXPLOIT
→ profundizar donde existe fertility real

EXPLORE
→ buscar familias nuevas
```

Un reparto inicial puede comenzar, por ejemplo, en 70/30, pero nunca es una constante sagrada.

Debe aprender:

```text
fertility
quality
novelty
robustness
cost
```

La familia más rentable no debe monopolizar el laboratorio si empieza a generar near-duplicates.

---

# 16. TRIAL ACCOUNTING

Cada búsqueda importante debe registrar:

```text
trial_id
campaign_id
family_id
strategy_version
parameter_space
market
instrument
timeframe
dataset_snapshot
research_iteration
parent_hash
outcome
```

Esto evita el problema:

> “esta estrategia ganó, pero no sabemos cuántas miles de pruebas hubo para encontrarla”.

El trial count debe formar parte de la evaluación de evidencia.

---

# 17. FILTRO EN CASCADA

No lanzar los análisis más caros sobre todos los candidatos.

```text
LEVEL 0
syntax / schema / data sanity
        ↓
LEVEL 1
cheap risk / signal sanity
        ↓
LEVEL 2
basic statistics
        ↓
LEVEL 3
full deterministic backtest
        ↓
LEVEL 4
OOS / WFO / robustness
        ↓
LEVEL 5
heavy gates
        ↓
LEVEL 6
research / mutation
```

Ningún nivel modifica la estrategia silenciosamente.

---

# 18. RESEARCH LAB

Una estrategia que falla no desaparece sin más.

Debe producir:

```text
failure
→ root-cause hypothesis
→ research proposal
→ experiment
→ immutable child version
→ independent evaluation
→ result
→ learning event
```

## Agentes especializados

```text
Quant Researcher
Strategy Engineer
Regime Specialist
Execution Specialist
Robustness Scientist
Adversarial Researcher
Overfitting Guardian
Failure-Knowledge Analyst
```

Nunca editar directamente una versión certificada.

---

# 19. BLIND RESEARCH

Los agentes que diseñan una mutación no deben disponer del resultado exacto del holdout que después certificará la versión.

Proceso:

```text
STRUCTURAL DIAGNOSTICS
→ HYPOTHESIS
→ PROPOSAL FREEZE
→ IMMUTABLE CHILD
→ INDEPENDENT OOS
→ GATES
→ RESULT
```

Una mutación jamás reutiliza la evidencia de su padre como su propia evidencia.

---

# 20. ROBUSTNESS / FRAGILITY

Cada estrategia deberá estudiar sensibilidad a:

```text
parameter changes
execution costs
spread
slippage
latency
missed trades
fill degradation
regimes
OOS decay
trade omissions
```

Construir:

```text
Parameter Stability Map
Fragility Score
Execution Degradation Curve
Regime Survival Matrix
```

Objetivo:

```text
BROAD ROBUST REGION
```

No:

```text
PERFECT SINGLE PARAMETER PEAK
```

---

# 21. VALIDACIÓN Y 11 GATES

Los 11 Gates son una fabric de evidencia independiente de la IA.

Deben utilizar configuración canónica y registrar:

```text
gate_id
policy_version
input evidence
calculation
threshold
PASS
FAIL
BLOCKED
NO_EVIDENCE
```

Ningún Discovery Score puede saltarse un gate.

El número exacto, fórmula y aplicabilidad de cada gate deben provenir de la política canónica actual de ULTRA/FONDEO y quedar versionados.

---

# 22. OOS, WFO Y MULTIPLE TESTING

Validación mínima de investigación:

```text
IS
→ WFO
→ múltiple OOS temporal
→ robustez
→ blind holdout
```

Cuando corresponda incorporar:

```text
purging
embargo
Monte Carlo sobre resultados reales
multiple-testing accounting
Deflated Sharpe / otras medidas apropiadas
```

No se certificará una estrategia porque haya “pasado un WFO”.

---

# 23. METAESTRATEGIAS

La metaestrategia es otro laboratorio de descubrimiento.

Puede investigar:

```text
candidate
promising
incubation
certified
```

pero los estados deben permanecer separados.

Para cada combinación evaluar:

```text
correlation
 tail correlation
drawdown concurrence
exposure overlap
risk contribution
margin
capital efficiency
regime diversification
failure concentration
```

## ULTRA meta-strategy

Objetivo potencial:

```text
preservar convexidad
capturar tails
reducir probabilidad de ruina agregada
mejorar capital efficiency
```

No simplemente “sumar ROI”.

## FONDEO meta-strategy

Solo futuros.

Debe buscar combinaciones de estrategias de futuros que:

```text
maximicen probabilidad de aprobar
reduzcan probabilidad de breach
respeten daily loss
respeten trailing/static drawdown
controlen exposición simultánea
permitan cumplir target en una ventana razonable
```

Una metaestrategia no puede convertir una estrategia rechazada en certificada.

---

# 24. ULTRA +1000%: CÓMO PERSEGUIRLO CORRECTAMENTE

La búsqueda de +1000% debe estar presente como objetivo explícito del laboratorio, pero nunca como manipulación de métricas.

La fábrica debe buscar mecanismos que puedan crear asimetría auténtica:

```text
small loss distribution
large right-tail winners
convex payoff
trend acceleration
volatility expansion
campaign persistence
asymmetric exits
ratchet/harvest
multi-asset opportunities
```

La pregunta es:

```text
¿existe una familia que produzca grandes ganancias repetibles
sin depender de un solo evento histórico?
```

Debe evaluarse:

```text
profit concentration
number of independent campaigns
tail contribution
OOS tail survival
execution sensitivity
regime dependency
ruin probability
```

Un único trade de +1000% no convierte una estrategia en ULTRA robusta.

---

# 25. FONDEO FUTURES: MAXIMIZAR LA APROBACIÓN

El objetivo del laboratorio de FONDEO no es construir estrategias “bonitas” de bajo riesgo.

Es investigar el equilibrio óptimo entre:

```text
agresividad
probabilidad de alcanzar target
probabilidad de breach
coste de evaluación
número esperado de intentos
tiempo de aprobación
```

Durante evaluación puede existir una política de riesgo agresiva dentro de las reglas de la firma.

Después de pasar:

```text
risk policy changes
position size changes
payout preservation becomes dominant
```

Esto permite que el sistema busque **estrategias de evaluación agresivas y estrategias funded defensivas** sin cambiar la identidad de la estrategia subyacente.

---

# 26. FORWARD / PAPER INCUBATION

Antes de permitir despliegue con capital real:

```text
BACKTEST
→ OOS
→ ROBUSTNESS
→ CURRENT CERTIFICATION
→ PAPER FORWARD
→ OBSERVED EXECUTION
→ LIVE-COMPATIBILITY REVIEW
```

Los paper trades deben provenir del feed/pipeline real.

Si el feed no existe:

`BLOCKED / NO_EVIDENCE`.

Nunca inventar fills de paper.

---

# 27. APRENDIZAJE PERSISTENTE

El aprendizaje no puede ser una blacklist simple.

Modelo mínimo:

```text
strategy_versions
validation_snapshots
failure_records
research_proposals
research_experiments
agent_debates
mutation_history
sqx_feedback
revalidation_queue
learning_patterns
knowledge_links
```

Debe recordar:

```text
qué falló
por qué falló
en qué régimen
qué mutación se intentó
qué coste añadió
qué resultado produjo
qué familias son fértiles
qué familias son frágiles
qué campañas generan near-duplicates
```

Si existe Firebase histórico, primero recuperación forense:

```text
NO WRITE
→ locate project/config
→ enumerate collections
→ snapshot
→ reconcile
→ rehydrate
→ mark ambiguous UNVERIFIED
→ only then enable new writes
```

---

# 28. 24/7 RESILIENTE

La operación continua debe ser resistente a roturas.

Componentes:

```text
SUPERVISOR
DURABLE QUEUE
JOB ID
LEASE
HEARTBEAT
CHECKPOINT
RETRY
IDEMPOTENCY
WATCHDOG
RESUME
```

Un reinicio de VPS no puede perder una campaña.

Una caída de SQX no debe destruir Research/Gates/Revalidation.

Una caída del frontend no debe detener el laboratorio.

Un worker muerto no puede perder un lote.

---

# 29. OBSERVABILIDAD

Cada proceso importante debe poder responder:

```text
WHAT?
WHY?
WHICH STRATEGY?
WHICH VERSION?
WHICH DATA?
WHICH ENGINE?
WHICH POLICY?
WHICH JOB?
WHICH TRIAL?
WHICH RESULT?
```

Los logs operativos y la UI deben mostrar estados reales:

```text
SUCCESS
INFO
WARN
ERROR
BLOCKED
NO_EVIDENCE
UNVERIFIED
STALE
REVALIDATION_REQUIRED
```

---

# 30. PLAN DE FASES DEFINITIVO

## PHASE 00 — FORENSIC BASELINE / REALITY LOCK

### Objetivo
Establecer la verdad actual antes de modificar arquitectura.

### Debe auditar

- commit/branch/worktree;
- estructura real;
- dependencias;
- runtime;
- datos físicos;
- canonical strategy;
- engine;
- ledger;
- metrics;
- 11 gates;
- current vs legacy;
- UI/API provenance;
- mocks/random/defaults/fallbacks;
- discovery actual;
- trial accounting existente;
- research/mutation;
- 24/7;
- Firebase;
- contradicciones de documentación.

### Salida
`PHASE_00_EXECUTION_REPORT.md`

### NO hacer
No rediseñar todavía.

---

## PHASE 01 — DATA CHAIN OF CUSTODY

### Objetivo
Cada run debe saber exactamente qué bytes de datos utilizó.

### Entregables

- Dataset Registry;
- source metadata;
- instrument registry;
- timeframe registry;
- snapshot manifests;
- hashes;
- UTC normalization;
- duplicate/out-of-order checks;
- missing policy;
- IS/Validation/OOS partitioning;
- immutable data identity.

### FONDEO
Registry exclusivo de futuros y políticas de firmas.

---

## PHASE 02 — CANONICAL STRATEGY + VERSION GOVERNANCE

### Objetivo
CanonicalStrategy es SSOT.

### Entregables

- immutable AST;
- deterministic serialization;
- strategy hash;
- lineage;
- engine/contract versions;
- compatibility matrix;
- invalidation rules;
- current/legacy state.

---

## PHASE 03 — DETERMINISTIC UNIVERSAL EXECUTION ENGINE

### Objetivo
Mismo input bundle = mismo ledger.

### Comprobar

- event ordering;
- next-bar/fill model;
- no-lookahead;
- capital;
- costs;
- spread/slippage;
- margin;
- liquidation;
- ledger hash;
- deterministic rerun.

---

## PHASE 04 — DISCOVERY FACTORY

### Objetivo
Convertir SQX + otras fuentes reales en una fábrica diversificada.

### Entregables

- campaigns;
- Strategy Genome;
- behavioral clustering;
- dedupe;
- trial accounting;
- genealogy;
- Discovery Score;
- research budget;
- fertility;
- exploration/exploitation;
- cascaded screening;
- candidate queue;
- rejection memory.

### FONDEO
Solo futuros.

### ULTRA
Todos los instrumentos registrados y soportados.

---

## PHASE 05 — INDEPENDENT VALIDATION + 11 GATES

### Objetivo
Transformar validación en evidencia independiente de la IA.

### Entregables

- gate evidence records;
- current policies;
- PASS/FAIL/BLOCKED/NO_EVIDENCE;
- multiple-testing accounting;
- exact thresholds versioned;
- track-specific gates.

---

## PHASE 06 — ROBUSTNESS / WFO / PURGED VALIDATION

### Objetivo
Probar que el edge no depende de una isla de parámetros o periodo.

### Entregables

- multiple OOS;
- WFO;
- WFO matrix where supported;
- parameter stability;
- execution stress;
- regime survival;
- Fragility Score;
- degradation curves.

---

## PHASE 07 — RESEARCH + REPROGRAMMING LAB

### Objetivo
Aprender de fallos y crear nuevas versiones sin contaminar OOS.

### Entregables

- research proposals;
- experiments;
- debates;
- immutable child versions;
- blind mutation;
- independent revalidation;
- family-level failure analysis.

---

## PHASE 08 — LEARNING STORE + FIREBASE RECOVERY

### Objetivo
Memoria durable y recuperable.

### Regla
Recuperar antes de recrear.

### Entregables

- canonical LearningStore;
- Firebase recovery if real;
- reconciliation;
- genealogy links;
- fertility history;
- failure relationships;
- learning patterns.

---

## PHASE 09 — PAPER / FORWARD INCUBATION

### Objetivo
Comparar comportamiento esperado y observado con datos/feeds reales.

### Entregables

- forward ledger;
- observed costs;
- latency;
- spread;
- fill quality;
- divergence;
- reconnect handling.

---

## PHASE 10 — FONDEO FUTURES EVALUATION LAB

### SOLO FUTUROS.

### Objetivo
Investigar estrategias y asignaciones que maximicen probabilidad de aprobar evaluaciones rápidamente, respetando la política exacta de cada producto.

### Debe estudiar

- account sizes;
- futures instrument universe;
- evaluation cost;
- profit target;
- daily loss;
- max/trailing loss;
- position limits;
- session rules;
- news rules;
- overnight/weekend rules;
- consistency;
- minimum-day rules;
- payout conditions;
- attempt economics.

### Objetivo de riesgo

Permitir investigación agresiva durante evaluación **dentro de las reglas reales**.

Estudiar específicamente ventanas cortas de 1–5 días cuando la estructura de la firma lo permita, pero sin falsear suficiencia estadística.

---

## PHASE 11 — FONDEO FUNDED / PRESERVATION LAB

### SOLO FUTUROS.

### Objetivo
Separar la política de “pasar” de la política de “conservar y cobrar”.

### Debe optimizar

- payout survival;
- drawdown preservation;
- daily loss preservation;
- consistency;
- reduced ruin;
- dynamic sizing;
- capital efficiency.

No confundir un sprint de evaluación con una estrategia de operación conservadora después del fondeo.

---

## PHASE 12 — ULTRA BULLET / CONVEXITY LAB

### Objetivo
Buscar asimetría extrema y estrategias/campañas capaces de alcanzar retornos potenciales de +1000% o más.

### Debe estudiar

- bullets independientes;
- convexity;
- tail capture;
- volatility expansion;
- momentum acceleration;
- campaign mechanics;
- asymmetric exits;
- harvest/ratchet;
- pyramiding where policy permits;
- multi-asset opportunities;
- risk of ruin.

### Resultado esperado

No una promesa de +1000%.

Una demostración reproducible, si existe, de que una familia puede producir retornos extremos sin que desaparezcan bajo validación hostil.

---

## PHASE 13 — META-STRATEGY / PORTFOLIO DISCOVERY

### Objetivo
Convertir diversificación real en otra capa de edge.

### ULTRA
Buscar convexidad agregada, tail diversification y capital efficiency.

### FONDEO
Solo futuros; optimizar probabilidad de aprobar/sobrevivir bajo reglas de la firma.

### Prohibición
Ningún portfolio puede esconder el fracaso de sus componentes.

---

## PHASE 14 — CERTIFICATION + UI + API + CONTINUOUS REVALIDATION

### Objetivo
Que web y backend representen exactamente la realidad.

### Debe garantizar

- UI read-only para certificación;
- canonical API;
- provenance every metric;
- `NO_EVIDENCE` for missing evidence;
- current/legacy visible;
- version lineage visible;
- automatic invalidation on material changes;
- no hardcoded metrics;
- no duplicated quant logic.

---

## PHASE 15 — 24/7 OPERATIONS / SELF-AUDIT / DISASTER RECOVERY

### Objetivo
Mantener el laboratorio funcionando sin permitir que la autonomía rompa la ciencia.

### Entregables

- durable queue;
- scheduler;
- campaign allocator;
- stale evidence detector;
- watchdog;
- job recovery;
- drift detection;
- integrity alerts;
- periodic self-audit;
- disaster recovery;
- immutable operational logs.

Automation may discover and report; it may never silently self-certify.

---

# 31. ADAPTIVE BRANCHING — EL PLAN PUEDE CAMBIAR

Después de cada fase el auditor puede decidir:

```text
APPROVE
→ next phase

REJECT
→ same phase rework

BLOCK
→ missing real dependency

REDESIGN
→ new bounded phase/order

SPLIT
→ phase becomes multiple phases

MERGE
→ two phases become one

ABANDON
→ hypothesis archived
```

Ejemplos:

### Si no hay datos suficientes
No inventar. `BLOCKED`.

### Si todos los candidatos fallan
No bajar gates. Investigar discovery/data/engine.

### Si una familia domina
Aplicar diversity/clustering.

### Si hay muchos near-duplicates
Reasignar discovery budget.

### Si un engine change invalida resultados
Revalidation queue.

### Si Firebase existe
Recuperarlo antes de crear memoria nueva.

### Si la UI contradice backend
Backend/evidence gana.

---

# 32. CRITERIOS DE TERMINACIÓN DEL PROGRAMA

ULTRARENTABLE no se considera terminado porque “hay muchas estrategias”.

Debe poder demostrar:

```text
REAL DATA
→ CANONICAL STRATEGY
→ CURRENT ENGINE
→ DETERMINISTIC LEDGER
→ METRICS
→ VALIDATION
→ GATES
→ EVIDENCE
→ CERTIFICATION
→ API
→ UI
```

y además:

```text
CHANGE ENGINE
→ OLD CERTIFICATION BECOMES STALE
→ REVALIDATION REQUIRED
```

Discovery must demonstrate:

```text
campaigns
+ genome
+ diversity
+ trials
+ fertility
+ research learning
```

FONDEO must demonstrate:

```text
FUTURES ONLY
+ firm-specific policies
+ evaluation optimization
+ funded preservation policy
```

ULTRA must demonstrate:

```text
GLOBAL REGISTRY
+ bullet isolation
+ convexity research
+ +1000% objective
+ hostile validation
```

---

# 33. DEFINICIÓN FINAL DE ÉXITO

```text
SQX = FACTORY

ULTRARENTABLE =
    RESEARCH OPERATING SYSTEM
  + VALIDATION JUDGE
  + VERSION GOVERNANCE
  + LEARNING MEMORY
  + META-STRATEGY LAB
  + 24/7 ORCHESTRATOR

ANTIGRAVITY = EXECUTOR + SUBAGENT ORCHESTRATOR

REPOSITORY = SOURCE OF EXECUTABLE TRUTH

EVIDENCE = PROOF

GATES = DECISION RULES

CHATGPT EXTERNAL REVIEW = PHASE AUTHORITY
```

La regla final es:

> **Antigravity trabaja. Sus subagentes investigan, implementan y verifican. El repositorio produce la evidencia. El laboratorio aprende. ChatGPT audita. Sólo después de la auditoría existe la siguiente orden.**

---

# 34. ORDEN ACTUAL

`CURRENT_PHASE = 00`

`ACTIVE_ORDER = AG2-P00-001`

Hasta que el informe de Fase 00 sea entregado y auditado, ninguna otra fase está autorizada.
