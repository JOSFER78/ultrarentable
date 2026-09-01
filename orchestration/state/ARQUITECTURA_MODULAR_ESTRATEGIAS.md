# ARQUITECTURA MODULAR DEL PIPELINE DE ESTRATEGIAS — M1·M2·M3·M4 (2026-09-01)

> **ESTADO: HIPÓTESIS DE TRABAJO.** M1-M4 formaliza la IDEA-REQUISITO de Emilio (partes
> reemplazables de forma independiente, también en el código); Emilio no es programador y la
> frontera técnica exacta NO se toma de su literalidad: la investiga y la sella el expediente
> **I7** (`reviews/investigacion_I7_arquitectura_codigo.md`), que ya midió el código real (el
> paquete `api` es un monolito de 29.478 LOC y las dos suites de gates están entrelazadas) y
> propone la migración gradual en 3 movimientos, empezando por el registro de gates
> individualmente versionados. Hasta que I7 selle, este doc guía el QUÉ; el CÓMO exacto es suyo.
>
> Mandato de Emilio: el plan y el código deben estar **separados por partes bien claras**, cada
> una con su investigación, su código y su página. **Nada se da por sentado**: cada módulo
> arranca ABIERTO, su investigación (I1-I4, I7) elige el mejor diseño, y solo entonces se sella.
>
> **La estrella polar de los cuatro módulos**: *conseguir estrategias para FONDEO y META-FONDEO
> de manera eficaz y LO MÁS REAL POSIBLE respecto al mercado real.* Realismo = fricción honesta
> (motor ≥5.17.0), datos verificados, reglas de prop firm exactas barra a barra, y cero
> maquillaje. Ante cualquier disyuntiva de diseño, gana la opción más fiel al mercado real.

## El pipeline en una línea

```
M1 GENERAR (Strategy One/SQX) → M2 MEJORAR (loop iterativo) → M3 VALORAR PARA FONDEO
                                      ↑__________________________________|
                                      (los fallos etiquetados realimentan la mejora)
M4 METAESTRATEGIAS consume certificadas de M3 y reutiliza el motor de mejora de M2
```

Entre módulos solo viajan **contratos** (`contracts/`): AST canónico + hashes + evidencia.
Nada cruza una frontera sin `strategy_hash`, `dataset_hash` y procedencia. Prohibido el
acoplamiento lateral (un módulo no importa internals de otro).

---

## M1 — GENERACIÓN: "Strategy One" (StrategyQuant X) exprimido al 100 %

**Misión**: que SQX produzca el máximo caudal de estrategias crudas VIABLES con el mínimo
trabajo posterior nuestro. La fábrica es SQX; nosotros ponemos el control de calidad.

| Aspecto | Definición |
| :--- | :--- |
| Investigación | **I1** (`PLAN_INVESTIGACION_PROFUNDA.md`): inventario completo del motor, fitness custom con proxy del criterio 1.1, cross-checks como pre-gates, QDM para datos, config FONDEO (sesiones RTH, micros, comisiones reales) |
| Código | `services/sqx_bridge/` (cliente, ingest, export) + configs `.cfx` versionadas + `scripts/` de lote. La config del Builder se trata COMO CÓDIGO: cambia → se versiona y se registra qué produce |
| Ejecución | SQX en el PC (GUI para iterar, headless para lotes nocturnos), según `OPERACION_LOCAL.md` |
| Entrada | Datasets verificados (manifiesto SHA-256) importados con naming `<SYM>_<TF>` |
| Salida (contrato) | Estrategias crudas: `.sqx` + export CSV de métricas + AST parseado, con procedencia (proyecto, databank, config-hash, fecha) persistida a disco/BD INMEDIATAMENTE (nada en RAM del motor) |
| Métrica del módulo | Crudas viables/hora de CPU y % que sobrevive al primer paso de M2 — no "estrategias generadas" (generar 100k/h con 0 % de aceptación ya pasó y no vale nada) |
| Estado hoy | Builder estéril por config (fusible MC × MinTradesInRun × MaxTradesPerDay) — I1.5 lo repara; 2.035 crudas en `ToImprove` esperando el parser (W3.3) |

## M2 — MEJORA: el loop iterativo que revisa y mejora sin descanso

**Misión**: coger crudas de M1 (o near-misses de campañas) y mejorarlas en un **ciclo cerrado
con revisión del motor en cada vuelta**, hasta certificarlas o agotarlas honestamente.

**La máquina de estados del loop (el "cómo se comprueba y se va mejorando"):**

```
CRUDA → EVALUADA (backtest honesto + gates; cada fallo ETIQUETADO: qué gate, por qué,
        con qué margen — la telemetría del embudo es la materia prima)
      → EN_MEJORA(iter n): hipótesis sobre el mecanismo del fallo → experimento
        parametrizado (la IA elige la DIMENSIÓN, la búsqueda el VALOR — F04)
      → RE-EVALUADA por el MISMO pipeline de gates (nunca uno más blando)
      → CERTIFICADA (11/11 + criterio 1.1)  |  vuelve a EN_MEJORA(n+1)  |  AGOTADA
```

Reglas duras del loop: blind holdout INTOCADO durante todas las iteraciones; presupuesto de
iteraciones por estrategia con penalización por multiplicidad (DSR: cuantas más vueltas, más
alto el listón); `AGOTADA` con su historial es un resultado válido y se archiva con linaje
(`services/lineage/` ya existe); `SIN MEJORA` se reporta, no se fuerza.

| Aspecto | Definición |
| :--- | :--- |
| Investigación | **I2**: benchmark de los 6 sistemas candidatos (SQX Improver, F04 semántico, bayesiana, meta-labeling, filtros de régimen, WF rodante) — puede ganar una COMBINACIÓN |
| Código | `services/improvement/` (nuevo, sellado tras I2) + reutiliza validación canónica y lineage. El Improver de SQX, si I2 lo valida, se orquesta desde aquí — nunca como pipeline paralelo |
| Entrada | Crudas de M1 con evidencia; near-misses de campañas (≥7/11 gates o PF OOS alto con pocas ops) |
| Salida (contrato) | Candidatas con historial completo de iteraciones (qué se probó, qué mejoró, qué holdout lo confirmó) |
| Métrica del módulo | % de entradas que alcanzan certificación y uplift MEDIANO de PF OOS en holdout — jamás la mejora en IS |

## M3 — VALORACIÓN PARA FONDEO: extraer, organizar y puntuar contra el examen real

**Misión**: convertir candidatas certificadas en decisiones de fondeo: **con qué firma, en qué
horarios, con qué tamaño y con qué probabilidad real de pasar y de sobrevivir.**

| Aspecto | Definición |
| :--- | :--- |
| Investigación | **I4** (reglas/economía 2026 re-verificadas de cero, firma a firma) + la parte de examen de F07 |
| Código | `services/fondeo/` consolidando `fondeo_examen` + `prop_firms` + el simulador barra a barra del motor 5.15.0. El catálogo de firmas (`PROP_FIRM_CATALOG`) vive AQUÍ con test contra ToS citado — y se sirve a la web por API (muere `lib/prop-firms.ts` de 4.307 LOC en cliente) |
| Análisis de horarios | Del ledger real de cada estrategia: distribución de PnL por hora/sesión (NY AM/PM, Londres — decisión #2), días de la semana, comportamiento en apertura/cierre. Las killzones se aplican como CAPA POSTERIOR de optimización (decisión #1, vía M2), nunca inventadas a mano |
| Examen | Monte Carlo remuestreando OPERACIONES REALES sobre las reglas EXACTAS de cada firma evaluadas sobre equity FLOTANTE (`reejecutar_examen_barra_a_barra` DECIDE — deuda W4.1 cerrada antes de la primera valoración) |
| Salida (contrato) | Ranking: estrategia × firma → P(pasar en ≤8 días), P(romper cuenta) 6m, mediana/p5/p95 mensual, horario recomendado, tamaño en micros. Y el veredicto agregado contra el objetivo sellado: ≥20 % mensual sostenible (mediana), P(ruina) ≤20 % |
| Métrica del módulo | Fidelidad: divergencia entre lo que predice el examen y lo que luego mide el vigía en demo (V0). Si divergen, se corrige el simulador, jamás la cifra |

## M4 — METAESTRATEGIAS: varias estrategias que juntas forman una

**Misión**: combinar certificadas (M3) en una sola estrategia compuesta que **baje la varianza
del examen y la P(ruina) conjunta** — en fondeo, la varianza mata más que la media baja.

| Aspecto | Definición |
| :--- | :--- |
| Investigación | **I3**: ensamblado (ERC/HRP/Kelly fraccional/mín-varianza del examen), router dinámico con debate IA multi-agente DENTRO de límites deterministas, correlación honesta por solape temporal real, y qué aportan QuantAnalyzer/PortfolioMaster vs motor propio |
| Código | `services/meta/` (se REHACE: el actual está muerto — hardcode 5.4.0 + correlación fabricada; a cuarentena tras I3) |
| Reutiliza M2 | El motor de mejora dinámico-semántico se aplica también a la META como unidad: la combinación se itera (pesos, filtros de régimen, reglas de activación) con el mismo loop de holdout+DSR |
| Entrada | ≥2 certificadas M3 con ledgers completos y solape temporal suficiente |
| Salida (contrato) | Meta-estrategia con: componentes+pesos+hash, matriz de correlación verificada, examen F07 propio (la meta se examina como una estrategia más), y su ranking M3 |
| Métrica del módulo | Reducción REAL de varianza del examen y de P(ruina) vs la mejor componente sola. Si la meta no mejora a su mejor componente, se reporta y no se usa |

---

## La web refleja los módulos (con la estética de `docs/19_UI_STYLE_SPEC.md`)

`/estrategias` = **página maestra** (decisión #16) con cuatro secciones jerarquizadas:

| Sección | Muestra (siempre honesto, gris salvo P&L) |
| :--- | :--- |
| **Generación (Strategy One)** | Estado de SQX, config vigente (hash), caudal real, crudas con procedencia — hoy absorbe el panel SQX existente |
| **Mejora** | El loop en vivo: cada candidata con su iteración, fallo etiquetado, historial de linaje |
| **Valoración Fondeo** | Ranking estrategia×firma, P(pasar)/P(ruina), horarios (heatmap gris con verde/rojo por PnL), objetivo sellado vs cifra real |
| **Meta** | Composiciones, correlaciones verificadas, examen de la meta |

El catálogo raíz de `/estrategias` sigue rigiéndose por `18_STRATEGIES_PAGE_SPEC.md`
(identidad + estados + NO EVIDENCE); las secciones añaden las vistas por módulo.

## ULTRA en esta arquitectura — presente en TODO, estado: EN CONSTRUCCIÓN

**ULTRA no desaparece de ninguna parte: queda visible y estructurado en todo el proyecto con
estado EN CONSTRUCCIÓN/PENDIENTE, y nada de lo que se construya ahora puede bloquear su vuelta.**

- **M1 (Generación) y M2 (Mejora) son agnósticos al track POR DISEÑO** (decisión sellada #24:
  el descubrimiento es el mismo; la diferencia está en la envolvente). Cuando ULTRA se
  reactive, consume estos mismos módulos sin cambios.
- **El gemelo ULTRA de M3** es la envolvente de balas (F05: pirámide, reciclaje, 80 % DD
  flotante) y **el de M4** es el meta-router ULTRA (F06). Ambos EN CONSTRUCCIÓN, con su estado
  íntegro congelado en `state/PUNTO_GUARDADO_ULTRA.md` y sus bloques con `aparcado: true`.
- **En la web, ULTRA se VE**: entrada propia en el Sidebar al final ("Ultra — EN CONSTRUCCIÓN",
  atenuada) y sus rutas con banner gris, nunca borradas.
- Regla para el orquestador: ante cualquier decisión de diseño, preguntarse "¿esto le cierra
  una puerta a ULTRA?" — si sí, se elige otra vía o se deja documentado el coste de reabrir.

## Integración con los planes vigentes

| Módulo | Investigación | Carriles de ejecución |
| :--- | :--- | :--- |
| M1 | I1 (YA, D0-D2) | W3.1, W3.2, W3.3 (parser piloto) |
| M2 | I2 (diseño ya; benchmark con near-misses) | W3.5 → construye `services/improvement/` |
| M3 | I4 (YA, documental) | W4.1 (examen decide honesto), W6.2-W6.3, análisis de horarios |
| M4 | I3 (diseño ya; experimentos tras ≥2 certificadas) | W6.1, rehacer `services/meta/` |
| Web M1-M4 | I5 (RESUELTA: podar y reparar) | W5 con `19_UI_STYLE_SPEC.md` |

Regla de cierre: **un módulo no se sella hasta que su expediente I esté cerrado**, y cada
expediente actualiza este documento y `PLAN_LOCAL_FONDEO.md` en el mismo commit.
