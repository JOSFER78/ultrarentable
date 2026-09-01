# PLAN DE INVESTIGACIÓN PROFUNDA — el plan de los planes (2026-09-01)

> Mandato de Emilio: antes de (y en paralelo a) ejecutar, **investigar a fondo cada parte y no
> dar NADA por sentado de lo que está escrito**. Todo documento del repo — incluido el corpus
> tradesfera, los planes SQX previos (`17C_PLAN_100_PORCIENTO_SQX.md`), el diseño F04 y las
> specs de la web — es **HIPÓTESIS a re-verificar**, no verdad. La verdad sale de fuentes
> primarias (documentación oficial, ToS vigentes, el propio software) y de **experimentos
> reproducibles en nuestra máquina con nuestros datos**.
>
> Ejecuta: el ORQUESTADOR local con su loop no bloqueante (los SUB recolectan y ejecutan
> experimentos; el ORQ diseña, contrasta y concluye). Cada investigación alimenta y puede
> MODIFICAR `PLAN_LOCAL_FONDEO.md`: el plan de ejecución obedece a la evidencia, no al revés.

> **Mapa investigación → módulo** (`ARQUITECTURA_MODULAR_ESTRATEGIAS.md`): I1→M1 Generación ·
> I2→M2 Mejora · I3→M4 Metaestrategias · I4→M3 Valoración fondeo · I5→la web de los cuatro
> (RESUELTA) · I6→infra. Un módulo no se sella sin su expediente cerrado.

## I0 — MÉTODO COMÚN (obligatorio para las seis)

Cada investigación produce un expediente en `orchestration/reviews/investigacion_IX_<tema>.md` con:

1. **Preguntas** formuladas ANTES de mirar (las de abajo + las que surjan).
2. **Fuentes primarias consultadas** (doc oficial, código, ToS, foro del fabricante) con fecha y
   enlace/ruta. Lo que diga el repo se cita como "afirmación previa" y se marca CONFIRMADO /
   REFUTADO / NO VERIFICABLE.
3. **Experimentos** con comando, datos, coste y resultado pegado literal (REAL-ONLY también aquí).
4. **Conclusión y decisión propuesta**, con lo que cambia en el plan de ejecución (diff concreto
   de carriles/tareas).
5. **Lo que queda abierto**, sin disimular.

Timebox por investigación: fase documental 0,5-1 día de agente; experimentos según coste
declarado ANTES de lanzarlos. Prohibido concluir sin experimento cuando el experimento es
posible. Prohibido "lo dice el doc X del repo" como única fuente.

---

## I1 — STRATEGYQUANT X AL 100 % ("Strategy One")

**Hecho ya verificado (2026-09-01, web):** "Strategy One" no existe como producto; el motor es
**StrategyQuant X (SQX)**, y la suite del fabricante incluye además **QuantDataManager (QDM:
descarga/gestión de datos históricos GRATUITOS — Dukascopy entre las fuentes)**, **QuantAnalyzer
(QA: análisis de resultados y carteras)** y **AlgoCloud**. Esto abre dos vías que hoy no usamos:
QDM para el problema de las velas y QA para la meta-análisis.

**Objetivo**: que SQX haga el 90 % del trabajo sucio (generar, pre-filtrar, robustecer, mejorar)
y nuestro motor solo certifique. "Aprovechar todo su motor al completo para hacer menos luego."

**Preguntas (mínimo):**

1. Inventario COMPLETO de capacidades de nuestra instalación real (`StrategyQuantX144`, licencia
   ¿Starter/Pro/Ultimate? — condiciona qué hay): Builder (genético/aleatorio/plantillas, islas,
   fitness), cross-checks (WFO, WF Matrix, Monte Carlo trades/datos, retest precisión superior,
   mercados adicionales, System Parameter Permutation), Optimizer, **Improver**, ranking y
   fórmulas de fitness CUSTOM, databanks y su persistencia, AlgoWizard, snippets/indicadores
   custom en Java, comandos completos del CLI headless (`sqcli /call?cmd=...`), import/export.
2. **Gap analysis**: qué usamos hoy (project.cfx de Ultra_Matrix/Ultra_Auto_Pilot) vs qué ofrece.
   Contrastar con los docs previos del repo (`estrategias_um/docs/CONFIG_DOORS.md`,
   `FACTORY_REFERENCE.md`, `docs/Estado/auditoria/17A/17B/17C`, `13_especificacion_generador_ideal.md`,
   `14_analisis_antioverfit.md`) — confirmar o refutar cada afirmación.
3. ¿Se puede expresar el **criterio 1.1 DENTRO de SQX** (fitness/filtros: nº trades OOS, PF OOS,
   estabilidad WF) para que lo que salga del Builder ya venga pre-alineado? ¿Custom fitness en
   Java lo permite exactamente?
4. ¿Cómo se configura FONDEO nativo: sesiones RTH/killzones en el Builder, cierre intradía
   obligatorio, MaxTradesPerDay coherente con ≥200 ops OOS, comisiones/slippage reales de micros?
5. Por qué el Build actual era estéril (fusible MC + `MinTradesInRun>20` × `MaxTradesPerDay=1`,
   documentado en `estrategias_um/docs/ESTADO.md`): reproducir en el PC, arreglar, y medir la
   config nueva (% aceptación, calidad, coste CPU/estrategia).
6. **QDM**: ¿descarga M1/5m de los proxies (índices CFD Dukascopy, oro, petróleo) y exporta al
   formato de SQX y al nuestro? Si sí, ¿sustituye o complementa `dukascopy_feed.py`? ¿Y las
   velas de futuros/cripto que hoy nos faltan?
7. **QA (QuantAnalyzer)**: ¿qué aporta a meta-carteras (correlaciones, WF de cartera, Monte
   Carlo de cartera) frente a hacerlo en nuestro motor? Licencia incluida o aparte.
8. El puente SQX→motor propio: formato .sqx/AST (piloto W3.3), ¿hay export XML/JSON documentado
   más robusto que parsear .sqx?
9. Modo de trabajo PC: GUI vs headless, memoria (el VPS necesitaba 8-10 GB), y si conviene
   Builder en GUI (iteración) + headless para lotes nocturnos.

**Experimentos**: (a) Build A/B en el PC: config actual vs config re-diseñada, mismas semillas y
datos, medir embudo completo; (b) fitness custom con proxy del criterio 1.1 y comparar tasa de
supervivencia posterior en NUESTROS 11 gates; (c) QDM descargando un símbolo problema y
verificación contra nuestro consolidado (hashes, conteos).

**Fuentes**: doc oficial strategyquant.com (+ manual de la instalación local), foro SQ, código
XML de los .cfx, y pruebas. Los MD del repo solo como afirmaciones previas a contrastar.

## I2 — EL SISTEMA DE MEJORA DE ESTRATEGIAS (¿funciona el diseñado? ¿cuál es el mejor?)

**Estado real de partida (verificado)**: F04 está DISEÑADO pero NO implementado; el lazo de
mejora de SQX (Improver) llevaba meses roto por configuración; no existe hoy NINGÚN sistema de
mejora funcionando. La pregunta no es "si funciona el implementado" — es qué construir.

**Candidatos a evaluar (todos, sin favoritos):**

| Sistema | Qué es | Riesgo principal |
| :--- | :--- | :--- |
| SQX Improver/Optimizer bien configurado | mejora nativa dentro de SQX | opaco; ¿respeta nuestro holdout? |
| F04 diseñado (semántica IA → experimento parametrizado → holdout/DSR/WF) | la IA elige la DIMENSIÓN, la búsqueda el VALOR | coste de construirlo; sobreajuste por multiplicidad |
| Optimización bayesiana (Optuna) sobre dimensiones elegidas | barato, medible | mejora parámetros, no reglas |
| Meta-labeling (López de Prado): un clasificador decide QUÉ señales tomar | mejora sin tocar la señal | necesita features honestas; complejidad |
| Filtros de régimen (vol/tendencia/sesión) buscados, no fijados | simple y auditable | puede ser todo lo que F04 haría, más barato |
| WF re-optimización periódica (parámetros rodantes) | estándar de la industria | ¿compatible con certificación estática? |

**Preguntas**: ¿cuál produce más supervivientes REALES del criterio 1.1 por hora de CPU? ¿cuál
generaliza (uplift en blind holdout, no en IS)? ¿cómo se penaliza la multiplicidad en cada uno
(DSR)? ¿qué combinación (p. ej. SQX genera → filtros de régimen → bayesiana fina) rinde más?

**Benchmark obligatorio (el corazón de I2)**: banco de pruebas con los near-misses REALES ya
existentes (ETHUSDT 4h PF OOS 2,17/39 ops, SOLUSDT 4h 1,56/36, AVAXUSDT 1h 7/11 gates — sirven
como cobayas aunque ULTRA esté aparcado, y las FONDEO que aparezcan se suman). Protocolo: mismo
presupuesto CPU por sistema, blind holdout INTOCADO hasta el final, métrica = % de mejoras que
sobreviven OOS+DSR y uplift mediano de PF OOS. Resultado `SIN MEJORA` es aceptable y publicable.

## I3 — META-ESTRATEGIAS (dinámico, semántico, entre agentes, con todo el software posible)

**Estado real de partida**: el pipeline meta actual está muerto de fábrica (filtro hardcodeado
5.4.0 + correlación fabricada). Se rehace sobre lo que diga esta investigación.

**Preguntas:**

1. Ensamblado: ERC / HRP / Kelly fraccional / mínima varianza del EXAMEN — ¿cuál minimiza
   P(romper cuenta) conjunta y varianza de los 3-8 días, que es el objetivo FONDEO (no Sharpe)?
2. Router dinámico (decisión #4, "debate IA multi-activo sin hardcodear"): diseñar el protocolo
   concreto — qué evidencia ven los agentes (regímenes, correlación rodante, telemetría en
   vivo del vigía), cómo su salida se convierte en pesos/activaciones DENTRO de límites
   deterministas, y cómo se valida (walk-forward de cartera con holdout). Qué parte JAMÁS puede
   ser un LLM (límites de riesgo).
3. Correlación honesta: solape temporal mínimo, ventanas, ¿de retornos de operaciones o de
   equity diaria? (la actual fabricaba 0,15 — prohibido).
4. Software: **QuantAnalyzer** y el PortfolioMaster/Composer de SQX vs nuestro
   `services/portfolio/` — matriz de qué hace cada uno, qué certifica la doctrina y qué no.
5. En fondeo multi-cuenta (corpus tradesfera 05): ¿la meta se aplica POR cuenta o entre cuentas?
   ¿qué permiten las firmas (copy-trading entre cuentas propias — verificar en I4)?

**Experimentos**: con ≥2 certificadas cuando existan (bloqueante real); mientras, prototipo
sobre las mejores candidatas reales NO certificadas, etiquetado EXPLORATORIO (nunca entra en
producción; solo valida la maquinaria de ensamblado y el protocolo de debate).

## I4 — EMPRESAS DE FONDEO: reglas y economía 2026, re-verificadas de cero

**El corpus existente (`docs/tradesfera/`, `docs/Fondeo/BASE_DATOS_EMPRESAS_FONDEO_FUTUROS_2026-08-02.md`)
tiene fecha 08-2026 y NO se da por bueno: las prop firms cambian reglas cada pocos meses.**

**Preguntas por firma (Topstep, Apex, MFFU, TradeDay, y 2-3 más del corpus):**

1. Reglas EXACTAS hoy: trailing DD (¿EOD o intradía? ¿sobre equity flotante? — determina que
   nuestro motor 5.15.0 simule LO MISMO), pérdida diaria, consistencia, mínimo de días,
   micros permitidos, horario obligatorio de cierre.
2. Economía real: precio examen, activación/PA, resets, payout (frecuencia, mínimos, splits),
   denegaciones documentadas. Métrica reina: **retiros netos − costes totales**.
3. Automatización: ¿permiten algo-trading/semiautomático? ¿copy entre cuentas propias? ¿qué
   detectan y qué descalifica (IP datacenter, consistencia de horario, latencia)? Contrastar
   con `docs/conexiones_automatizar/`.
4. Compatibilidad con NUESTRAS estrategias: frecuencia intradía de ORB/VWAP vs regla de
   consistencia; sizing de micros vs pérdida diaria 2 %.
5. Ranking final: firma × coste × P(pasar con nuestras candidatas, del examen F07) × payout
   neto → **dónde se compra el primer examen** (la compra en sí es decisión de Emilio).

**Fuentes**: webs y ToS oficiales (con fecha de captura), FAQ/soporte, comunidades (con
escepticismo, señalado como secundario). Entregable extra: los parámetros exactos por firma en
`PROP_FIRM_CATALOG` del código, con test que compare catálogo vs ToS citado.

## I5 — LA WEB: ¿REESCRIBIR LA PÁGINA O CONSTRUIRLA DE CERO? — ✅ RESUELTA (2026-09-01)

**Investigación ejecutada con medición directa sobre el código. Expediente completo:
`orchestration/reviews/investigacion_I5_web.md`.**

**Veredicto: NO se hace la web de cero. Se PODA (cuarentena de ~15 rutas fuera de misión, el
42 % del código) y se REPARA lo roto real (6 items acotados), con DOS reescrituras quirúrgicas
dentro de la app: el contenido de `/estrategias` (374 LOC, de cero contra la spec) y la home.**

Números que sostienen el veredicto: 29.773 LOC totales; núcleo útil FONDEO ~5.200 LOC (17 %),
delgado, tipado y ya conectado a la API canónica con fetch fail-closed; peso muerto ~12.500 LOC
que la cuarentena corta en horas; `MotorBacktestView` con cero importadores; lo roto de verdad
(firebase env, badges 5.4.0, estados de la spec, prop-firms.ts de 4.307 LOC como código de
cliente) cabe en 1-2 días de agente frente a 1-2 semanas de reescritura con riesgo de dualidad
— el fallo histórico nº 1 del repo. Plan de obra en el expediente, ya reflejado en
`PLAN_LOCAL_FONDEO.md` W5.

Queda dentro de W5: hosting definitivo (VPS build de producción vs Firebase Hosting
`ultrafondeo` + espejo), auth de un solo proyecto Firebase, `/plan` renderizando también estos
planes.

## I7 — ARQUITECTURA DEL CÓDIGO: partes reemplazables de verdad — 🔶 ABIERTA (preliminar hecho)

**Requisito de Emilio**: si hay que mejorar la parte SQX, el modelo de mejora o las puertas,
que se toque SOLO esa parte. **Expediente con el análisis preliminar del orquestador:
`reviews/investigacion_I7_arquitectura_codigo.md`** — medido: `services/api/` es un monolito
de 29.478 LOC y las dos suites de gates están entrelazadas (un router importa ambas), luego hoy
el requisito NO se cumple. Propuesta preliminar: opción B (dominios con puertos, migración
gradual en 3 movimientos, empezando por el **registro de gates versionados uno a uno**), NO el
big-bang. Para sellar faltan: grafo completo de imports + 2 tests de sustitución (§5 del
expediente). M1-M4 queda como hipótesis hasta entonces.

## I6 — INFRA (ligera, ya casi decidida)

Validar con medición lo ya diseñado: optimización VPS corregida (zRAM DESPUÉS de liberar,
medir `memory.events` antes/después), R2 como lago de datasets (¿10 GB gratis bastan con
Parquet+zstd? medir tamaño real), arquitectura del vigía (`HERMES_VPS_VIGIA.md`) contra
alternativas si I4 revela restricciones de automatización que la invaliden.

---

## SECUENCIA Y ACOPLAMIENTO CON EL PLAN DE EJECUCIÓN

| Investigación | Cuándo | Bloquea / alimenta |
| :--- | :--- | :--- |
| I1 SQX | **YA** (D0-D2, en paralelo con W0-W1) | W3 entero (SQX en PC, configs, carril .sqx); puede cambiar W1 (QDM) |
| I4 Fondeo | **YA** (D0-D2, es documental) | W6/F07 (catálogo de reglas), vigía V1, elección de firma |
| I5 Web | D1 (spike tras W4.3 designar API canónica) | W5 entero |
| I2 Mejora | benchmark cuando haya near-misses frescos; diseño documental YA | F04/W3.5 |
| I3 Meta | diseño YA; experimentos tras ≥2 certificadas | W6 |
| I6 Infra | con la ventana sudo | W0.6/W7 |
| I7 Arquitectura código | preliminar HECHO; sellar con grafo de imports + tests de sustitución (D1-D2) | redefine W4.3 (→ registro de gates); dónde nace el código de M2/M4 |

Regla final: **cada expediente cerrado actualiza `PLAN_LOCAL_FONDEO.md` en el mismo commit.**
Un plan que no cambia con la evidencia es un plan muerto; uno que cambia sin evidencia es humo.
