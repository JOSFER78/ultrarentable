# I2 — EL SISTEMA DE MEJORA DE ESTRATEGIAS (M2): qué construir y cómo se demuestra que funciona

Agente: SUB carril MEJORA. Fecha: 2026-09-01. Territorio: SOLO LECTURA sobre el repo completo;
escritura únicamente en este fichero. Ningún fichero de código fue creado ni modificado.
`services/improvement/` **no existe todavía** (verificado: `find services -maxdepth 1 -iname
improvement` → vacío) y tampoco existe `tests/test_improvement_*.py` — este expediente es
exclusivamente diseño y verificación, no construcción; la construcción es W3.5, posterior al
sellado de este documento.

## 0. Método

Cada afirmación previa citada de otro documento del repo se marca **CONFIRMADA** / **REFUTADA** /
**NO VERIFICABLE**, con el comando o la lectura de código que lo sostiene. Ninguna cifra de este
informe se ha tomado de un documento sin abrir el fichero fuente (código o JSON) citado.

Fuentes primarias consultadas: `orchestration/state/PLAN_INVESTIGACION_PROFUNDA.md` (§I2),
`orchestration/state/ARQUITECTURA_MODULAR_ESTRATEGIAS.md` (§M2), `orchestration/state/plan/bloques/
F04_mejora_inteligente.md`, `orchestration/results/analisis_tf_coste_vs_trades.md`,
`orchestration/reviews/forense_telemetria_2026-09-01.md`, `orchestration/results/
grafo_imports_2026-09-01.md`, `orchestration/results/I1_sqx_hallazgos.md`, la telemetría real
`orchestration/results/telemetria/embudo_FONDEO_ES_15m_arquetipos_20260901T182459Z.json` y
`orchestration/results/setup/orq_E2_es_15m_completa.log`, y lectura directa de: `scripts/mine.py`,
`services/api/app/factory/{deep_strategy_improver,optimizer,quality_gates,optimization_loop}.py`,
`services/optimization/expert_refinement_loop.py`, `services/semantic_ai/semantic_engine.py`,
`services/lineage/lineage_service.py`, `contracts/lineage_contracts.py`,
`services/api/app/validation/gates/gate_08_dsr_ratio.py`,
`services/api/app/validation/gates/gate_pipeline_orchestrator.py`,
`services/api/app/engine/fast_engine.py`, `services/api/app/db/database.py` (CandidateModel),
`orchestration/results/cola_mineria.jsonl`.

---

## 1. Hallazgo central (léase antes que nada)

**El único código del repo con nombre "mejora" que hoy está realmente conectado a un flujo de
certificación real (`services/optimization/expert_refinement_loop.py`, importado por la suite B
de gates, por `services/discovery/discovery_validation_pipeline.py` y por
`services/validation/legacy_revalidation_service.py`) implementa exactamente el patrón que la
propia doctrina F04 prohíbe** (mutaciones de parámetro con multiplicadores fijos, sin buscar
valor, sin hipótesis en lenguaje natural) **y además rompe la regla dura "blind holdout intocado
durante todas las iteraciones"** que `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` exige para M2, porque
usa el propio backtest sobre el tramo Blind OOS como criterio de parada en cada una de sus hasta 5
iteraciones. Los "5 agentes de IA" (`InterpreterAgent`, `CriticAgent`, `ImproverAgent`,
`RegimeAnalystAgent`, `AdversarialResearcherAgent`) que su docstring promociona se instancian y no
se llaman nunca — y ni siquiera si se llamaran invocan ningún LLM: son clases Python
deterministas de coincidencia de cadenas. Detalle completo en §4.2. **Ninguno de los seis
candidatos de la tabla de I2 existe hoy en forma utilizable; F04 no existe en ninguna forma
parcial.** Esto no es una sorpresa respecto al "estado real de partida" que el propio
`PLAN_INVESTIGACION_PROFUNDA.md` ya declaraba ("no existe hoy NINGÚN sistema de mejora
funcionando") — lo que aporta este expediente es la evidencia línea a línea de POR QUÉ, y que el
motivo no es solo ausencia sino además un patrón activo que viola la doctrina y que un
`services/improvement/` ingenuo podría heredar por error si solo mirase "qué ya está conectado".

Segundo hallazgo, igual de importante y no capturado por `grafo_imports_2026-09-01.md` (que mide
pureza de imports, no honestidad semántica): `services/api/app/factory/deep_strategy_improver.py`
—citado en el propio encargo como "casi puro" (CONFIRMADO en el eje de imports, ver §4.1)— no
ejecuta ningún backtest: fabrica "métricas mejoradas" multiplicando las de entrada por constantes
fijas (`pf_gain_multiplier = 1.30`, `dd_reduction_factor = 0.40`...) y fuerza
`status = "CERTIFIED_PASS"` incondicionalmente. Es un violador de la Regla 1 (REAL-ONLY) de
libro de texto. Está verificado **inerte hoy** (cero importadores en todo el repo, §4.1), así que
no es fraude en producción — pero es una mina que `services/improvement/` no puede heredar sin
reescritura completa, pese a que su pureza de imports lo haría "barato de mover" en el sentido
puramente mecánico del grafo.

---

## 2. Preguntas del encargo

### 2.1 Protocolo del benchmark I2

**Los 6 sistemas candidatos, mismo presupuesto de CPU, blind holdout intocado, métrica = % de
mejoras que sobreviven OOS+DSR y uplift mediano de PF OOS; `SIN MEJORA` es resultado válido.**

Antes de diseñar el protocolo hay que registrar en qué estado real llega cada candidato a la
línea de salida — verificado, no asumido:

| # | Sistema | Estado real verificado hoy | Riesgo operativo verificado |
| :-- | :--- | :--- | :--- |
| 1 | SQX Improver | CONFIRMADO disponible en la licencia Pro instalada (`I1_sqx_hallazgos.md` §1: módulo "CORE BUILDING" en todos los tiers; visto como `<Task type="Optimize" name="Improve">` real en `.cfx` de `Ultra_Matrix`) | **Licencia Trial Pro expira 05.09.2026** — 4 días desde hoy (`sqcli.exe -license action=info`, salida literal citada en I1 §1). Si el benchmark no arranca este brazo antes de esa fecha (o sin renovar), queda descalificado por causa ajena al diseño, no al sistema |
| 2 | F04 semántico (hipótesis IA → experimento parametrizado) | **NO EXISTE en ninguna forma parcial** (verificado leyendo el código homónimo más cercano, §4.2). Se construye desde cero | Coste de construcción completo, no incremental |
| 3 | Bayesiana (Optuna) sobre dimensiones elegidas | Existe una implementación correcta y reutilizable (`services/api/app/factory/optimizer.py::OptunaOptimizer`, real Optuna+TPE con `eval_fn` inyectado, fallback determinista si Optuna no está instalado) — pero **verificado sin ningún llamador en todo el repo** (`grep -rn "OptunaOptimizer()"` → 0 resultados; se importa en `orchestrator.py` y `autopilot.py` y nunca se instancia) | Ninguno técnico; requiere solo cablear `eval_fn` al motor canónico y decidir qué dimensiones expone (ver §4.1) |
| 4 | Meta-labeling (clasificador decide qué señales tomar) | NO EXISTE ningún código con este patrón en `services/` (buscado por nombre y por concepto: no hay clasificador secundario sobre señales primarias en ningún fichero de `optimization/`, `discovery/` ni `semantic_ai/`) | Se construye desde cero; necesita features honestas — ninguna infraestructura de features aparte del motor de backtest existe hoy para alimentarlo |
| 5 | Filtros de régimen (buscados, no fijados) | Existe reutilizable a medias: `services/optimization/quantitative_arsenal.py` (`MicrostructureProfiler`, perfil de régimen real por Hurst/Parkinson/squeeze) calcula régimen de forma honesta sobre velas reales, pero quien lo consume (`expert_refinement_loop.py`) NO busca los límites del filtro — los fija con constantes (§4.2) | Reescribir solo la capa de aplicación del perfil (que sí busque el umbral), no el perfil en sí |
| 6 | WF re-optimización periódica (parámetros rodantes) | El motor SQX ya tiene `WalkForwardOptimization`/`WalkForwardMatrix` nativos (confirmado en `I1_sqx_hallazgos.md` §1 y §5, tags XML reales) pero eso es WF **dentro** del build, no reoptimización periódica del motor propio en producción — ese segundo sentido no existe en `services/` | Solapa parcialmente con el candidato 1 si se usa vía SQX; si se hace en motor propio, se construye |

**Diseño de protocolo propuesto** (no implementado, es la propuesta de este expediente):

1. **Cobayas**: los near-misses reales de hoy (§2.1.b) — no near-misses inventados ni sintéticos.
   El presupuesto de CPU se fija en tiempo de wall-clock por candidato-cobaya × sistema, medido con
   el mismo mecanismo que ya usa `scripts/mine.py` (`segundos` en `cola_mineria.jsonl`), para que
   los 6 brazos sean comparables sin depender de heurísticas de "número de iteraciones" que no
   significan lo mismo entre sistemas (una iteración de Optuna no cuesta lo mismo que un Build
   completo de SQX).
2. **Blind holdout**: el tramo OOS (últimas 20 % barras cronológicas, split canónico 60/20/20 ya
   usado por `mine.py` y por `expert_refinement_loop.py`) se congela en disco ANTES de lanzar
   cualquier brazo — un hash SHA-256 del tramo se registra en el informe del benchmark y se
   verifica al final que no cambió. Ningún sistema, incluido el brazo "F04 semántico" que se
   construya, puede leer ese tramo hasta la evaluación final de cada intento; el hallazgo de
   §4.2 (que `expert_refinement_loop.py` sí lo lee dentro del propio bucle) es precisamente el
   antipatrón que este punto del protocolo existe para prohibir por diseño, no solo por disciplina.
3. **`trials_tested` acumulado, no reiniciado**: cada brazo debe reportar al Gate 8 (DSR) la suma
   de (a) el tamaño del espacio de búsqueda que produjo el candidato de partida (heredado del
   `contexto.espacio_total` de la telemetría de M1, p. ej. 420 para la campaña de hoy) más (b) las
   iteraciones propias que ese brazo gastó. Se verificó (§5) que hoy ningún sistema hace esto
   correctamente salvo `mine.py` en su propio tramo — es un requisito NUEVO del protocolo, no una
   práctica ya establecida.
4. **Métrica**: % de intentos que llegan a 11/11 gates + criterio 1.1 completo sobre el holdout
   nunca tocado, y uplift mediano de PF OOS (mejora menos candidato de partida) SOLO sobre ese
   holdout — nunca sobre IS ni sobre el tramo usado durante la mejora. `SIN MEJORA` se registra
   explícitamente como resultado (no se descarta el intento del informe).
5. **Mismo presupuesto de CPU por sistema**: dado que la máquina está compartida con otros
   agentes (regla de presupuesto del proyecto), el benchmark real debe lanzarse en una ventana
   donde sea el único proceso pesado — no se ejecutó ningún experimento de benchmark en este
   turno por ser de solo lectura; queda como trabajo de construcción posterior a este sellado.

**2.1.b — Near-misses reales verificados HOY para usar de cobayas** (verificado en la BD/telemetría
real, no en documentos):

`orchestration/results/telemetria/embudo_FONDEO_ES_15m_arquetipos_20260901T182459Z.json`
(generado 2026-09-01T18:24:59Z, motor 5.17.0, `dataset_source=dukascopy`,
`ds_dukascopy_usa500idxusd_15m_consolidated.json`, **espacio de búsqueda completo: 420/420
configuraciones, sin truncar** — `contexto.max_candidates=0`, `contexto.truncado=false`,
confirmando que las correcciones D1/D2 de `forense_telemetria_2026-09-01.md` §6 ya están
aplicadas en esta campaña):

| Candidato | Familia | Etapa donde muere | trades | pf en esa etapa |
| :--- | :--- | :--- | ---: | ---: |
| `UR_FONDEO_ES_15M_c106` | REVERSION_ATR | OOS | 132 | 0,650 |
| `UR_FONDEO_ES_15M_c107` | REVERSION_ATR | VAL | 133 | 0,960 |
| `UR_FONDEO_ES_15M_c108` | REVERSION_ATR | VAL | 134 | 0,990 |

Estos tres son, literalmente, **los únicos 3 supervivientes de la etapa IS de las 108
configuraciones REVERSION_ATR** (verificado: 105 de 108 mueren en IS con pf entre 0,600 y 1,040;
umbral IS = 1,05 — quedan exactamente 3, que son c106/c107/c108) y los únicos 3 de las 420
configuraciones totales que llegaron a VAL u OOS junto con 12 `SQUEEZE_BREAKOUT` de pf 0,11-0,17
(muy lejos del umbral, no son near-misses útiles). Son cobayas reales y legítimos para el
benchmark de I2.

**Matiz sobre la afirmación previa del encargo** ("PF IS ≈1,0 y >130 ops"): **CONFIRMADA en la
parte de operaciones** (132/133/134, todas >130) y **CONFIRMADA en sustancia pero NO VERIFICABLE
en el valor exacto** en la parte de PF IS. Se verificó leyendo `scripts/mine.py:712-799,
1000-1018`: la telemetría persistida solo registra la etapa donde el candidato MUERE, con el PF de
ESA etapa — nunca el PF en IS de un candidato que superó IS. El PF ≈1,0 real y verificable en el
JSON es el de la etapa de muerte (VAL para c107/c108: 0,96/0,99, sí muy cerca de 1,0; OOS para
c106: 0,65, no cerca de 1,0 — dista 0,45 del umbral OOS 1,1). Que su PF en IS estuviera cerca de
1,0-1,1 es una inferencia razonable (el umbral IS es 1,05 y las 105 muertes en IS de la misma
familia llegan hasta 1,04) pero no un dato persistido. **Esto es en sí mismo un hallazgo de
diseño para I2**: el banco de pruebas necesita near-misses caracterizados en las tres etapas
(IS/VAL/OOS), y el instrumento actual no lo provee — se recomienda extender la telemetría
(ya hay una tarea abierta equivalente, W2.7, para PF bruto/neto) para persistir también PF/trades
de IS de todo candidato que la supere, no solo de los que mueren en ella.

También se verificaron los tres near-misses ULTRA citados en `PLAN_INVESTIGACION_PROFUNDA.md`
§I2 contra `orchestration/results/cola_mineria.jsonl` (no contra el propio doc): **CONFIRMADOS
exactos los tres** — `UR_ULTRA_ETHUSDT_4H_c481/c485` trades=39 pf=2,170; `UR_ULTRA_SOLUSDT_4H_
c337/c341` trades=36 pf=1,560; `UR_ULTRA_AVAXUSDT_1H_c997/c1001` gates=7/11 score=63,5 — los tres
del 2026-08-31, perfil `amplio`, track ULTRA. Siguen siendo cobayas válidas (ULTRA aparcado pero
explícitamente autorizado para esto por el propio texto del encargo), aunque más antiguas que el
lote FONDEO ES 15m de hoy.

### 2.2 La interfaz de `services/improvement/`

**Protocolo `Improver`**: no existe hoy ningún protocolo/ABC con ese nombre ni equivalente
(buscado en `contracts/` y `services/`: no hay ninguna clase base o `Protocol` de Python que
defina "recibe candidato + evidencia, devuelve candidato mejorado + evidencia"). Los 6 candidatos
tienen firmas completamente distintas hoy: `DeepStrategyImprover.improve_candidate(candidate_dict,
technique, n_trials) -> dict`, `OptunaOptimizer.optimize_parameters(strategy_dict, eval_fn,
n_trials, max_leverage) -> tuple`, `AggressiveOptimizationLoop.run(initial_population, evaluate,
mutate, fresh, ...) -> LoopResult`, `ExpertStrategyOptimizer.refine_candidate_loop(candidate_id,
max_iterations) -> dict`. Diseñar un protocolo común (`Improver.propose(candidate, evidence,
budget) -> ImprovementAttempt`) es trabajo de W3.5, no está hecho.

**Máquina de estados CRUDA→EVALUADA→EN_MEJORA(n)→RE-EVALUADA→CERTIFICADA|AGOTADA**: **NO EXISTE
hoy en ningún contrato ni modelo de datos** — verificado en dos sitios:
- `contracts/lineage_contracts.py::CertificationStatus` solo tiene estados TERMINALES (`APPROVED`,
  `ULTRA_CERTIFIED`, `FUNDING_CERTIFIED`, `PORTFOLIO_CERTIFIED`, varios `REJECTED_*`, varios
  `BLOCKED_*`, `PENDING_EVALUATION`) — nada de `EN_MEJORA(n)` ni presupuesto de iteración.
- `services/api/app/db/database.py::CandidateModel.status` es un `Column(String)` de texto libre,
  **sin `Enum` que lo gobierne**, y ya está divergente entre dos escritores reales del propio
  código: el comentario de la línea 383 documenta `INVESTIGACION_BTC, RECHAZADA_FONDEO_DD,
  CANDIDATA_FONDEO, PAPER, LISTA_PARA_EVALUACION, EJECUTANDO, PAUSADA, RETIRADA`, pero
  `expert_refinement_loop.py` escribe un vocabulario DISTINTO no documentado ahí: `APPROVED`,
  `CANDIDATA_AVANZADA`, `INCUBADORA_REPROGRAMACION`, `REJECTED_AFTER_REFINEMENT` (líneas 369-383
  de ese fichero). Es evidencia directa de que un campo de estado sin Enum ya ha divergido con
  solo dos escritores — un argumento fuerte para que la máquina de estados de M2 nazca como un
  contrato Pydantic con `Enum` cerrado, no como texto libre en la tabla existente.

**Presupuesto de iteraciones con penalización DSR**: el MECANISMO matemático existe y es correcto
(§5), pero **el campo que lo alimenta (`trials_tested`) no tiene una fuente única de verdad hoy**
— cada llamador decide qué poner. `scripts/mine.py:1056` lo hace bien
(`trials_tested = len(search_space)`); `expert_refinement_loop.py:271` lo hace mal
(`trials_tested = iteration`, 1 a 5, ignorando el tamaño del espacio de búsqueda que produjo el
candidato). Es una fuga real de disciplina de multiplicidad si un near-miss nacido de una campaña
de 420 configuraciones entrara en ese bucle y se certificara en la iteración 3: Gate 8 vería
`trials_tested=3` en vez de 423, e infra-penalizaría por un factor de más de 100×. **La interfaz
de `services/improvement/` debe exigir como campo OBLIGATORIO del contrato de entrada un
`trials_tested_upstream` heredado de la telemetría de M1 y sumarlo a sus propias iteraciones antes
de invocar Gate 8** — no es una opción de diseño, es una corrección de un bug de disciplina ya
demostrado en el código existente.

**Linaje (`services/lineage/` ya existe: ¿sirve?)**: CONFIRMADO que existe
(`services/lineage/lineage_service.py`, 237 LOC, un solo fichero + `contracts/
lineage_contracts.py`). Arquitectura DAG genealógica (`parent_ids`/`children`) con
`CertificationRecord` firmado criptográficamente (SHA-256 sobre el propio certificado,
`_compute_cert_hash`/`verify_certificate`) — el mecanismo de certificado inmutable y verificable
es sólido y reutilizable EN CONCEPTO para M2. Pero **NO sirve tal cual**, por tres motivos
verificados leyendo el fichero completo:
1. No tiene ningún campo para el estado intermedio de mejora (iteración, presupuesto,
   `EN_MEJORA(n)`) — solo certificados terminales.
2. Hardcodea `venue="BINGX"` para TODO nodo del árbol (líneas 167 y 189) — etiquetaría mal
   cualquier estrategia FONDEO que pasara por linaje, sin lanzar ningún error (falla silenciosa).
3. Depende directamente de `services.api.app.db.database` (5 modelos ORM en una sola línea,
   línea 20) — es exactamente la arista que `grafo_imports_2026-09-01.md` (§3, corte #4 del
   ranking) identifica como la ÚNICA razón del ciclo `services.api ↔ services.lineage`, y el
   corte de mayor apalancamiento recomendado (sustituir por un contrato de lectura). Reutilizar
   linaje en M2 sin cortar esto arrastraría al nuevo módulo dentro del mismo macro-ciclo de
   importación que el expediente I7 ya documentó para el resto del backend.

Conclusión de la pregunta 2: **el linaje sirve como cimiento (certificado firmado + DAG) pero
necesita tres cambios concretos antes de que M2 pueda apoyarse en él: generalizar `venue`,
añadir estado de iteración (probablemente como contrato nuevo `ImprovementCycle` en vez de forzarlo
dentro de `CertificationRecord`, que es `frozen=True` — inmutable por diseño, correcto para un
certificado, incorrecto para un estado que cambia en cada iteración), y cortar el acceso directo a
`api.app.db.database`.**

### 2.3 Qué código existente se mueve o se envuelve

Verificación directa (no solo el grafo de imports) de los 4 ficheros que el propio encargo pide
comprobar, `services/api/app/factory/{deep_strategy_improver,optimizer,quality_gates}.py` +
`optimization_loop.py` (673 LOC):

| Fichero | Pureza de imports (grafo, CONFIRMADA) | Honestidad semántica (verificado en este expediente, NO cubierto por el grafo) | Veredicto de reutilización |
| :--- | :--- | :--- | :--- |
| `deep_strategy_improver.py` (168 LOC) | 0 imports internos — CONFIRMADO | **FABRICA métricas**: multiplica PF/DD/ROI de entrada por constantes fijas sin ejecutar ningún backtest y fuerza `status="CERTIFIED_PASS"` incondicionalmente (líneas 90-165). Violación de libro de texto de REAL-ONLY. Verificado **sin ningún importador en todo el repo hoy** (`grep -rn "deep_strategy_improver\|DeepStrategyImprover"` → solo el propio fichero) | **NO mover tal cual**. Es una PETICIÓN AL ORQUESTADOR de decisión de cuarentena (ver §6) — este carril no puede tocarlo por ser de solo lectura, pero debe quedar señalado antes de que W3.5 lo mueva por error confiando en la pureza de imports |
| `optimizer.py` (`OptunaOptimizer`, 105 LOC) | 0 imports internos — CONFIRMADO | Legítimo: usa Optuna real (TPE) con `eval_fn` inyectado externamente, fallback determinista con semilla si Optuna no está instalado; no fabrica nada. Verificado **sin ningún llamador en todo el repo** (`grep -rn "OptunaOptimizer()"` → 0) — se importa en `orchestrator.py`/`autopilot.py` y nunca se instancia | Mover sin cambios; cablear `eval_fn` al motor canónico es el único trabajo pendiente |
| `quality_gates.py` (173 LOC) | 0 imports internos — CONFIRMADO | Legítimo (umbrales deterministas, sin datos inventados) pero define una **política de aceptación paralela** (`MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO=4.50`, `MIN_CALMAR_RATIO=0.5`, `MIN_RENTABLE_PROFIT_FACTOR=1.30`) que **no coincide** con el criterio 1.1 sellado (PF OOS ≥1,25, no 1,30; sin exigencia explícita de Calmar) | Mover, pero documentar explícitamente como pre-filtro barato SUBORDINADO al criterio 1.1 — nunca como gate competidor. Riesgo de confusión si conviven ambas políticas sin esa etiqueta |
| `optimization_loop.py` (`AggressiveOptimizationLoop`, 227 LOC) | Solo depende de `quality_gates.py` (el propio) — CONFIRMADO | Legítimo y genérico (recibe `evaluate`/`mutate`/`fresh` como callbacks, no fabrica nada por sí mismo) — **y activamente usado hoy** por `campaign_pipeline.py` y `fast_engine_campaign.py`. Pero su único llamador real de producción evalúa vía `services/api/app/engine/fast_engine.py::FastEngine`, un motor **distinto y no-canónico** (importa `BingXIsolatedMarginModel`/`BingXMarketRiskRules`, específico de BingX/ULTRA), NO el SSOT `services/validation/engine/event_backtest_engine.py` | Mover el bucle sin cambios; pero su adopción en M2/FONDEO exige un nuevo callback `evaluate` que llame al motor canónico vía puerto — cablearlo a `FastEngine` para FONDEO sería usar un motor no gobernado por la Regla #26 |

`services/optimization/*` (1.582 LOC, `universal_optimizer_engine.py`,
`expert_refinement_loop.py`, `continuous_research_daemon.py`, `quantitative_arsenal.py`):
**CONFIRMADO que NO cumple la frontera "solo contracts/ + gates"** (el propio grafo ya lo decía,
con líneas exactas de import a `discovery`, a la suite B completa de gates, a `api.config`, a
`semantic_ai`) — y este expediente añade que, además de los imports, su lógica central
(`expert_refinement_loop.py`) tiene **dos defectos de comportamiento verificados** (holdout usado
dentro del bucle, §4.2; `trials_tested` mal calculado, §5) que exigen reescritura semántica, no
solo reencaje de imports. `quantitative_arsenal.py` (perfil de microestructura por régimen real:
Hurst, volatilidad de Parkinson, squeeze) SÍ es reutilizable — es cálculo honesto sobre velas
reales, cero imports internos confirmado por el grafo — pero solo si quien lo consuma en M2 BUSCA
los umbrales del filtro en vez de fijarlos como hace hoy `expert_refinement_loop.py`.

### 2.4 Cómo se penaliza la multiplicidad en cada sistema

| Sistema | Mecanismo de penalización verificado |
| :--- | :--- |
| SQX Improver | NO VERIFICABLE sin ejecutarlo (fuera de alcance de solo lectura); SQX tiene Monte Carlo/WFO/SPP nativos que podrían usarse como proxy, pero no hay evidencia de que su ranking interno aplique una fórmula equivalente a DSR sobre el nº de estrategias evaluadas en el Build |
| F04 semántico (a construir) | Por diseño (F04_mejora_inteligente.md §4.3): DSR obligatorio, "cuantas más hipótesis, más alto el listón" — pendiente de implementar |
| Bayesiana (Optuna) | El propio `n_trials` de Optuna es, por construcción, el número exacto de evaluaciones — trivial de propagar a Gate 8 como `trials_tested` si se cablea correctamente; hoy no se cablea porque no hay llamador (§2.3) |
| Meta-labeling | No existe código — sin mecanismo |
| Filtros de régimen buscados | Si se implementa como búsqueda real de umbral, el nº de umbrales probados es el `trials_tested` natural; hoy `expert_refinement_loop.py` no busca umbral, así que no hay multiplicidad que penalizar en ese sentido (el problema es el opuesto: cero búsqueda) |
| WF rodante | Si se hace en SQX, WFO ya reporta nº de ventanas — proxy razonable de multiplicidad temporal, no de multiplicidad de hipótesis |
| **Mecanismo transversal ya construido** | Gate 8 (`services/api/app/validation/gates/gate_08_dsr_ratio.py`, y su gemelo de la suite A `services/validation/engines/gate_08_deflated_sharpe.py`) implementa correctamente Bailey & López de Prado (Sharpe esperado máximo bajo selección múltiple vía `trials_tested`, ajuste por skewness/kurtosis, `math.erf` determinista, sin dependencias binarias). **Es reutilizable tal cual para los 6 sistemas** — el trabajo pendiente no es matemático, es de PROPAGACIÓN CORRECTA del contador de intentos desde cada sistema hasta este gate (§2.2, ya identificado como bug real en `expert_refinement_loop.py`) |

---

## 3. Tabla de afirmaciones previas verificadas

| # | Afirmación previa | Fuente | Veredicto |
| :-- | :--- | :--- | :--- |
| P1 | "F04 está DISEÑADO pero NO implementado; el lazo de mejora de SQX llevaba meses roto por configuración; no existe hoy NINGÚN sistema de mejora funcionando" | `PLAN_INVESTIGACION_PROFUNDA.md` §I2 | **CONFIRMADA en la parte de F04** (verificado línea a línea, §4.2 y §1); **NO VERIFICABLE la parte de SQX Improver "roto"** (el estado runtime del VPS no es accesible desde este PC — el propio `I1_sqx_hallazgos.md` ya lo declara NO VERIFICABLE; lo que sí se confirma es que el módulo Improver existe y está disponible en la instalación local, con licencia que expira en 4 días) |
| P2 | "services/api/app/factory/{deep_strategy_improver,optimizer,quality_gates}.py son casi puros" | Encargo, citando `grafo_imports_2026-09-01.md` §2d | **CONFIRMADA en el eje que mide** (0 imports internos en los tres, verificado leyendo cada fichero completo) — **pero incompleta como criterio de reutilización**: uno de los tres (`deep_strategy_improver.py`) fabrica datos y no debe moverse sin reescritura pese a su pureza de imports. El grafo no pretendía medir esto (mide acoplamiento, no honestidad), así que no es un REFUTADA — es una matización necesaria antes de actuar sobre esa cifra |
| P3 | "near-misses reales: c106/c107/c108 REVERSION_ATR con PF IS ≈1,0 y >130 ops" | Encargo, citando la telemetría de hoy | **CONFIRMADA la existencia y el nº de operaciones** (132/133/134, verificado en el JSON); **NO VERIFICABLE el valor exacto de PF en IS** (la telemetría solo persiste el PF de la etapa de muerte, no el de IS para quien la supera — hallazgo de diseño documentado en §2.1.b) |
| P4 | "el linaje (`services/lineage/`) ya existe" | `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` §M2 | **CONFIRMADA que existe** (237 LOC + contrato); **matizada en si "sirve" tal cual** — no, necesita los tres cambios de §2.2 |
| P5 | "presupuesto de iteraciones por estrategia con penalización por multiplicidad (DSR)" ya es una regla dura del loop M2 | `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` §M2 | El MECANISMO matemático (Gate 8) **CONFIRMADO correcto y ya construido**; su aplicación real en el único código de "refinamiento en bucle" que existe hoy (`expert_refinement_loop.py`) **REFUTADA** — el `trials_tested` que ese fichero calcula ignora el tamaño del espacio de búsqueda ascendente (bug real, §2.2/§5) |
| P6 | "blind holdout INTOCADO durante todas las iteraciones" (regla dura de M2) | `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` §M2 | Como regla de diseño, no se contradice; pero el único código existente que se parece a un bucle de mejora **la viola activamente** (`expert_refinement_loop.py` lee `candles_blind_oos` dentro del bucle, §4.2) — dato relevante para que el protocolo del benchmark (§2.1) la haga cumplir por construcción, no solo por disciplina de diseño |
| P7 | Cobayas ULTRA citadas en el propio `PLAN_INVESTIGACION_PROFUNDA.md`: ETHUSDT 4h PF 2,17/39, SOLUSDT 4h 1,56/36, AVAXUSDT 1h 7/11 gates | `PLAN_INVESTIGACION_PROFUNDA.md` §I2 | **CONFIRMADAS exactas las tres**, verificadas contra `cola_mineria.jsonl` (no contra el propio doc) |

---

## 4. Evidencia literal de los dos hallazgos centrales

### 4.1 `deep_strategy_improver.py` fabrica métricas (líneas 90-165, cita textual parcial)

```python
prev_pf = float(upgraded.get("profit_factor_oos") or upgraded.get("profit_factor") or 1.05)
...
pf_gain_multiplier = 1.30 if "INJECT_ATR_VOLATILITY_FILTER" in diag["recommended_mutations"] else 1.18
new_pf = round(max(1.35, prev_pf * pf_gain_multiplier), 2)
...
upgraded["status"] = "CERTIFIED_PASS"
upgraded["tier"] = "TIER_1_CERTIFIED"
```

No hay llamada a ningún motor de backtest en todo el fichero (168 LOC, verificado completo). El
"trial" y el "Optuna engine" que declara en su metadata (`"optuna_engine":
"DeterministicRegimeFilterOptimizer"`) son etiquetas de texto, no una ejecución real.

### 4.2 `expert_refinement_loop.py`: holdout usado dentro del bucle + agentes nunca invocados

Partición (líneas 153-159): `candles_is = candles[:0.60·N]`, `candles_blind_oos =
candles[0.80·N:]`. Dentro del bucle de refinamiento (líneas 205-364, hasta `max_iterations=5`
veces):

```python
is_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_is, initial_capital_usd=initial_cap)
oos_bt = self.backtest_engine.run_backtest(strat_snapshot, candles_blind_oos, initial_capital_usd=initial_cap)
...
if gates_passed_count == 11 and oos_bt.net_profit_usd > 0 and oos_bt.max_drawdown_pct <= (85.0 if is_ultra else 4.5):
    is_certified = True
    ...
    break
```

El holdout se lee y se usa como criterio de parada en CADA iteración, no una sola vez al final.

Los 5 agentes se instancian en `__init__` (líneas 63-68: `self.failure_db`, `self.interpreter`,
`self.critic`, `self.improver`, `self.regime_analyst`, `self.adversarial`) y **no aparecen en
ningún otro punto del fichero** — verificado con `grep -n "self\.interpreter\.\|self\.critic\.\|
self\.improver\.\|self\.regime_analyst\.\|self\.adversarial\.\|self\.failure_db\." <fichero>` →
0 resultados. El fichero solo tiene 3 métodos en total (`__init__`, `find_dataset_file`,
`refine_candidate_loop`); no hay ningún otro sitio donde pudieran usarse.

Las clases en sí (`services/semantic_ai/semantic_engine.py`) no llaman a ningún LLM — verificado
con `grep -n "anthropic\|openai\|requests\.\|httpx\|api_key\|LLM"` sobre el fichero completo → 0
resultados. `InterpreterAgent.describe_strategy` es coincidencia de subcadenas
(`"EMA" in d or "RSI" in d`); `CriticAgent.critique` es una lista de comprobaciones `if/else`
fijas. Es lógica determinista de reglas, correctamente escrita, pero no es "IA" en el sentido que
F04 exige (hipótesis en lenguaje natural sobre el mecanismo del fallo).

Las mutaciones reales que sí se ejecutan (líneas 320-359) son del tipo que F04 prohíbe
explícitamente:

```python
if 5 in failed_ids or oos_bt.max_drawdown_pct > (80.0 if is_ultra else 4.0):
    params["sl_atr_mult"] = max(1.1, round(float(params.get("sl_atr_mult", 2.0)) * 0.88, 2))
...
if 2 in failed_ids or (oos_bt.profit_factor < 1.25 and oos_bt.net_profit_usd > 0):
    params["tp_atr_mult"] = max(min_viable_tp, round(float(params.get("tp_atr_mult", 5.0)) * 1.20, 2))
```

Multiplicadores fijos (0,88×, 1,20×, 1,15×, 0,92×...) por gate fallido — exactamente "subir el SL
un 2 %" con otro nombre, no una dimensión buscada.

---

## 5. Gate 8 (DSR) es correcto; su alimentación no lo es

`services/api/app/validation/gates/gate_08_dsr_ratio.py` implementa Bailey & López de Prado
correctamente (expected max Sharpe bajo selección múltiple vía `_std_norm_ppf`/`_std_norm_cdf`
deterministas, ajuste por skewness/kurtosis, `passed = dsr_prob >= 0.50`). Recibe `trials_tested`
como parámetro puro — no calcula multiplicidad por sí mismo, confía en quien lo llama
(`services/api/app/validation/gates/gate_pipeline_orchestrator.py:108-109`:
`g.evaluate(oos_trades_pnl=oos_trades, trials_tested=candidate_info.get("trials_tested"))`).

Dos llamadores reales verificados, con resultado opuesto:

- `scripts/mine.py:1056`: `"trials_tested": len(search_space)` — CORRECTO, refleja el tamaño real
  del espacio de búsqueda (420 para la campaña ES 15m de hoy).
- `services/optimization/expert_refinement_loop.py:271`: `"trials_tested": iteration` — INCORRECTO
  si el candidato de partida viene de una búsqueda más amplia, porque solo cuenta las iteraciones
  del propio bucle (1 a `max_iterations`, por defecto 5) e ignora el origen.

No hay ninguna fuente única de verdad para este contador entre M1 y M2 hoy. Es el requisito de
interfaz más concreto y accionable de todo este expediente (§2.2).

---

## 6. Lo que queda abierto y peticiones al orquestador

- **No se ejecutó ningún experimento del benchmark de I2** en este turno: el territorio del carril
  es solo lectura y `services/improvement/` aún no existe. El protocolo de §2.1 es una propuesta a
  validar con el primer experimento real de W3.5, no un resultado.
- **PETICIÓN AL ORQUESTADOR**: `services/api/app/factory/deep_strategy_improver.py` fabrica
  métricas y fuerza `CERTIFIED_PASS` sin backtest — hoy verificado inerte (0 importadores), pero
  es una decisión fuera de este territorio si debe ir a cuarentena antes de que W3.5 lo toque
  (por su pureza de imports podría moverse por error confiando solo en `grafo_imports_2026-09-01.md`
  sin leer su contenido). No se ha movido nada — es solo lectura.
- **PETICIÓN AL ORQUESTADOR**: la licencia SQX Pro Trial expira 05.09.2026 (4 días desde hoy) —
  si el benchmark de I2 quiere incluir el brazo "SQX Improver" con evidencia real, la renovación o
  activación de licencia es una decisión que excede este carril (I1 ya lo señaló como bloqueo para
  la ventana de Emilio).
- **PETICIÓN AL ORQUESTADOR**: la telemetría de `mine.py` no persiste el PF/trades de IS para los
  candidatos que superan esa etapa (solo registra la etapa de muerte) — esto limita qué se puede
  decir de los near-misses como cobayas caracterizadas en las tres etapas. Encaja con la tarea ya
  abierta W2.7 (PF bruto/neto); se recomienda ampliarla para cubrir también este campo, pero es
  una decisión de otro carril (código de minería, no de mejora).
- No se verificó en este turno si `services/validation/certification_registry.py` (importado por
  `expert_refinement_loop.py` y no leído aquí por presupuesto de tiempo) aporta algo relevante a
  la máquina de estados de M2 — queda como pregunta abierta para quien construya W3.5.
- El estado runtime EN VIVO del SQX Improver (si de verdad respeta el holdout cuando se ejecuta
  un Improve real) sigue **NO VERIFICADO** — no se lanzó ningún proceso de SQX en este turno por
  ser de solo lectura; es el primer experimento pendiente del propio benchmark, no de este
  expediente de diseño.
