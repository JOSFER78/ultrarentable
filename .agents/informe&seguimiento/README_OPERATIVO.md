# ULTRARENTABLE — CONTROL OPERATIVO ÚNICO

Este directorio es el **centro de mando completo** de Antigravity 2.0 para ULTRARENTABLE.

No debe existir otro sistema paralelo de fases/control que pueda contradecirlo.

## 1. QUÉ ES CADA ARCHIVO

| Archivo | Función | Autoridad |
|---|---|---|
| `00_CONTROL_PROTOCOL.md` | Protocolo operativo permanente: watcher, subagentes, SSH, GitHub, Zero-Simulation | Reglas operativas |
| `01_CONTROL_STATE.md` | Estado vivo de fase/orden | SSOT de estado |
| `02_CURRENT_ORDER.md` | **ÚNICA orden ejecutable ahora** | SSOT de ejecución |
| `03_HANDOFF_TEMPLATE.md` | Formato de entrega de Antigravity | Obligatorio |
| `03_HANDOFF_<order_id>.md` | Resultado real de una orden | Evidencia de entrega |
| `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` | Plan científico/técnico completo y adaptativo | Hoja de ruta |
| `04_REVIEW_<order_id>.md` | Auditoría externa de ChatGPT | Decisión de siguiente trabajo |
| `05_REVIEW_PROTOCOL.md` | Cómo se audita `origin/main` | Contrato de revisión |
| `06_PHASE_01_ORDER_LOCKED.md` | Orden futura preparada, no ejecutable mientras esté LOCKED | Reserva |
| `ULTRARENTABLE_Informe_Maestro_Learning_Firebase_Antigravity.docx` | Doctrina maestra histórica/arquitectónica | Contexto, no trigger |

## 2. ÚNICA REGLA DE EJECUCIÓN

Antigravity **solo ejecuta** lo que indique simultáneamente:

```text
01_CONTROL_STATE.md
        +
02_CURRENT_ORDER.md
```

El plan maestro no autoriza por sí mismo una fase.
Una orden LOCKED no es ejecutable.
Una orden histórica no es ejecutable.
Una orden duplicada no debe existir como orden activa.

## 3. CICLO AUTOMÁTICO COMPLETO

```text
Antigravity 2.0 watcher (~3 min)
            ↓
lee .agents/informe&seguimiento/
            ↓
detecta nuevo order_id + ISSUED
            ↓
AUTO-START
            ↓
Antigravity orquesta subagentes
            ↓
trabaja sobre el proyecto real
            ↓
SSH/VPS para ejecución real cuando corresponda
            ↓
trabajo paralelo; nunca espera bloqueado
            ↓
tests + evidencia + red-team
            ↓
commit
            ↓
push origin/main
            ↓
verifica SHA remoto
            ↓
handoff en GitHub
            ↓
STOP
            ↓
ChatGPT revisa origin/main
            ↓
CORREGIR / BLOCK / REDISEÑAR / AVANZAR
            ↓
ChatGPT publica nueva orden
            ↓
cron la detecta
            ↺
```

No existe un paso de "preguntar al usuario si empieza".

## 4. ANTIGRAVITY = EJECUTOR + ORQUESTADOR DE SUBAGENTES

Antigravity no debe comportarse como un único agente monolítico.

En cada orden debe:

```text
RECON
→ descomponer
→ asignar subagentes
→ investigar en paralelo
→ reconciliar conflictos
→ implementar
→ verificar con otro agente
→ ejecutar pruebas
→ revisar evidencia
→ commit/push
→ handoff
→ STOP
```

Roles disponibles según el alcance:

- RECON / ARCHITECTURE
- IMPLEMENTATION
- QUANT / EXECUTION
- DATA / EVIDENCE
- VALIDATION / GATES
- VERSION / CERTIFICATION
- RED-TEAM / OVERFITTING
- DISCOVERY RESEARCH
- RESEARCH / REPROGRAMMING
- LEARNING / FIREBASE
- RELIABILITY / 24x7
- UI / API PROVENANCE

Un agente que implementa una propiedad **no puede ser el único verificador** de esa propiedad.

## 5. PROYECTO REAL VS SUPERFICIE DE REVISIÓN

Workspace real:

`/home/ubuntu/workspace/pro/trading/01 Ultrarentable`

Puede trabajarse localmente o por SSH en el VPS.

Pero la superficie que ChatGPT revisa es:

`origin/main`

Por tanto:

> **LO QUE NO ESTÁ EN `origin/main` NO ESTÁ ENTREGADO.**

Para terminar una orden, Antigravity debe:

1. trabajar en el proyecto real;
2. ejecutar las pruebas reales;
3. guardar evidencia apropiada;
4. commit;
5. `git push origin main`;
6. verificar que `HEAD == origin/main` en el SHA final;
7. crear el handoff;
8. dejar todo lo versionable en GitHub;
9. detenerse.

El handoff debe registrar el SHA remoto verificado.

## 6. SSH/VPS: NO QUEDARSE ESPERANDO

SSH existe para ejecutar, no para bloquear al agente.

Para cualquier proceso largo (suite completa, WFO, backtest masivo, build, scan, investigación, etc.):

```text
SSH
→ lanzar async/detached
→ remote_job_id
→ PID/log/status
→ volver inmediatamente al trabajo independiente
→ subagentes siguen trabajando
→ polling corto y periódico
→ recoger exit code real
→ integrar resultados
```

Mecanismos válidos:

- `nohup`
- `systemd-run --user`
- `tmux`
- durable queue del proyecto
- cualquier runner idempotente que preserve PID/log/status

Prohibido:

```text
"Esperando la finalización de toda la suite..."
```

si eso mantiene al orquestador esperando 10–20 minutos.

Mientras una suite larga corre, los subagentes deben hacer todo el trabajo independiente posible.

### Verdad de los jobs remotos

Hasta tener:

- `remote_job_id`
- comando exacto
- commit objetivo
- log identificable
- exit code real
- artefactos verificables

el resultado es:

`UNVERIFIED`.

Nunca:

`timeout → PASS`
`job lento → PASS`
`sin salida → PASS`
`resultado antiguo → evidencia del commit nuevo`

## 7. ZERO-SIMULATION / ZERO-FORCING

Regla absoluta para **todo** el proyecto:

```text
ZERO-MOCK
ZERO-SIMULATION
ZERO-FORCING
ZERO-LOOKAHEAD
REAL-ONLY
EVIDENCE-GATED
```

Nunca inventar:

- trades
- métricas
- curvas
- hashes
- datasets
- fills
- gate evidence
- candidatos
- resultados de pruebas

Nunca:

- sustituir datos reales por sintéticos en rutas operativas;
- ocultar un fallo de VPS;
- marcar timeout como PASS;
- modificar tests sólo para ponerlos verdes;
- relajar gates porque sobreviven pocos candidatos;
- reutilizar evidencia de otro commit sin demostrar identidad;
- fabricar fallback científico;
- presentar una simulación como forward real;
- presentar un score de UI como certificación.

Los mocks/fixtures sólo pueden existir en tests unitarios aislados y nunca son evidencia cuantitativa.

## 8. ULTRA

ULTRA es el laboratorio global de oportunidades.

Debe poder investigar cualquier instrumento/mercado/temporalidad que cumpla:

- datos reales disponibles;
- identidad del instrumento;
- histórico suficiente;
- costes/ejecución modelables;
- reglas conocidas;
- reproducibilidad.

No hardcodear una lista cerrada de cripto o temporalidades.

Objetivo explícito de investigación:

`+1000% o más`

pero **solo como objetivo de descubrimiento**, nunca como motivo para relajar validación.

Debe buscar:

- convexidad;
- right-tail;
- asymmetry;
- campaign mechanics;
- trend acceleration;
- volatility expansion;
- asymmetric exits;
- bullets independientes;
- multi-asset opportunities;
- metaestrategias.

Una sola operación extrema no constituye un edge certificado.

## 9. FONDEO = SOLO FUTUROS

El track FONDEO excluye completamente:

- Forex spot/CFD;
- crypto perpetuals;
- CFDs.

Solo puede usar futuros que la política vigente de cada firma/producto permita.

Debe existir un registry por:

```text
firm
product
account
futures universe
policy_version
effective_date
session rules
news rules
overnight/weekend rules
position limits
daily loss
max/trailing loss
profit target
consistency
minimum days
payout rules
cost
```

Siempre resolver:

`FIRM + PRODUCT + ACCOUNT + DATE -> APPLICABLE POLICY`

### Evaluación vs Funded

Son dos problemas distintos:

```text
EVALUACIÓN
→ agresividad permitida dentro de reglas
→ maximizar probabilidad/eficiencia de aprobar

FUNDED
→ preservar drawdown
→ preservar payout eligibility
→ reducir risk of ruin
```

Se pueden estudiar ventanas de 1–5 días cuando las reglas y la muestra lo permitan, pero nunca fabricar suficiencia estadística.

El coste real de la evaluación es un parámetro económico de la cuenta; no existe un hardcode universal de "80 €".

## 10. DISCOVERY FACTORY

No usar:

`GENERATE → FILTER → REPAIR`

Usar:

```text
GENERATE
→ DIVERSIFY
→ DISCOVER
→ CHEAP SCREEN
→ BACKTEST
→ DISCOVERY SCORE
→ CLUSTER
→ SELECT
→ OOS/WFO
→ ROBUSTNESS
→ RESEARCH
→ MUTATE
→ REVALIDATE
→ LEARN
→ REDISCOVER
```

Piezas obligatorias cuando Discovery entre en alcance:

- Strategy Genome;
- behavioral clustering;
- deduplication;
- campaigns por familia;
- trial accounting;
- genealogy;
- Discovery Score separado de Certification;
- fertility;
- exploration/exploitation;
- research budgets;
- cascaded screening;
- Fragility Score;
- blind OOS/research;
- aprendizaje de fallos sin aprender a jugar con los gates.

## 11. VERSIONES Y CERTIFICACIÓN

Nunca sobrescribir una estrategia como si fuera la misma evidencia.

Cambios materiales en:

- strategy
- AST/compiler
- engine
- execution/cost
- risk
- data
- validation policy
- gates
- portfolio logic

pueden invalidar evidencia y exigir revalidación.

Una versión hija no hereda certificación del padre.

Estados posibles:

`CERTIFIED_CURRENT`
`CERTIFIED_LEGACY`
`STALE`
`REVALIDATION_REQUIRED`
`REVALIDATING`
`FAILED_CURRENT_POLICY`

## 12. VALIDACIÓN

Cadena objetivo:

```text
REAL DATA
→ CANONICAL STRATEGY
→ CURRENT ENGINE
→ DETERMINISTIC LEDGER
→ METRICS
→ 11 GATES
→ EVIDENCE
→ CERTIFICATION
```

Cada gate debe producir semántica explícita:

`PASS / FAIL / BLOCKED / NO_EVIDENCE`

Discovery Score nunca sustituye gates.

## 13. RESEARCH / BLIND MUTATION

```text
FAILURE
→ ROOT CAUSE
→ RESEARCH PROPOSAL
→ IMMUTABLE CHILD
→ INDEPENDENT OOS
→ ROBUSTNESS
→ GATES
→ RESULT
→ LEARNING EVENT
```

El holdout nunca puede convertirse en herramienta de diseño de la mutación que después se certificará con ese mismo holdout.

## 14. METAESTRATEGIAS

Composición = otro problema de investigación.

Evaluar:

- correlation;
- tail correlation;
- drawdown concurrence;
- exposure overlap;
- risk contribution;
- margin;
- capital efficiency;
- regime diversification;
- failure concentration.

ULTRA: buscar convexidad agregada y capital efficiency.

FONDEO: solo futuros y optimización contra la política real de evaluación/funded.

Una metaestrategia no puede ocultar que uno de sus componentes falló.

## 15. 24/7 Y RESILIENCIA

El laboratorio puede operar 24/7, con:

- durable queue;
- job IDs;
- leases;
- heartbeat;
- checkpoints;
- retry;
- idempotency;
- watchdog;
- resume;
- stale evidence detection;
- disaster recovery.

Pero **runtime autónomo NO significa cambios arquitectónicos autónomos**.

## 16. PLAN DE FASES

El plan maestro vive en `04_MASTER_ADAPTIVE_IMPLEMENTATION_PLAN.md` y contiene 16 fases:

```text
00 Forensic Baseline / Reality Lock
01 Data Chain of Custody
02 Canonical Strategy + Version Governance
03 Deterministic Universal Execution Engine
04 Discovery Factory
05 Independent Validation + 11 Gates
06 Robustness / WFO / Purged Validation
07 Research + Reprogramming Lab
08 Learning Store + Firebase Recovery
09 Paper / Forward Incubation
10 FONDEO Futures Evaluation Lab
11 FONDEO Funded Preservation Lab
12 ULTRA Bullet / Convexity Lab
13 Meta-Strategy / Portfolio Discovery
14 Certification + UI + API + Continuous Revalidation
15 24/7 Operations / Self-Audit / Disaster Recovery
```

El plan es adaptativo. Después de cada entrega ChatGPT puede:

`AVANZAR | REWORK | BLOCK | REDESIGN | SPLIT | MERGE | ABANDON`

No se avanza por calendario ni por deseo de completar fases.
Se avanza por evidencia.

## 17. QUIÉN HACE QUÉ

### Antigravity
Ejecuta la orden actual usando subagentes, modifica el proyecto real, prueba, documenta, commit/push y entrega handoff.

### Cron
Detecta nuevas órdenes y dispara automáticamente Antigravity.

### ChatGPT / revisión externa
Lee `origin/main`, audita el resultado real, identifica fallos y decide/escribe la siguiente orden adaptativa.

### Usuario
No necesita aprobar manualmente cada fase.

## 18. ESTADO ACTUAL

A fecha de este documento:

```text
CURRENT_PHASE = 00
PHASE_STATUS = REWORK
ACTIVE_ORDER = AG2-P00-002
ACTIVE_ORDER_FILE = 02_CURRENT_ORDER.md
PHASE_01 = LOCKED
```

La Fase 00 descubrió P0 de confianza fundacional; por eso está en rework antes de entrar en Data Chain of Custody.

## 19. REGLA FINAL

> **Antigravity trabaja en el proyecto real con subagentes. Para procesos largos usa SSH/VPS de forma asíncrona y sigue trabajando; no se queda esperando. Todo resultado debe acabar en `origin/main`. Después ChatGPT lee `origin/main`, corrige lo necesario y publica la siguiente orden. El cron la ejecuta automáticamente. Y siempre: ZERO-SIMULATION, ZERO-FORCING.**
