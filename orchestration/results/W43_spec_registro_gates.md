# W43 — Especificación del registro de gates versionados (Movimiento 1 del expediente I7)

Fecha: 2026-09-01 · Carril: GATES · Alcance: **solo lectura de código**. No se ha creado ni
modificado ningún fichero de `services/`, `contracts/` ni `tests/` en esta ola — el territorio
reservado (`services/validation/registry/**`, `contracts/` nuevos, `tests/test_gate_registry_*.py`)
queda para la ola de implementación que siga a este sello. Único artefacto de esta ola: este
documento.

Fuentes leídas enteras antes de escribir: `orchestration/reviews/investigacion_I7_arquitectura_codigo.md`
(con su §7), `orchestration/results/grafo_imports_2026-09-01.md`, `AUTHORITY_GRAPH.md`, las dos
suites completas de gates (22 ficheros + 2 orquestadores), `contracts/gate_directory.py`,
`contracts/snapshots/evidence_record.py`, `contracts/snapshots/strategy_snapshot.py`,
`services/validation/certification_registry.py`, `services/validation/legacy_revalidation_service.py`
y el tramo de `scripts/mine.py` que certifica (líneas 895-1234).

---

## 1. Tabla de los 11 gates — umbrales suite A vs suite B, con ruta:línea

**Metodología:** para cada gate se leyó el fichero completo de ambas suites y se citan los
umbrales tal como aparecen en el `__init__`/lógica de `evaluate()`. Se añade una tercera columna
con `contracts/gate_directory.py` (el catálogo que expone `gates_router` a la web en
`/api/v1/gates/*`, consumido por `apps/web/app/gates/[slug]/GateDetailClient.tsx:109`) porque es
una **tercera fuente de números**, independiente de ambas suites, y las discrepancias con ella
son un hallazgo en sí mismo (sección 1.2).

| # | Nombre | Suite A — `services/validation/engines/` (umbral, ruta:línea) | Suite B — `services/api/app/validation/gates/` (umbral, ruta:línea) | `gate_directory.py` (ruta:línea) | ¿Coinciden A y B? |
|---|---|---|---|---|---|
| 1 | Ingesta/Sanidad OHLCV | `max_allowed_gaps=5` (nº de huecos), `max_allowed_corrupt=0` — `gate_01_ingest_sanity.py:27-29` | `min_required` por timeframe (300/200/150/50 velas según tf), `corrupt==0`, `out_of_order==0`, huecos `<= 2%` del total — `gate_01_data_ingest.py:39-41,110` | `max_gap_pct=2.0`, `min_bars=1000` — `contracts/gate_directory.py:14` | **NO.** A cuenta huecos en unidades absolutas (≤5); B en % del total (≤2%) y además exige un mínimo de velas que A no tiene. El directorio (min_bars=1000) no coincide con ninguna de las dos. |
| 2 | Backtest con costes | Solo `net_profit_usd > 0` (`min_net_profit=0.0`); **sin umbral de Profit Factor** — `gate_02_deterministic_backtest.py:30-40,96` | `net_pf >= 1.10` **y** `net_pnl > 0` — `gate_02_cost_backtest.py:64` | `min_profit_factor=1.25` — `contracts/gate_directory.py:21` | **NO.** A no exige ningún PF mínimo (una estrategia con PF 1.01 y \$1 de beneficio pasaría A); B exige ≥1.10. Ninguna de las dos coincide con el 1.25 documentado. |
| 3 | Significancia de trades | `total_trades(IS+OOS) >= 40`, `oos >= 20`, `trades/mes >= 2.5`; **sin distinción de ruta** — `gate_03_trade_significance.py:23-31` | `is >= 15/30` y `oos >= 10/20` (ULTRA/FONDEO) **más** un chequeo de dependencia de outliers (top-2 trades ≤85%/50% del PnL ganador) — `gate_03_trade_significance.py:26-32` (suite B) | `min_trades_is=30`, `min_trades_oos=15` — `contracts/gate_directory.py:28` | **NO — divergencia confirmada y la más profunda de las 11.** No es solo el número: B introduce una dimensión (outlier-dependency) que A no tiene, y B es route-aware (ULTRA/FONDEO) mientras A es un único umbral fijo. El directorio no coincide exactamente con ninguna (min_oos=15 no es ni el 20 de A ni el 10/20 de B). |
| 4 | Walk-Forward Efficiency | `min_wfe=0.50`, `min_oos_profit_factor=1.20` (chequeado dentro del propio gate), `max_degradation_pct=50.0` — `gate_04_walk_forward_efficiency.py:24-32` | `avg_wfe>=0.40` **y** `consistency_pct>=40.0`; sin chequeo de PF OOS dentro del gate — `gate_04_walk_forward.py:106` (evidencia interna dice erróneamente `"min_wfe_required": 0.50` en la línea 127, que **no** es el umbral realmente aplicado en la 106 — bug propio de B) | `windows=5`, `min_wfo_efficiency=0.60` — `contracts/gate_directory.py:35` | **NO.** Umbral distinto (0.50 vs 0.40) y A exige además un PF OOS mínimo que B no comprueba en este gate. El directorio (0.60) no coincide con ninguna. |
| 5 | Monte Carlo / ruina | `ruina<=1.0%`, `p95 DD<=8.0%`, DD-de-ruina definido en `10.0%` — `gate_05_monte_carlo_stress.py:25-30` | `ruina<=5.0%(ULTRA)/0.5%(FONDEO)`, `DD95<=80.0%(ULTRA)/4.0%(FONDEO)` — `gate_05_monte_carlo.py:31,114` | `simulations=1000`, `confidence_pct=95.0` (no publica el umbral de ruina/DD) — `contracts/gate_directory.py:42` | **NO.** Los rangos ni se solapan entre rutas: B permite hasta 80% de DD simulado en ULTRA (5 veces más laxo que el 8% fijo de A) y es 10x más laxo en ruina para ULTRA (5% vs 1% de A). |
| 6 | Estrés de fricción 3x | `min_stressed_pf=1.10`, `min_retention_pct=65.0` — `gate_06_friction_stress.py:24-27` | Aprueba si `>=1 (ULTRA) / >=2 (FONDEO)` escenarios de estrés superan un umbral interno (no expone un único PF) — `gate_06_stress_slippage.py:77-78` | `stress_factor=3.0`, `min_stressed_pf=1.05` — `contracts/gate_directory.py:49` | **NO — formulación distinta.** A calcula un único PF-bajo-estrés; B cuenta cuántos de N escenarios pasan. No son la misma métrica, no solo el número difiere. |
| 7 | Cobertura de régimen | `min_alignment_score=65.0`, pérdida catastrófica si `<-$1000` en cualquier régimen — `gate_07_market_regime_coverage.py:25-28` | `min_active_required=2` regímenes con desempeño activo/positivo — `gate_07_regime_coverage.py:189-190` | `min_profitable_regimes=2` — `contracts/gate_directory.py:56` | **NO — formulación distinta.** A usa un score continuo 0-100 con corte catastrófico en USD; B cuenta regímenes activos. El directorio coincide con B en el "2", no con A. |
| 8 | Deflated Sharpe Ratio | Estadístico DSR **crudo** (z-score), `min_dsr=1.5` — `gate_08_deflated_sharpe.py:71-76,140` | **Probabilidad** DSR (0-1), `dsr_prob>=0.50` **y** `raw_sharpe>0` — `gate_08_dsr_ratio.py:142` | `min_dsr=2.0` — `contracts/gate_directory.py:63` | **NO — ni la escala coincide.** A compara contra 1.5 en escala de estadístico; B compara 0.50 en escala de probabilidad. Son dos métricas distintas con el mismo nombre. El directorio (2.0) no es la escala de ninguna de las dos. |
| 9 | Novedad / anti-overfitting | Distancia AST estructural, `min_novelty_score=70.0` — `gate_09_novelty_antioverfit.py:26-31` | Robustez por perturbación paramétrica: `min_dof_required=10.0/15.0`, `min_stability_required=50.0/60.0%`, `max_params_allowed=8` — `gate_09_novelty_antifit.py:120-121,218-223` | `min_ast_distance=0.15` — `contracts/gate_directory.py:70` | **NO — métodos completamente distintos.** A mide distancia sintáctica contra `FailureKnowledgeDB`; B mide estabilidad de resultados ante perturbación de parámetros. El directorio describe el método de A (AST), pero la que certifica es B (perturbación) — ver §1.2. |
| 10 | Debate multi-agente | `min_consensus_score=75.0` — `gate_10_semantic_ai_debate.py:24-25` | Fórmula ponderada (`research*0.25 + risk*0.30 + stat*0.15 + exec*0.15 + adversarial*0.15`), `>=40.0` — `gate_10_agent_debate.py:137-140` | `min_consensus_score=75.0` — `contracts/gate_directory.py:77` | **NO — la más grave en magnitud.** El directorio que ve la web (75.0) coincide con A, **no con B**, que es casi la mitad de exigente (40.0) y es la que realmente certifica (§2). Un usuario leyendo la documentación web cree que el corte es 75; el corte real que usa `scripts/mine.py` es 40. |
| 11 | Reconciliación Nautilus / liquidación | `max_cross_correlation=0.35`, `min_diversification_ratio=1.05`, `min_combined_sharpe=2.0` — `gate_11_ensemble_synergy.py:29-37` | `min_dist_liquidation_pct>=2.0(ULTRA)/20.0(FONDEO)` — `gate_11_nautilus_event.py:119` | `min_liquidation_buffer_pct=5.0` — `contracts/gate_directory.py:84` | **NO — miden cosas distintas.** A mide correlación/diversificación/Sharpe combinado entre estrategias de una cartera; B mide distancia a liquidación de una sola candidata frente a su apalancamiento. El directorio (5.0) no coincide con el 2.0 ni el 20.0 de B, y B ni siquiera calcula lo que A calcula. |

### 1.1 Veredicto sobre la afirmación previa "difieren en el gate 3"

**CONFIRMADA, y ampliada por evidencia nueva de este informe: la divergencia no está aislada en
el gate 3.** El gate 3 sí diverge (umbral fijo total-40/oos-20 en A vs. umbral route-aware
15-30/10-20 más un chequeo de dependencia de outliers en B, inexistente en A), pero de los 11
gates auditados **los 11 tienen umbrales o fórmulas distintas entre A y B**, y en al menos 4
casos (gates 6, 7, 9, 11) no es solo el número: es una **métrica matemáticamente distinta** bajo
el mismo nombre de gate. El caso más grave para el usuario final no es el 3, es el **gate 10**:
la web documenta 75.0 (que coincide con A) pero el pipeline que certifica exige solo 40.0 (B) —
ver §1.2 y §2.

### 1.2 Hallazgo adicional: `contracts/gate_directory.py` no es la fuente de verdad de ningún umbral real

`GATES_DIRECTORY` (`contracts/gate_directory.py:8-86`) es lo que `gates_router.py` sirve a
`/api/v1/gates/{slug}` y lo que `apps/web/app/gates/[slug]/GateDetailClient.tsx:109` renderiza
como "parámetros" del gate en la UI. Se verificó gate a gate (tabla de arriba): **en ningún caso
sus `default_params` coinciden exactamente con los umbrales realmente ejecutados por la suite que
certifica (B)**; en 2 de los 11 casos (gate 3, gate 10) coincide en cambio con la suite que **no**
certifica (A). Es decir: hoy la web puede mostrarle a un humano un umbral que no es el que decide
si su estrategia se certifica. Esto es un defecto de exactitud de la UI, no solo de arquitectura,
y debe corregirse cuando el registro exista (la solución natural es que `gates_router.py` deje de
leer `GATES_DIRECTORY` estático y lea `VERSION`+umbrales desde el registro — ver §3.4).

---

## 2. ¿Cuál suite certifica? Trazado del flujo completo

**Suite B (`services/api/app/validation/gates/`) es la canónica que certifica.** Trazado
completo, con ruta:línea, desde `scripts/mine.py` hasta la escritura del estado certificado:

1. `scripts/mine.py:934-940` importa `EventBacktestEngine` (motor SSOT), **`GatePipelineOrchestrator`
   de la suite B** (no la A) y `CertificationRegistry`, e instancia los tres.
2. Tras pasar los filtros de embudo IS/VAL/OOS (líneas 998-1021), `scripts/mine.py:1068` llama
   `gates_orchestrator.run_all_gates(...)` — el método de la suite B
   (`gate_pipeline_orchestrator.py:64`), que ejecuta los 11 gates de B (`gate_pipeline_orchestrator.py:99-115`),
   **persiste físicamente cada `EvidenceRecord` con hash SHA-256** en
   `data/evidence/{strategy_id}/gate_XX_*.json` (`gate_pipeline_orchestrator.py:117-171`) y
   devuelve `gates_passed_count`/`overall_score`.
3. `scripts/mine.py:1093` pasa ese resultado a `cert_registry.certify_candidate(...)`
   (`certification_registry.py:103-134`), que exige `gates_passed_count == 11` (además de sus
   propios umbrales de PF/DD/trades — un macro-gate adicional, fuera del alcance de los 11 gates
   de este informe) para fijar `is_certified=True`.
4. Si `verdict.is_certified`, `scripts/mine.py:1212` llama `save_certified_candidate_to_db(...)`,
   que escribe `scorecard_payload` (incluyendo `gates_eval.get("gates", [])`, es decir, **la
   salida cruda de la suite B**) en `CandidateModel.scorecard_json` vía SQLAlchemy
   (`scripts/mine.py:635-686` para la firma de la función; la escritura real ocurre en su cuerpo,
   no leído línea a línea en esta ola por no ser necesario para la trazabilidad del flujo).
5. La web lee exactamente esa columna: `certified_summary_router.py:32-42` (`_scorecard`) parsea
   `candidate.scorecard_json`, y `apps/web/lib/api.ts:96` (`getCertifiedStrategies` →
   `/api/v2/certified/strategies`) es la única función que alimenta `apps/web/app/estrategias/page.tsx`
   y `apps/web/app/gates/page.tsx:219,237-238` (`c.gates_passed_count`, `c.gates`). El campo
   `c.gates` que la web pinta por candidata es, literalmente, el array que produjo la suite B en
   el paso 2.

**Ruta B confirmada por un segundo camino independiente**, no solo mine.py: candidates_router
(que sí sirve tráfico web, `main.py:146`) llega a la suite B en 2 saltos —
`candidates_router.py:20` → `services/validation/legacy_revalidation_service.py` → línea 31 de
ese fichero importa `GatePipelineOrchestrator` (suite B) y replica exactamente el mismo patrón
(`EventBacktestEngine` + `GatePipelineOrchestrator` + `CertificationRegistry`,
`legacy_revalidation_service.py:30-32,49-51`). Dos flujos de producción distintos (minería nueva
y revalidación de legado) convergen en la misma suite B.

**La suite A (`services/validation/engines/`) solo se alcanza vía `/api/v2/validation/*`**
(`validation_router.py:158-160`, montada en `main.py:169`), un router que **no tiene ningún
consumidor en `apps/web/`** — se comprobó con `grep` sobre todo `apps/web/`: cero referencias a
`v2/validation` o `validate-11-gates` (la búsqueda de la sección "web" de este informe). Es
decir: la suite A está viva en el backend, expuesta por HTTP, pero **no forma parte de ningún
camino que la web recorra hoy**, y tampoco es la que escribe el estado certificado.

**Conclusión sobre la etiqueta previa "suite A es la que ve la web":** es **imprecisa según lo
medido aquí**. Lo que la web ve (página `/estrategias`, página `/gates`) son registros
certificados en BD cuyo contenido de gates fue producido por la suite B, no por la suite A. La
suite A existe, corre, y tiene un endpoint HTTP montado — pero ningún componente de `apps/web/`
lo llama. El registro de gates de la ola de implementación debe tratar **B como la fuente de
comportamiento canónico a preservar exactamente** en el adaptador (§4), y A como la suite cuyo
comportamiento (más laxo o simplemente distinto en los 11 gates) puede migrarse con más libertad
porque hoy no tiene tráfico de producción medible desde la web — aunque **sigue teniendo 1
importador productivo** (`validation_router.py`) que el adaptador debe preservar igualmente
(regla de "cero importadores rotos" de §4, no depende de cuánto tráfico real reciba).

---

## 3. Diseño del registro plugin-style

### 3.1 Interfaz única

```
Gate (protocolo/ABC)
  GATE_ID: int           # constante de clase, 1..11, inmutable
  NAME: str               # constante de clase
  VERSION: str            # semver propio del gate, independiente de CURRENT_ENGINE_VERSION
  def evaluar(self, candidata: StrategySnapshot, evidencia: Evidencia) -> GateResult: ...
```

- **`candidata`**: se reutiliza el contrato **ya existente** `contracts/snapshots/strategy_snapshot.py`
  (`StrategySnapshot`, verificado con campos `route: StrategyRoute`, `symbol`, `timeframe`,
  `canonical_hash`, `parameters` — `strategy_snapshot.py:57-69`). No hace falta un contrato nuevo
  para esto: ya es inmutable, ya lo generan `UltraDiscoveryEngine`/`FundingDiscoveryEngine`, y ya
  lo reciben ambas suites hoy indirectamente. Reusarlo evita una tercera representación de "qué es
  una candidata".
- **`evidencia`**: **contrato nuevo** (`contracts/gate_evidence.py`, a crear en la ola de
  implementación) que agrega, como campos `Optional` con default `None` (nunca con un valor de
  relleno — REAL-ONLY), la unión de todo lo que las 22 implementaciones actuales consumen hoy:
  `candles`, `is_trades`, `oos_trades`, `pre_oos_trades`, `trades_raw`, `regime_pnls`,
  `rules_text`, `trials_tested`, `dataset_id`, `dataset_sha256`, `total_bars`. Cada gate lee solo
  los campos que le conciernen; si el campo que necesita es `None`, el gate devuelve
  `GateResult(status=BLOCKED, ...)` con el motivo — exactamente el patrón "CERO MOCKS" que la
  propia suite A ya aplica hoy en el orquestador para los gates 4, 7 y 9
  (`pipeline_orchestrator.py:120-124,177-180,214-217`). Este es el mecanismo que permite que
  **añadir un campo nuevo a `Evidencia` para un gate nuevo, o para ampliar uno existente, no
  obligue a tocar los demás módulos de gate**: es un contrato aditivo (Pydantic con campos
  opcionales), no una tupla posicional.
- **`GateResult`**: contrato nuevo (`contracts/gate_result.py`), tipado, con al menos
  `gate_id: int`, `gate_version: str`, `status: GateStatus` (se reutiliza el enum ya existente en
  `contracts/snapshots/evidence_record.py:13-18`), `score: float`, `verdict: str`,
  `evidence: Dict[str, Any]`. El orquestador del registro (no cada gate) es responsable de mapear
  `GateResult` → `EvidenceRecord` para persistir (reutilizando `EvidenceRecord`
  **sin modificarlo**, solo llenándolo correctamente — ver §3.3, que corrige un defecto ya
  detectado en el código actual).

### 3.2 Un módulo por gate, versión propia

`services/validation/registry/gates/gate_01.py` … `gate_11.py`: cada uno contiene **una única**
implementación canónica (la que se decida como umbral real — ver la petición al orquestador en la
sección final, porque A y B no coinciden en ninguno de los 11 y elegir cuál umbral es el correcto
es una decisión de producto/cuantitativa, no arquitectónica) con su propio `VERSION` de módulo,
en el estilo de changelog fechado que ya usa `services/engine_version.py:15-24` para el motor
(comentarios `# 1.1.0 (fecha): qué cambió y por qué`), pero **desacoplado por completo del
`CURRENT_ENGINE_VERSION`** del motor.

**Un detalle importante de diseño para no repetir el error ya presente en el código actual**: hoy
`GatePipelineOrchestrator` construye cada `EvidenceRecord` con
`formula_version=CURRENT_ENGINE_VERSION` (`gate_pipeline_orchestrator.py:159`) — es decir, **los
11 gates comparten literalmente el mismo número de versión (5.17.0, el del motor) aunque el campo
`formula_version` del contrato ya está pensado para ser distinto por gate** (el propio contrato lo
declara como campo independiente, `evidence_record.py:35`). Hoy es imposible saber, mirando un
`EvidenceRecord`, si el gate 4 que lo produjo es la versión de ayer o la de hace 3 meses: todos
dicen "5.17.0". El registro corrige esto trivialmente: el orquestador debe poblar
`formula_version=<VERSION del módulo de ese gate concreto>`, no `CURRENT_ENGINE_VERSION`. Este es
el mecanismo real de "mejorar solo las puertas": el `engine_version` (motor) y el `formula_version`
(gate) dejan de ser el mismo número.

### 3.3 Registro por id

```
services/validation/registry/registro.py

GATE_REGISTRY: Dict[int, Type[Gate]] = {
    1: Gate01IngestSanity,
    2: Gate02CostBacktest,
    ...
    11: Gate11NautilusEvent,
}
```

Diccionario **explícito, no descubrimiento dinámico por `importlib`/escaneo de paquete**. Se
descarta deliberadamente el patrón "auto-plugin" (escanear `gates/*.py` y registrar por
convención de nombre) porque: (a) el repo ya tiene un antecedente documentado de un nombre de
método que cambió y rompió la certificación en silencio durante semanas
(`scripts/mine.py:1035-1037`, comentario "El nombre anterior... hacía que el pipeline reventara");
un registro dinámico basado en convención de nombres de fichero repetiría exactamente ese riesgo
de forma menos visible. (b) un diccionario explícito es lo que hace el test de sustitución (§5)
trivial de razonar: el diff que demuestra el aislamiento es literal, no depende de que un
escáner "haya encontrado" el fichero nuevo.

### 3.4 Cómo un cambio en gate_04 se relaciona con la regla #26 — y por qué NO la dispara

Se verificó explícitamente contra el texto de la regla #26 y contra la cadena de autoridad de
`AUTHORITY_GRAPH.md:28-37`: el motor determinista (`DETERMINISTIC EVENT BACKTEST ENGINE`) produce
el `CANONICAL EXECUTION LEDGER`, del cual la `METRICS DERIVATION ENGINE` deriva métricas, y **solo
entonces** entra el `EVIDENCE BUNDLE & 11 GATES`. Los 11 gates son, sin excepción, **consumidores
posteriores** de operaciones ya producidas y ya selladas por el motor — ninguno de los 11 gates
lee ni altera señales de entrada del motor (`event_backtest_engine.py`) ni sus datos de mercado.
**Por tanto, cambiar el umbral o la fórmula de `gate_04` no altera qué operaciones produce el
motor: no dispara la regla #26.** Confirmado además de forma negativa por el propio código: el
motor (`services/validation/engine/event_backtest_engine.py`) no importa ni referencia ningún
módulo de `services/validation/engines/gate_*` ni de `services/api/app/validation/gates/gate_*`
en ninguna de las dos suites (no aparece en la lista de importadores de ninguna suite en la
sección 2a de `grafo_imports_2026-09-01.md`) — la dependencia es unidireccional: gates → motor,
nunca motor → gates.

Lo que el registro SÍ necesita, como disciplina paralela y propia (no como sustituto de la #26,
sino como su equivalente para gates, hoy inexistente): **un cambio en la lógica de `gate_04.py`
obliga a subir `gate_04.VERSION`** (bump semver del módulo, no del motor), y esa nueva versión
queda estampada en `formula_version` de cada `EvidenceRecord` que ese gate produzca a partir de
ese momento (§3.2). Esto es lo que permite, mirando hacia atrás, distinguir qué candidatas fueron
evaluadas con qué criterio exacto del gate 4 — la misma garantía de trazabilidad que la #26 da
para el motor, pero con radio de explosión de 1 gate en vez de todo el histórico de certificadas.
Los demás 10 gates "no se enteran" porque (a) su propio módulo no cambia de fichero ni de
contenido, (b) su entrada en `GATE_REGISTRY` no cambia, y (c) `Evidencia` es aditivo (§3.1): si
`gate_04` empieza a necesitar un campo nuevo, se añade como `Optional` al contrato sin romper la
lectura que los otros 10 gates hacen del mismo objeto.

### 3.5 Serialización con versión por gate — que la web y el pipeline vean lo MISMO

Hoy la web (`gates_router.py` + `GATES_DIRECTORY` estático) y el pipeline que certifica (suite B)
divergen literalmente en los números mostrados (§1.2 — gate 10 es el caso grave: 75.0 en la web,
40.0 en lo que certifica). El registro cierra esa brecha por construcción, no por disciplina
manual: `gates_router.py` (fuera de territorio de esta ola; queda como petición para la ola de
integración) dejaría de leer `GATES_DIRECTORY` codificado a mano y leería, para cada
`gate_id`, `GATE_REGISTRY[gate_id].VERSION` más los umbrales reales expuestos como atributos de
clase del propio módulo del gate (no un diccionario paralelo que se puede desincronizar, que es
exactamente el defecto medido en §1.2). El pipeline (mine.py / legacy_revalidation_service, vía
el adaptador de §4) y la web leerían entonces la **misma fuente en memoria** — no hace falta
ningún paso de sincronización porque nunca hay dos copias.

---

## 4. El adaptador fino — cero importadores tocados en esta ola

**Medido con precisión (corrigiendo el redondeo del expediente preliminar, con el detalle exacto
de `grafo_imports_2026-09-01.md` §2a):** hoy son **19 ficheros** los que importan
`GatePipelineOrchestrator` (suite B) directamente — 14 en `scripts/` y 5 en `services/`
(`discovery_validation_pipeline.py`, `expert_refinement_loop.py`, `universal_optimizer_engine.py`
—dos líneas—, `autonomous_discovery_engine.py`, `legacy_revalidation_service.py`), y **1 fichero**
(`validation_router.py:158`) importa `ModularValidationPipeline` (suite A). El matiz exacto sobre
la frase previa "19 ficheros importan las dos suites": **ninguno de esos 19 importa además la
suite A** — el hallazgo correcto (§2a del grafo) es que `legacy_revalidation_service.py` vive
dentro del *paquete* de la suite A (`services/validation/`) pero solo importa lógica de la suite
B; no hay solapamiento de imports directos entre las dos listas.

**Diseño del adaptador (a construir en la ola de implementación, no en esta):**

```
services/validation/registry/adaptadores.py

class GatePipelineOrchestrator:          # mismo nombre, mismo módulo de import
    """Reexportado en services/api/app/validation/gates/gate_pipeline_orchestrator.py
    para que los 19 importadores actuales seguir escribiendo exactamente
    `from services.api.app.validation.gates.gate_pipeline_orchestrator import GatePipelineOrchestrator`
    sin ningún cambio."""
    def __init__(self, evidence_base_dir=None): ...
    def run_all_gates(self, candidate_info, candles=None, is_trades=None,
                       oos_trades=None, pre_oos_trades=None, trades_raw=None,
                       strategy_snapshot=None) -> Dict[str, Any]:
        # 1. traduce candidate_info (dict) + strategy_snapshot -> StrategySnapshot + Evidencia
        # 2. delega en RegistryPipeline.evaluar_todas(candidata, evidencia)
        # 3. traduce List[GateResult] -> el MISMO dict shape que hoy devuelve
        #    run_all_gates (gates_passed_count, overall_score, tier, prescriptions...)
        #    incluida la escritura de EvidenceRecord en data/evidence/ — comportamiento
        #    observable idéntico para los 19 importadores.

class ModularValidationPipeline:         # ídem para el único importador de la suite A
    def validate_candidate(self, strategy_id, name, symbol, timeframe, route,
                            raw_trades_is, raw_trades_oos, rules_text="",
                            regime_pnls=None) -> FullValidationReport:
        # misma traducción en sentido inverso hacia el registro, mismo tipo de retorno.
```

El punto de inserción físico: el contenido actual de
`services/api/app/validation/gates/gate_pipeline_orchestrator.py` y de
`services/validation/engines/pipeline_orchestrator.py` se sustituye por un **re-export** de estas
dos clases del adaptador (`from services.validation.registry.adaptadores import
GatePipelineOrchestrator` / `ModularValidationPipeline`), de modo que **la ruta de import que ya
usan los 19+1 ficheros no cambia una sola línea**. Los 22 módulos de gate individuales de ambas
suites (`gate_01_*.py` … `gate_11_*.py` en ambos árboles) pasan a cuarentena con su
`MANIFEST.sha256`/`MOTIVO.md` (regla #4) **solo cuando** el adaptador ya reemplaza su lógica y los
tests de paridad (nota de la sección 5) confirman comportamiento observable idéntico — no antes.

**Qué NO se migra en esta ola y queda explícitamente para olas siguientes (por orden de coste
medido en `grafo_imports_2026-09-01.md` §2b/§3):**

1. **Ola 2 — los 14 scripts.** Son puntos de entrada CLI; no se ha medido en este informe si algún
   otro módulo de producción los importa a su vez (no apareció ninguna arista de ese tipo en el
   grafo), así que su radio de cambio, una vez el adaptador exista y esté probado, se limita al
   propio script. Cambiar su import de `gate_pipeline_orchestrator` a
   `services.validation.registry` directamente (retirando el adaptador para ellos) es 1 línea por
   script.
2. **Ola 3 — los 5 ficheros de `services/`** que hoy importan la suite B
   (`discovery_validation_pipeline.py`, `expert_refinement_loop.py`,
   `universal_optimizer_engine.py`, `autonomous_discovery_engine.py`,
   `legacy_revalidation_service.py`) y el único importador de la suite A
   (`validation_router.py`). Estos sí participan en el macro-ciclo de 22 paquetes medido en
   `grafo_imports_2026-09-01.md` §2c, así que su migración debe ir acompañada de una relectura del
   grafo tras cada corte, no en bloque.
3. **Ola 4 — `contracts/gate_directory.py` y `gates_router.py`** (fuera de `services/validation/`,
   por tanto fuera de este territorio) para que la web deje de leer un catálogo estático
   desincronizado y lea el registro (§3.5). Esto es una **petición al orquestador**, no algo que
   este carril pueda ejecutar (territorio de escritura ajeno).
4. **Nunca en esta serie de olas**: tocar `services/validation/engine/event_backtest_engine.py`.
   El registro de gates no tiene ninguna razón para tocarlo (§3.4) y si alguna ola futura
   propusiera hacerlo, esa ola debe parar y aplicar la regla #26 explícitamente, no este carril.

---

## 5. Prueba de sustitución nº1 — diseño del test

**Objetivo del test** (`tests/test_gate_registry_substitution.py`, a escribir en la ola de
implementación): demostrar mecánicamente la promesa central de este expediente — "mejorar el
gate 4" es, en el código, un cambio de exactamente 2 ficheros.

**Procedimiento del test:**

1. **Fixture de partida**: un `GATE_REGISTRY` de referencia con las 11 entradas apuntando a los
   módulos canónicos de `services/validation/registry/gates/`, y una `Evidencia` fija con trades
   IS/OOS deterministas (números explícitos en el test, no generados — cumple regla #1: es un
   objeto de test legítimo porque está etiquetado como tal).
2. **La variante**: se añade **un fichero nuevo**,
   `services/validation/registry/gates/gate_04_v2_prueba_sustitucion.py`, con
   `VERSION = "1.1.0-test"` y un umbral deliberadamente distinto (p. ej. `min_wfe: 0.40 -> 0.45`)
   respecto al `gate_04.py` canónico.
3. **El cambio de registro**: se edita **una línea** de `registro.py` —
   `4: Gate04WalkForwardEfficiency` → `4: Gate04WalkForwardEfficienciaV2Prueba`.
4. **Aserciones del test, sobre la MISMA `Evidencia` fija, antes y después del swap:**
   - a) `git diff --stat` (o el equivalente por comparación de ficheros dentro del test, sin
     invocar git si el entorno de test no lo permite) entre el estado "antes" y "después" toca
     **exactamente 2 rutas**: el fichero nuevo del gate variante y la línea de `registro.py`.
   - b) Los `GateResult` de los gates 1, 2, 3, 5, 6, 7, 8, 9, 10, 11 son **byte-idénticos** antes y
     después (mismo `score`, `verdict`, `evidence`, y crucialmente el mismo `gate_version` — prueba
     de que "los demás no se enteran").
   - c) El `GateResult` del gate 4 cambia de `passed`/`score` entre las dos ejecuciones (porque el
     umbral cambió) **y** su `gate_version` pasa a ser `"1.1.0-test"` en vez de la versión
     canónica — prueba de que la serialización versionada (§3.5) refleja el cambio real.
   - d) El veredicto agregado (`gates_passed_count`, `overall_certified`) cambia si y solo si el
     cambio de umbral del gate 4 cambiaba el resultado de esa candidata concreta — prueba de que
     el registro compone correctamente sin lógica oculta adicional entre gates.

Este test es la evidencia operativa que el expediente I7 (§5, punto 2) exige para pasar de
HIPÓTESIS a SELLADA respecto al Movimiento 1; no se ejecuta en esta ola porque el registro aún no
existe (es SOLO LECTURA), pero queda completamente especificado para que la ola de implementación
lo escriba sin ambigüedad.

---

## 6. Peticiones al orquestador (decisiones fuera de este territorio/carril)

1. **Cuál umbral se vuelve canónico, gate por gate.** Este informe demuestra que A y B divergen en
   los 11 gates (§1), en 4 casos con fórmulas distintas, no solo números distintos (gates 6, 7, 9,
   11). Elegir el umbral real de cada gate del registro (¿el de B, por ser el que certifica hoy en
   producción? ¿un tercero, recalculado?) es una decisión cuantitativa/de producto, no
   arquitectónica — no me corresponde fijarla en esta ola de solo-lectura.
2. **`contracts/gate_directory.py` y `services/api/app/api/gates_router.py`** necesitan
   actualizarse para leer el registro en vez de un catálogo estático (§3.5, §4 ola 4) — están
   fuera de mi territorio de escritura de esta tarea (el primero es un fichero YA existente en
   `contracts/`, no nuevo; el segundo vive en `services/api/`).
3. **Confirmar si `services/ops`** (0 aristas de import, ver `grafo_imports_2026-09-01.md` §2b
   nota) tiene algo que ver con gates antes de que cualquier ola de gates lo dé por no afectado —
   dato pendiente de otro carril, mencionado aquí solo porque apareció al leer el grafo completo
   según instrucción de la tarea.

---

## 7. Ficheros de evidencia y alcance de lo leído

Ningún fichero de código fue creado ni modificado en esta ola. Se leyeron enteros: los 11+11
módulos de gate de ambas suites, ambos orquestadores, `certification_registry.py`,
`legacy_revalidation_service.py` (primeras 60 líneas, suficientes para confirmar el patrón de
imports e instanciación), el tramo 895-1250 de `scripts/mine.py`, `contracts/gate_directory.py`,
`contracts/snapshots/evidence_record.py`, los campos relevantes de
`contracts/snapshots/strategy_snapshot.py`, `AUTHORITY_GRAPH.md` completo, y los dos informes de
investigación previos (I7 completo con su §7, y el grafo de imports completo). Comandos de grep
usados para localizar consumidores web quedan reflejados inline junto a cada afirmación de la
sección 2.
