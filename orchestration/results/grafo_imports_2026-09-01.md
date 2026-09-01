# Grafo de imports — cierre de la investigación I7 (AG-5)

Fecha: 2026-09-01 · Alcance: **solo lectura** sobre `services/` y `scripts/`. Ningún fichero de
código fue modificado. Artefactos producidos: este informe y
`orchestration/results/grafo_imports_2026-09-01.json`.

## 0. Metodología

No se instaló `grimp`/`pydeps`: se escribió un analizador propio
(`ast` de la stdlib, Python 3.11.8 del venv del proyecto) porque es más trazable y no depende de
paquetes externos. El script:

1. Camina `services/` y `scripts/` con `Path.rglob("*.py")`, excluyendo `__pycache__`.
2. Parsea cada fichero con `ast.parse` (lectura `utf-8-sig` para tolerar BOM;
   `services/execution/canonical_runtime_adapter.py` lo llevaba).
3. Un `NodeVisitor` mantiene una pila de contexto (`FunctionDef`/`AsyncFunctionDef`, `Try`, `If`)
   y clasifica cada `Import`/`ImportFrom` — **incluidos los anidados dentro de funciones o
   bloques `try`/`if`** — en `top-level`, `diferido-en-función` o `condicional`.
4. Los imports relativos (`from .`, `from ..x`) se resuelven a nombre punteado absoluto
   replicando el algoritmo real de `importlib._bootstrap._resolve_name`.
5. Una arista solo se crea cuando el módulo resuelto (o el prefijo interno más largo que
   coincide, para `from pkg import symbol`) es un fichero real de `services/`/`scripts/`. Los
   imports a terceros/stdlib/`contracts/` no son nodos de este grafo (se documentan aparte donde
   son relevantes, preguntas d/e).

Script y consultas auxiliares quedaron en el scratchpad de la sesión (no en el repo, por
territorio de escritura).

## 1. Cobertura y verificación

```
$ find services scripts -name "*.py" | wc -l
310
```

El JSON publicado tiene **310 nodos** — coincide exactamente, sin diferencia que explicar.
Parse errors: 0 (tras el fix de BOM). Total de aristas resueltas dentro del árbol: **1.003**
(916 `top-level`, 87 `diferido-en-función`, 0 `condicional` — no se encontró ningún
`try:`/`if:` a nivel de módulo que envuelva un import interno; los `try` que existen en el
árbol son para dependencias externas opcionales, no para módulos propios).

Los 87 imports diferidos-en-función son en sí mismos una pista: es el patrón clásico para
esquivar un ciclo de import en Python. Encaja con los ciclos medidos en la sección 3.

## 2a. Las dos suites de gates: quién importa a cada una

**Suite B — `services/api/app/validation/gates/` (la que certifica).** Verificado con AST y
cruzado con `grep -rn` independiente (mismo resultado exacto, 20 líneas / 18 ficheros):

| Fichero:línea | Tipo | Import |
| :--- | :--- | :--- |
| `scripts/debug_single_dataset.py:15` | top-level | `gate_pipeline_orchestrator.GatePipelineOrchestrator` |
| `scripts/debug_single_dataset_gates.py:18` | top-level | ídem |
| `scripts/diagnose_crypto_gates.py:19` | top-level | ídem |
| `scripts/diagnose_gates.py:29` | top-level | ídem |
| `scripts/diagnose_intraday_gates.py:15` | top-level | ídem |
| `scripts/mine.py:895` | diferido-en-función | ídem |
| `scripts/optimize_and_certify_es_ym.py:44` | top-level | ídem |
| `scripts/phase2_blind_oos.py:15` | top-level | ídem |
| `scripts/phase2_research_run.py:16` | top-level | ídem |
| `scripts/register_and_assemble_all_champions.py:24` | top-level | ídem |
| `scripts/run_sequential_crypto_certifier.py:28` | top-level | ídem |
| `scripts/run_ultra_intraday_mining.py:36` | top-level | ídem |
| `scripts/test_crypto_hyper_search.py:28` | top-level | ídem |
| `scripts/test_fondeo_cert.py:41` | top-level | ídem |
| `services/discovery/discovery_validation_pipeline.py:36` | top-level | ídem |
| `services/optimization/expert_refinement_loop.py:33` | top-level | ídem |
| `services/optimization/universal_optimizer_engine.py:27` | top-level | ídem |
| `services/optimization/universal_optimizer_engine.py:201` | diferido-en-función | `gate_10_agent_debate.Gate10AgentDebate` |
| `services/semantic_ai/autonomous_discovery_engine.py:41` | top-level | `gate_pipeline_orchestrator.GatePipelineOrchestrator` |
| `services/validation/legacy_revalidation_service.py:31` | top-level | ídem |

**14 scripts + 4 ficheros de `services/`** importan la suite B directamente.

**Suite A — `services/validation/engines/` (la que ve la web).** Solo **1 importador directo**
fuera del propio paquete:

| Fichero:línea | Tipo | Import |
| :--- | :--- | :--- |
| `services/validation/validation_router.py:158` | top-level | `engines.pipeline_orchestrator.ModularValidationPipeline` |

Verificado también con `grep -rn "from services\.validation\.engines\|import services\.validation\.engines"` — mismo resultado único.

**¿Quién importa las DOS suites?** A nivel de import directo, **ningún fichero** — la lista de
`src` de ambos conjuntos no se solapa. Pero el expediente preliminar decía "candidates_router
importa LAS DOS", así que se comprobó el camino transitivo real:

- `services/api/app/api/candidates_router.py:20` importa
  `services.validation.legacy_revalidation_service.legacy_revalidation_service` (vive en el
  paquete de la suite A, pero **no** importa `services.validation.engines`).
- `services/validation/legacy_revalidation_service.py:31` importa
  `services.api.app.validation.gates.gate_pipeline_orchestrator.GatePipelineOrchestrator`
  (suite B) — y también `services.validation.engine.event_backtest_engine` (el motor SSOT,
  distinto de `engines/`, la suite A).

**Esto es el nudo real, más preciso que la frase del expediente**: el fichero
`services/validation/legacy_revalidation_service.py` vive físicamente dentro del paquete de la
suite A (`services/validation/`) pero su lógica de certificación de gates depende
**exclusivamente de la suite B**. `candidates_router` llega a la suite B en 2 saltos
(`candidates_router → legacy_revalidation_service → gate_pipeline_orchestrator`), no en uno
directo. Además `services/api/app/main.py` monta **ambas** suites como routers HTTP en el mismo
proceso: línea 146 `candidates_router` (que llega a B por el camino de arriba) y línea 169
`validation_router` (que es la puerta de entrada directa a la suite A vía
`engines.pipeline_orchestrator`) — confirmado leyendo `services/api/app/main.py:32,43,146,169`.

También se comprobó `services/api/app/core/market_matrix.py` (mencionado en el expediente como
importador de B): su único import de validación es
`services.api.app.validation.market_specs.get_market_spec` (línea 16) — **no** importa
directamente ninguna de las dos suites de gates; el expediente lo agrupó de forma imprecisa.

**Conclusión verificada de a):** las dos suites siguen vivas y ambas alcanzables desde
`main.py`, pero el acoplamiento directo entre ellas pasa por **un solo fichero-bisagra**:
`services/validation/legacy_revalidation_service.py:31`. Cortar esa línea (mover
`legacy_revalidation_service` a depender de un registro de gates único, movimiento 1 del
expediente) es el corte de mayor apalancamiento de todo el grafo para este problema concreto.

## 2b. Acoplamiento entrante/saliente por paquete

Tabla calculada sobre el grafo (aristas fichero-a-fichero, agregadas al prefijo de paquete de 2
niveles, p. ej. `services.api`). "in-files"/"out-files" = nº de ficheros distintos en el borde,
no nº de aristas.

| Paquete | Módulos | LOC | Aristas entrantes | Ficheros que entran | Aristas salientes | Ficheros destino |
| :--- | ---: | ---: | ---: | ---: | ---: | ---: |
| `services/api` | 128 | 29.478 | 93 | 50 | 67 | 31 |
| `services/validation` | 27 | 6.010 | 41 | 31 | 22 | 13 |
| `services/discovery` | 14 | 3.174 | 40 | 23 | 11 | 7 |
| `services/portfolio` | 8 | 1.462 | 8 | 6 | 19 | 5 |
| `services/sqx_bridge` | 7 | 801 | 6 | 3 | 4 | 2 |
| `services/lineage` | 1 | 237 | 1 | 1 | 6 | 2 |
| `services/data_ingestion` | 3 | 682 | 4 | 3 | 0 | 0 |
| `services/sync` | 1 | 303 | 1 | 1 | 2 | 2 |
| `services/ops` | 2 | 275 | 0 | 0 | 0 | 0 |
| `services/exploitation_engines` *(equivalente a "fondeo")* | 4 | 774 | 3 | 2 | 4 | 2 |

**`services/meta` y `services/fondeo` NO existen como paquetes** — se comprobó con
`find services -maxdepth 2 -iname "*meta*" -o -iname "*fondeo*"`. Sus equivalentes reales:

- **"Meta"** vive dentro de `services/portfolio/` (`meta_strategy_engine.py`,
  `meta_strategy_pipeline.py`, `meta_ensemble_service.py`, `autonomous_meta_daemon.py`) — de ahí
  la fila de `services/portfolio` en la tabla, que YA es la mejor aproximación a M4.
- **"Fondeo"** no tiene hogar único: está disperso en `services/exploitation_engines/prop_firm_engine.py`
  (774 LOC), `services/validation/prop_firm_risk_engine.py`, `services/api/app/api/prop_firms.py`
  + `services/api/app/db/seed_prop_firms.py` (dentro del monolito), y 4 ficheros más dentro de
  `services/api/app/factory/` (`five_day_challenge_engine.py` 437 LOC,
  `portfolio_sprint_engine.py` 98 LOC, `ultra_risk_controlled_engine.py` 998 LOC,
  `ultra_portfolio_engine.py` 206 LOC — verificado con
  `grep -rli "fondeo\|prop_firm" services --include="*.py"`, 65 ficheros con alguna mención,
  pero el *hogar* de la lógica de valoración son los 8 ficheros citados). Esto es un hallazgo en
  sí mismo: **hoy "mejorar la valoración fondeo" obliga a tocar como mínimo 3 paquetes distintos**
  (`exploitation_engines`, `validation`, `api/app/factory`), justo el síntoma que el requisito de
  Emilio quiere eliminar.

Nota sobre `services/ops`: 0 aristas entrantes y 0 salientes — no está conectado al grafo de
imports de ningún otro módulo interno (probablemente se invoca como script/servicio systemd, no
como librería importada). Dato para verificar antes de decidir su destino en la modularización.

## 2c. Ciclos de import

**Ciclo fichero-a-fichero directo (SCC de tamaño >1) encontrado — solo 1 en todo el árbol:**

```
services/export/excel_master_catalog.py:35   [diferido-en-función]
    from services.api.app.api.certified_summary_router import _scorecard
services/api/app/api/certified_summary_router.py:22  [top-level]
    from services.export.excel_master_catalog import build_master_catalog_csv, build_master_catalog_xlsx
```

`excel_master_catalog.py` importa (en función, para esquivar el ciclo en tiempo de import) una
función **privada** (`_scorecard`) de un router HTTP; y ese mismo router importa el exportador a
nivel de módulo. Es la coupling más frágil detectada: un cambio de firma en una función privada
de un router rompe un exportador Excel.

**Ciclos DIRECTOS de 2 paquetes (A→B y B→A ambos existen) — 15 en total**, listados con su
arista más representativa de cada sentido:

| Ciclo | A→B (aristas) | ejemplo A→B | B→A (aristas) | ejemplo B→A |
| :--- | ---: | :--- | ---: | :--- |
| `services.api` ↔ `services.portfolio` | 4 | `main.py:46` `portfolio_router` | 13 | `autonomous_meta_daemon.py:14` `db.database.CandidateModel` |
| `services.policy` ↔ `services.api` | 7 | `impact_analyzer.py:21` `factory.quality_gates.*` | 1 | `policy_router.py:13` |
| `services.discovery` ↔ `services.validation` | 3 | `discovery_validation_pipeline.py:35` `event_backtest_engine` | 2 | `legacy_revalidation_service.py:28-29` `ultra_discovery`, `funding_discovery` |
| `services.semantic_ai` ↔ `services.validation` | 1 | `autonomous_discovery_engine.py:44` | 3 | `engines/gate_09...py:10`, `gate_10...py:9`, `gate_11...py:10` `semantic_engine.*` |
| `services.api` ↔ `services.optimization` | 4 | `research_lab_router.py:18` | 7 | `continuous_research_daemon.py:16` `db.database.*` |
| `services.sqx_bridge` ↔ `services.api` | 6 | `sqx_router.py:14` | 4 | `backfill_sqx_oos.py:16` `db.database.*` |
| `services.discovery` ↔ `services.api` | 4 | `research_router.py:19` | 4 | `discovery_validation_pipeline.py:36,39` |
| `services.data` ↔ `services.api` | 6 | `real_data_router.py:537` | 1 | `dataset_repository.py:15` `config.DATA_DIR` |
| `services.semantic_ai` ↔ `services.api` | 3 | `research_lab_router.py:19` | 6 | `autonomous_discovery_engine.py:39-41` |
| `services.api` ↔ `services.queue` | 1 | `job_queue_router.py:20` | 1 | `durable_job_queue.py:25` `config.STATE_DB_PATH` |
| `services.lineage` ↔ `services.api` | 1 | `lineage_router.py:19` | 5 | `lineage_service.py:20` (5 modelos ORM en una línea) |
| `services.api` ↔ `services.validation` | 4 | `candidates_router.py:20` | 6 | `candidate_registry.py:21` `config.STATE_DB_PATH` |
| `services.backtest` ↔ `services.discovery` | 1 | `fast_engine_adapter.py:78` | 2 | `funding_research_loop.py:17`, `strategy_research_loop.py:23` |
| `services.backtest` ↔ `services.api` | 1 | `routes.py:1071` | 1 | `fast_engine_adapter.py:47` `data_feed.feed_loader` |
| `services.export` ↔ `services.api` | 4 | `certified_summary_router.py:22` | 2 | ver ciclo fichero-a-fichero de arriba |
| `services.sync` ↔ `services.api` | 1 | `firebase_sync_router.py:21` | 1 | `firebase_sync_manager.py:26` `config.STATE_DB_PATH` |

**Ciclo global a nivel de paquete:** cuando se calculan los componentes fuertemente conexos
(Tarjan) sobre el grafo condensado por paquete, **22 de los ~24 paquetes de `services/` +
`scripts.mine` + `scripts.herramientas` caen en un único SCC gigante**:
`services.api, services.portfolio, services.export, services.sync, services.monitoring,
services.paper, services.policy, services.lineage, services.queue, services.optimization,
services.sqx_bridge, services.strategy_core, services.backtest, services.exploitation_engines,
services.validation, services.core, services.semantic_ai, services.discovery,
services.background_searcher, services.data, scripts.mine, scripts.herramientas`.

Es decir: **prácticamente todo el backend es un solo ciclo de dependencias a nivel de paquete**.
La causa raíz medida son dos módulos-hub dentro de `services/api/app/`:

- `services.api.app.config` (constantes `STATE_DB_PATH`, `DATA_DIR`, `LEARNING_DB_PATH`):
  **33 aristas entrantes** desde 25 ficheros externos a `services/api` (14 scripts + 11 de
  `services/`, incluidos `core`, `queue`, `data`, `sync`, `discovery`, `validation`,
  `semantic_ai`, `optimization`, `portfolio`, `sqx_bridge`, `background_searcher`).
- `services.api.app.db.database` (modelos ORM): **23 aristas entrantes** desde 6 paquetes
  (`portfolio` 11, `lineage` 5, `sqx_bridge` 3, `optimization` 2, `export` 1, `policy` 1).

Y en dirección opuesta, `services/api` importa de vuelta routers/servicios de casi todos esos
mismos paquetes para montarlos en `main.py`. Ese vaivén (api hacia fuera para exponer routers,
y casi todo el resto hacia dentro para leer `config`/`database`) es lo que cierra el
macro-ciclo. Un caso adicional fuera de `services/api`: **`services/data/session_calendar.py:47`
importa `scripts.herramientas.consolidar_dukascopy`** — un servicio dependiendo de un script,
único caso de esa dirección en todo el grafo, y es el eslabón que mete a `services.data` y a
`scripts.*` en el mismo SCC.

## 2d. Frontera de un futuro `services/improvement/`

**Código de "mejora" que ya existe hoy** (buscado por nombre de fichero con
`find services scripts -iname "*improv*" -o -iname "*optimiz*" -o -iname "*research_loop*"`):

| Fichero | LOC | Imports internos propios |
| :--- | ---: | :--- |
| `services/api/app/factory/deep_strategy_improver.py` | 168 | **ninguno** (solo stdlib) |
| `services/api/app/factory/optimizer.py` | 105 | **ninguno** (solo stdlib) |
| `services/api/app/factory/optimization_loop.py` | 227 | `services.api.app.factory.quality_gates` (línea 10) |
| `services/api/app/factory/quality_gates.py` | 173 | **ninguno** (solo stdlib) |
| `services/optimization/universal_optimizer_engine.py` | — | 8 destinos internos distintos (línea 23-38, 201) |
| `services/optimization/expert_refinement_loop.py` | — | 6 destinos internos (línea 29-36, 162, 168) |
| `services/optimization/continuous_research_daemon.py` | — | 5 destinos internos (línea 16-21) |
| `services/optimization/quantitative_arsenal.py` | — | **ninguno** interno |
| `services/discovery/funding_research_loop.py` | — | 5 destinos internos (línea 17-21) |
| `services/discovery/strategy_research_loop.py` | — | 6 destinos internos (línea 23-28) |

**Hallazgo importante:** el núcleo algorítmico de mejora que vive dentro del monolito
(`deep_strategy_improver.py` + `optimizer.py` + `optimization_loop.py` + `quality_gates.py`,
673 LOC en `services/api/app/factory/`) **ya es prácticamente puro** — 3 de los 4 ficheros no
importan NADA del resto del proyecto, y el cuarto (`optimization_loop.py`) solo depende del
propio `quality_gates.py` (que a su vez tampoco importa nada interno). Esto confirma que el
Movimiento 2 del expediente ("lo nuevo nace en su dominio, coste cero") es viable hoy mismo para
esta porción concreta: **movimiento mecánico sin tocar semántica**.

En cambio, `services/optimization/*` (el otro gran bloque de "mejora", `universal_optimizer_engine.py`
+ `expert_refinement_loop.py` + `continuous_research_daemon.py`) **NO** cumple la frontera
propuesta ("solo `contracts/` + registro de gates"). Importa hoy, con línea exacta:

- `services.discovery.ultra_discovery`, `services.discovery.funding_discovery` (líneas 23-24 /
  29-30 de `universal_optimizer_engine.py` / `expert_refinement_loop.py`) — dependencia directa
  de M1 (generación), no solo de contratos.
- `services.validation.engine.event_backtest_engine` (línea 26 / 32) — el motor SSOT, aceptable
  si se considera parte del "registro de gates canónico", pero hoy es un import directo al
  paquete de la suite A, no a un puerto.
- `services.api.app.validation.gates.gate_pipeline_orchestrator` (línea 27 / 33) — **suite B
  completa**, viola la frontera de forma directa: mejora depende del monolito `api`.
- `services.validation.certification_registry` (línea 28 / 34).
- `services.data.instrument_cost_registry` (línea 29, y línea 168 diferido en
  `expert_refinement_loop.py`).
- `services.api.app.config` (línea 30 / 35) — constantes de rutas, mismo hub que causa el
  macro-ciclo de 2c.
- `services.semantic_ai.semantic_engine` (línea 38 / 36, 6 nombres importados en una línea) —
  dependencia de M2↔gate_10/11 (debate semántico), cruzada.
- `services.optimization.quantitative_arsenal` (interna al propio paquete, no cuenta como
  violación).
- Solo en `universal_optimizer_engine.py`: `services.api.app.validation.gates.gate_10_agent_debate`
  (línea 201, diferida).

`services/discovery/*_research_loop.py` (funding/strategy) tampoco cumplirían la frontera: importan
`services.backtest.fast_engine_adapter`, `services.validation.engine.event_backtest_engine` y
varios módulos hermanos de `discovery` — coherente, porque estos dos ficheros son en realidad
generación/minería (M1), no mejora (M2); su nombre ("research_loop") es engañoso respecto a su
función real medida por el grafo.

**Conclusión de d):** si `services/improvement/` naciera hoy con la regla estricta
"solo `contracts/` + registro de gates", **podrían entrar sin cambios los 4 ficheros de
`services/api/app/factory/` citados arriba (673 LOC)**. Todo lo demás que hoy se llama
"optimización"/"mejora" (`services/optimization/*`, ~1.582 LOC) tiene entre 5 y 8 imports
externos a la frontera propuesta cada uno y necesitaría refactorizar primero sus accesos a
`api.config`, `api.db.database` y a la suite B de gates para poder migrar sin romper semántica.

## 2e. Los 4 módulos M1-M4: qué pertenecería a cada uno y coste de romper fronteras

**Aviso de método:** la asignación de ficheros a M1-M4 es una **hipótesis de trabajo por
semántica de nombre/ubicación** (igual que reconoce el propio expediente en su §6 — "M1-M4...
su frontera exacta queda pendiente"), no un hecho verificado línea a línea salvo donde se cita
evidencia concreta. Los RECUENTOS DE ARISTAS sí son datos medidos sobre el grafo, no
estimaciones.

| Módulo hipotético | Ficheros | LOC | Aristas cruzando frontera (medidas) |
| :--- | ---: | ---: | ---: |
| **M1 Generación/SQX** — `sqx_bridge/`, `discovery/`, `strategy_core/`, `backtest/`, `data_ingestion/`, `engine/`, `api/app/dsl/`, + 13 ficheros de `api/app/factory/` (`seed_factory`, `genetic`, `grammar`, `campaign_planner/pipeline/suite`, `fast_engine_campaign`, `repairer`, `selection`, `ai_learning_engine`, `intelligent_quant_miner`, `autopilot`, `orchestrator`) | 52 | 10.924 | **174** |
| **M2 Mejora** — `optimization/`, `semantic_ai/`, + 8 ficheros de `api/app/factory/` (`optimizer`, `optimization_loop`, `deep_strategy_improver`, `quality_gates`, `adversarial_validation`, `robustness_verifier`, `strategy_evidence`, `continuous_search_daemon`) | 21 | 5.915 | **112** |
| **M3 Valoración fondeo** — `exploitation_engines/`, `validation/prop_firm_risk_engine.py`, `api/app/api/prop_firms.py`, `api/app/db/seed_prop_firms.py`, `api/app/core/market_matrix.py`, + 4 ficheros de `api/app/factory/` (`five_day_challenge_engine`, `portfolio_sprint_engine`, `ultra_risk_controlled_engine`, `ultra_portfolio_engine`) | 12 | 7.208 | **22** |
| **M4 Meta** — `portfolio/`, `lineage/` | 9 | 1.699 | **34** |
| *(referencia)* Puertas (ambas suites + motor + registries) | 41 | 8.560 | 84 |
| *(referencia)* Resto de `api/app/` sin clasificar arriba (routers HTTP, `db/database.py`, `data_feed/`, `export/`, `core/` excepto market_matrix, `config.py`...) | 83 | 15.161 | 242 |

Notas de la tabla:

- `services/policy/impact_analyzer.py` (264 LOC) **se dejó fuera deliberadamente** de M1-M4: es
  un simulador de impacto de cambios de UMBRALES de gates sobre cohortes ULTRA+FONDEO
  (`contracts.lineage_contracts.PolicyImpactRequest`, ver docstring), gobernanza de políticas de
  gate, no valoración de fondeo ni mejora. Es un quinto tipo de código que el mapeo M1-M4 de
  Emilio no cubre y habría que decidir dónde vive.
- El "resto de api/app" que quedaría tras repartir M1-M4 sigue siendo **15.161 LOC en 83
  ficheros** — más grande que M1+M2+M3+M4 juntos (25.746 LOC pero en 94 ficheros ya fuera del
  monolito). Es decir: **repartir M1-M4 no basta para deshacer el monolito**; sin vaciar además
  routers/DB/export/data_feed (Movimiento 3 del expediente), `api/` seguiría siendo el paquete
  más grande con diferencia.
- El coste real por módulo (aristas a romper o reencauzar por contrato) es, de mayor a menor:
  **M1 (174) > M2 (112) > M4 (34) > M3 (22)**. M1 es el más caro de extraer porque hoy está
  entrelazado con `api` (65 aristas api→M1, ejemplo `services/api/app/api/research_router.py:19`)
  y con M2 (21 aristas M1→M2, ejemplo `services/api/app/factory/autopilot.py:34`). M3 es,
  sorprendentemente, el más barato de aislar — su código ya está relativamente contenido, salvo
  el acoplamiento a `api.app.db.database` vía `api/app/api/prop_firms.py` y a `market_matrix.py`.

## 2f. Verificación independiente de las 29.478 LOC de `services/api/`

Medido con dos comandos independientes (mismo resultado exacto, sin depender del script AST):

```
$ find services/api -name "*.py" -not -path "*__pycache__*" | wc -l
128
$ find services/api -name "*.py" -not -path "*__pycache__*" -print0 | xargs -0 cat | wc -l
29478
$ find services/api -name "*.py" -not -path "*__pycache__*" -print0 | xargs -0 wc -l | tail -1
  29478 total
```

**CONFIRMA exactamente la cifra del expediente (29.478 LOC, 128 ficheros).** El propio grafo AST
(suma de `len(text.splitlines())` por fichero) coincide con el mismo total en su nodo agregado
`services.api` de la tabla 2b. También se verificó de paso la cifra de `services/validation/`
citada en el expediente (6.010 LOC): coincide exacta con la misma metodología.

**Censo de módulos homónimos — ampliado respecto al expediente.** El expediente citaba 2 pares
verificados; con `find ... -exec basename {} \; | sort | uniq -c` sobre el árbol completo
aparecen **3 pares** (excluyendo `__init__.py`, 32 apariciones esperadas por diseño):

| Basename duplicado | Rutas | LOC | ¿Contenido? |
| :--- | :--- | ---: | :--- |
| `database.py` | `services/api/app/database.py` / `services/api/app/db/database.py` | 50 / 831 | Distinto: el primero es bootstrap de engine SQLite + healthcheck; el segundo son los modelos ORM. No son duplicados de lógica, pero el nombre idéntico en el mismo árbol (`api/app/`) es una fuente real de confusión. |
| `gate_03_trade_significance.py` | `services/api/app/validation/gates/` (suite B) / `services/validation/engines/` (suite A) | 51 / 59 | LOC distinto → implementaciones que ya han divergido, exactamente el riesgo que señala el expediente para F00.1. |
| `version_control_manager.py` | `services/version_control_manager.py` / `scripts/herramientas/version_control_manager.py` | 265 / 276 | LOC distinto → también divergentes; no estaba en el censo preliminar del expediente. |

## 3. Ranking de los 10 cortes de mayor impacto

Ordenados por impacto medido (nº de aristas de macro-ciclo que la línea cierra, y si es la
**única** arista saliente del paquete origen — cortarla saca al paquete entero del SCC gigante
de 2c sin tocar nada más de ese paquete):

1. **`services/core/runtime_paths.py:12`** — `from services.api.app.config import STATE_DB_PATH`.
   Es la **única** arista saliente de todo `services/core` (3 módulos, 232 LOC; 1 sola arista
   de salida en la tabla 2b). `services/core` es importado por 7 ficheros de otros paquetes
   (`validation`, `monitoring`, `semantic_ai`, `exploitation_engines`, `api`...). Cortarla (mover
   la constante de ruta, o inyectarla) saca a `services.core` entero del ciclo gigante.

2. **`services/queue/durable_job_queue.py:25`** — `from services.api.app.config import STATE_DB_PATH`.
   Mismo patrón: única arista saliente de `services/queue` (1 módulo). Cierra el tramo
   `api → monitoring → queue → api` del macro-ciclo.

3. **`services/data/session_calendar.py:47`** — `from scripts.herramientas.consolidar_dukascopy import PAUSA_DIARIA_MAX_HOURS`.
   Único caso en todo el grafo de un **servicio** importando un **script**; `scripts.herramientas`
   a su vez importa `scripts.mine`, que importa `services.api`/`services.validation`/`services.discovery`,
   cerrando el macro-ciclo. `services/data` tiene 23 aristas entrantes desde 11 ficheros — es un
   paquete "de infraestructura" que no debería depender de `scripts/`.

4. **`services/lineage/lineage_service.py:20`** — `from services.api.app.db.database import CandidateModel, StrategyModel, DatasetModel, InstrumentRuleSnapshotModel, AccountFeeSnapshotModel`.
   Es la única razón por la que el ciclo directo de 2 paquetes `services.api ↔ services.lineage`
   existe (`api`→`lineage` es solo 1 arista, `services/api/app/api/lineage_router.py:19`).
   `lineage` (237 LOC, 1 solo fichero) es de los candidatos más baratos a aislar del repo:
   sustituir estos 5 nombres por un contrato de lectura rompe el ciclo entero.

5. **`services/sync/firebase_sync_manager.py:26`** — `from services.api.app.config import STATE_DB_PATH`.
   1 de las 2 aristas salientes totales de `services/sync`; junto al import diferido de la línea
   237 del mismo fichero (`services.semantic_ai.failure_knowledge`) es todo lo que ata a `sync`
   al resto del grafo.

6. **`services/sqx_bridge/backfill_sqx_oos.py:16`** — `from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel`.
   El expediente ya señalaba que `sqx_bridge` "se importa desde 5 sitios fuera de su paquete";
   esta línea es la dirección inversa — la única vía por la que `sqx_bridge` (candidato natural
   a vivir dentro de M1) depende de los modelos ORM del monolito en vez de un contrato.

7. **`services/policy/impact_analyzer.py:21` y `:29`** — `from services.api.app.factory.quality_gates import (...)` (6 nombres) y `from services.api.app.db.database import CandidateModel`.
   `services/policy` tiene sus 7 aristas salientes **completas** apuntando a `api` (100% del
   out-degree del paquete) — y encima a un submódulo interno no estable (`factory/quality_gates`),
   no a un contrato. Es el paquete con la proporción de acoplamiento hacia `api` más alta de
   toda la tabla 2b.

8. **`services/export/excel_master_catalog.py:35` y `:56`** — `from services.api.app.api.certified_summary_router import _scorecard, get_certified_strategies_endpoint` (diferido-en-función).
   Cierra el **único ciclo fichero-a-fichero directo** de todo el árbol (sección 2c). Importar
   una función privada (`_scorecard`, prefijo `_`) de un router HTTP desde un exportador de
   Excel es el acoplamiento más fino y más frágil detectado: cualquier renombrado interno del
   router rompe el exportador sin que su firma pública haya cambiado.

9. **`services/discovery/discovery_validation_pipeline.py:36`** — `from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator`.
   Ata M1 (generación/discovery) directamente a la suite B de gates anidada dentro de `api`; es
   el mismo patrón que produce el nudo de la pregunta 2a, y `discovery_validation_pipeline.py`
   es el candidato más citado del expediente para F00/F00.1.

10. **`services/portfolio/autonomous_meta_daemon.py:14`, `meta_ensemble_service.py:13`, `meta_strategy_pipeline.py:104`, `portfolio_router.py:11`** — las 4 líneas que importan `services.api.app.db.database` (11 de las 13 aristas `portfolio→api`, la mayor concentración de cualquier paquete hacia el monolito en la tabla 2b).
    `services/portfolio` es el candidato más claro a M4/meta y hoy es, en términos absolutos, el
    paquete con más aristas de dependencia directa hacia `api` de todo el grafo (13). Mover los
    modelos ORM relevantes a un contrato de persistencia propio de `portfolio` (o a un puerto
    inyectado) es el corte de mayor volumen absoluto de la lista.

## 4. Ficheros de evidencia

- `orchestration/results/grafo_imports_2026-09-01.json` — grafo completo: 310 nodos
  (módulo, ruta, LOC, `is_package`, paquete de 2 niveles), 1.003 aristas (origen, destino,
  `src_path`, número de línea, tipo, texto crudo del import).
- Este informe.
- Ningún otro fichero del repo fue creado ni modificado. Scripts de análisis auxiliares
  (generador del grafo + consultas ad-hoc) quedaron únicamente en el directorio scratchpad de
  la sesión, fuera del repositorio.

## 5. Preguntas NO resueltas

Ninguna de las preguntas a-f quedó sin evidencia. Dos matices declarados explícitamente como
límites del método, no como huecos:

- La clasificación M1-M4 (2e) es una hipótesis razonada por nombre/ubicación de fichero, no una
  lectura línea a línea de los 94 ficheros implicados — así se marca en el propio apartado. Los
  recuentos de aristas que dependen de esa clasificación heredan el mismo grado de confianza.
- No se comprobó si `services/ops` (0 aristas en el grafo) es código muerto o se invoca fuera
  del grafo de imports de Python (p. ej. como entrypoint de systemd/cron); solo se reporta el
  hecho medido (aislado del grafo de imports).
