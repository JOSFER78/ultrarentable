# EXPEDIENTE I7 — Arquitectura del código: cómo separar en partes de verdad (ABIERTO)

Fecha: 2026-09-01 · Estado: **ABIERTO — análisis preliminar del orquestador hecho; faltan el
grafo completo de imports y los tests de sustitución antes de sellar.**

## 0. El mandato, traducido

Emilio (no programador, y lo dice él): *"os doy la idea; cómo organizarlo lo investigáis
vosotros"*. Su idea-requisito: **partes bien claras también en el código**, de modo que si hay
que mejorar la parte de SQX se toque SOLO esa, si hay que mejorar el modelo de mejora se toque
SOLO ese, si hay que mejorar las puertas (gates) se toquen SOLO ellas.

En ingeniería eso se llama **reemplazabilidad independiente por fronteras con contrato**: cada
parte se puede cambiar, medir o sustituir sin tocar las demás, porque solo se hablan a través
de interfaces estables. El requisito es de Emilio; **la frontera técnica exacta la decide este
expediente**, no la transcripción literal de su idea (M1-M4 queda como hipótesis de trabajo).

## 1. Estado medido del código HOY (2026-09-01, comandos sobre el árbol real)

| Hecho medido | Dato |
| :--- | :--- |
| `services/api/` es un **monolito** | **29.478 LOC** — la mitad del backend. Dentro viven cosas que NO son API: la suite de gates B, el FastEngine/DSL, ingestion, data_feed… |
| Segundo paquete | `services/validation/` 6.010 LOC (suite de gates A) |
| **Las DOS suites de gates están vivas y entrelazadas** | A (`services.validation`) la importan: discovery_validation_pipeline, strategy_research_loop, prop_firm_engine, expert_refinement_loop, candidates_router, job_queue_router, main.py. B (`services.api.app.validation.gates`) la importan: candidates_router, market_matrix y sus propios gates. **candidates_router importa LAS DOS** |
| Módulos homónimos | `database.py` y `gate_03_trade_significance.py` existen duplicados en dos árboles |
| `sqx_bridge` | Importado desde 5 sitios fuera de su paquete |
| Consecuencia directa | **Hoy es imposible "mejorar solo las puertas"**: cambiar un gate exige decidir en cuál de las dos suites, y el cambio se propaga por 8+ módulos de ambos lados. Exactamente lo contrario del requisito |

Lo que ya está BIEN y es la piedra angular: **`contracts/` (Pydantic inmutable, no importa de
`services/`)** — el AUTHORITY_GRAPH ya impone que los datos crucen fronteras solo por contrato.
La arquitectura buena se construye sobre eso, no contra eso.

## 2. Opciones evaluadas

| Opción | Qué es | A favor | En contra |
| :--- | :--- | :--- | :--- |
| **A. Statu quo + unificación mínima** | Solo cerrar F00.1 (una suite de gates), no mover nada más | Barato, poco riesgo | El monolito `api` sigue; "tocar solo X" sigue sin ser verdad para generación/mejora/meta |
| **B. Dominios con puertos (M1-M4 formalizada), migración GRADUAL** | Paquetes por dominio: `generation/` (SQX), `improvement/`, `validation/` (única), `fondeo/`, `meta/`, `api/` reducida a fachada HTTP | Cumple el requisito; lo nuevo nace ya en su sitio; compatible con F00; PRs auditables pequeños | Migración por etapas que hay que gobernar (meses de convivencia parcial) |
| **C. Hexagonal estricto (core/puertos/adaptadores) de golpe** | Reescritura de la estructura completa | Pureza máxima | **Big-bang con 0 certificadas = el mayor riesgo posible**; violaría la lección nº1 del repo (nunca dos cambios de semántica empaquetados; nunca árboles incoherentes) |

## 3. Propuesta preliminar (a sellar tras los experimentos de §5): **B gradual, en 3 movimientos**

**Movimiento 1 — Las puertas como enchufes (lo primero, cumple "mejorar las puertas sueltas"):**
cerrar F00.1 dejando UNA suite (`services/validation/`) con un **registro de gates
plugin-style**: cada gate es un módulo aislado con la misma interfaz
(`evaluar(candidata, evidencia) → GateResult`), registrado por id y **versionado
individualmente** (un cambio en gate_04 sube la versión del gate y dispara regla #26; los
demás gates ni se enteran). La suite B del monolito, a cuarentena o adaptador fino. Así
"mejorar una puerta" = editar UN fichero + su test + su bump.

**Movimiento 2 — Lo nuevo nace en su dominio (coste cero de migración):**
`services/improvement/` (M2) y `services/meta/` (M4, rehecho) se crean YA en frontera limpia:
solo importan `contracts/` y el registro de gates. Ídem el catálogo de firmas en
`services/fondeo/`. Nada de añadir código nuevo al monolito `api`.

**Movimiento 3 — Vaciar el monolito por gravedad, no por big-bang:**
cada vez que un carril toque algo del interior de `api/` que no sea HTTP (engine, dsl,
ingestion…), se muda a su dominio EN ESE momento (git mv + imports, cambio mecánico auditable,
sin tocar semántica — regla #26 no se dispara si la verificación de identidad 15/15 lo
confirma). `api/` termina siendo solo la fachada HTTP que llama a los dominios.

**Reglas transversales**: dependencia solo "dominio → contracts" y "api → dominios"; prohibido
dominio→dominio directo (pasa por contrato o por la cola); la config de SQX es código
versionado del dominio `generation/`; los tests viven con su dominio.

## 4. Por qué NO la opción C (y no es pereza)

El historial del repo es una lista de heridas por cambios grandes empaquetados: la regla #26
nació de un doble cambio en una edición; las 728 falsas certificadas, de motores que cambiaban
bajo los pies. Una reestructuración total con 0 certificadas pararía el objetivo semanas y
multiplicaría el riesgo de romper la reproducibilidad. La opción B da el mismo destino final
con el riesgo troceado en pasos verificables.

## 5. Lo que falta para SELLAR este expediente (lo ejecuta el orquestador local)

1. **Grafo completo de imports** (`grimp`/`pydeps` sobre `services/`+`scripts/`): confirmar que
   no hay más acoplamientos ocultos que los medidos aquí; publicar el grafo en `results/`.
2. **Test de sustitución nº1 (puertas)**: tras el Movimiento 1, cambiar un gate por una
   variante y demostrar que NADA fuera de su módulo+registro se toca (diff = 2 ficheros).
3. **Test de sustitución nº2 (mejora)**: stub de un `Improver` alternativo en
   `services/improvement/` intercambiado por config, cero cambios fuera.
4. Con los tres verdes: actualizar `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` de HIPÓTESIS a
   SELLADA, con las fronteras definitivas, y reflejarlo en `PLAN_LOCAL_FONDEO.md` (W4.3 pasa a
   ser el Movimiento 1).

## 6. Afirmaciones previas contrastadas

- "Dos pipelines de validación con umbrales distintos" (F00/current_phase) — **CONFIRMADO y
  ampliado**: además están entrelazadas (un router importa ambas).
- "9 módulos homónimos vivos" (F00) — parcialmente verificado aquí (2 homónimos en `services/`;
  el censo completo entra en el grafo de §5.1).
- La idea M1-M4 de Emilio — **viable como dominios de la opción B**; su frontera exacta queda
  pendiente de los tests de sustitución.
