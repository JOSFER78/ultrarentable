# DISEÑO DE `/estrategias` — página maestra M1·M2·M3·M4 (2026-09-01)

> Autor: ORQUESTADOR (Opus 5). Territorio `reviews/`. Es el **diseño previo** que exige la
> doctrina §3.3 antes de despachar el subagente de front (W5.2 / paso 2 del plan de obra de I5).
> Manda sobre este documento: `docs/18_STRATEGIES_PAGE_SPEC.md` (QUÉ se muestra) y
> `docs/19_UI_STYLE_SPEC.md` (CÓMO se ve). Lo que aquí se añade es el **puente concreto** entre
> esas dos specs, la arquitectura M1-M4 y los endpoints que existen HOY en `apps/web/lib/api.ts`.
>
> Restricción de método: **no se inventa ningún endpoint**. Cada dato de la página sale de una
> función que ya existe en `lib/api.ts` (verificado leyéndolo entero). Donde no hay endpoint, la
> sección muestra `NO DISPONIBLE` y se documenta como deuda — no se rellena.

## 1. Lo que la página es y lo que NO es

Es el **catálogo de inteligencia cuantitativa** y, desde la arquitectura modular, la **página
maestra de los cuatro módulos**. Responde a una sola pregunta: *¿qué estrategias tenemos, de
dónde salieron, en qué punto del pipeline están, y qué evidencia las sostiene?*

Prohibido dentro de esta página (spec 18, "Separación fundamental" — `STRATEGY IDENTITY !=
EXECUTION VENUE`): BingX o cualquier exchange como filtro de identidad, broker/venue como
dimensión, cuentas de 25K/50K, capital inicial, sizing de prop firm, ejecución en vivo,
posiciones u órdenes. El tamaño y la firma son cosa de la sección de Valoración (M3), que puntúa
estrategias YA certificadas — nunca del catálogo.

Prohibido reintroducir `MotorBacktestView` (spec 18, "No regresión"). Va a cuarentena en el paso
1 del plan de obra.

## 2. Anatomía: una cabecera honesta + cuatro secciones

```
┌─ CABECERA (siempre visible, una línea de verdad) ────────────────────────────┐
│  Estrategias    Motor 5.17.0 (dinámico)   API ●   Certificadas FONDEO: 0     │
└──────────────────────────────────────────────────────────────────────────────┘
┌─ EMBUDO DE ESTADOS (la spec 18, hecho barra) ────────────────────────────────┐
│  EXTRACTED 2035 → STRUCTURALLY_VERIFIED n → BACKTEST_VERIFIED n → CERTIFIED 0 │
└──────────────────────────────────────────────────────────────────────────────┘
┌─ CATÁLOGO (el corazón: tabla densa, filtrable) ──────────────────────────────┐
│  id · símbolo · TF · arquetipo · estado · gates · PF OOS · ops OOS · hash    │
└──────────────────────────────────────────────────────────────────────────────┘
┌─ M1 GENERACIÓN ─┬─ M2 MEJORA ─┬─ M3 VALORACIÓN ─┬─ M4 META ─┐  (secciones
└─────────────────┴─────────────┴─────────────────┴───────────┘   plegables)
```

Regla de la spec 19 §4: *"Cada página abre con una línea de estado honesta antes que cualquier
tabla"*. La cabecera ES esa línea, y hoy dirá **"Certificadas FONDEO: 0"**, porque es la verdad.
Se muestra en gris, no en rojo: cero certificadas no es un error del sistema, es el marcador.

### 2.1 Cabecera

| Dato | Origen real | Si falla |
| :--- | :--- | :--- |
| Versión de motor | `getDiscoveryStatus().current_engine_version` | `MOTOR: NO DISPONIBLE` en `--text-3`. **Nunca** un literal `5.4.0` — es justo la mentira que hay que matar (W5.4) |
| Estado de la API | éxito/fallo de la primera llamada | punto 6px: `--profit` si responde, `--loss` si no, con el error literal al lado |
| Contador de certificadas | filas del catálogo con `status` certificado y `route=FONDEO` | `0` real, en gris |

### 2.2 Embudo de estados (spec 18)

Los cuatro estados de la spec **existen tal cual** en la API:
`getStrategyLabOverview().pipeline` devuelve `{ extracted, structurally_verified,
backtest_verified, certified_current, approved_datasets }`. No hay que inventar nada ni derivarlo
en cliente.

Se pinta como **cuatro números con flechas**, no como gráfica de colores. Un estado superior
exige la evidencia correspondiente (spec 18): la UI **no promociona** una estrategia por tener
métricas bonitas. Si `certified_current` es 0, el último tramo se pinta en gris `--text-3`, no en
rojo: es ausencia, no fallo.

### 2.3 El catálogo (la tabla)

Fuente: `getCandidatosCanonicos()` → `/api/v1/candidates?include_rejected=true` (verificado
contra la BD: 578 filas). **Una sola fuente de verdad**, como exige el "Criterio de calidad" de la
spec 18: cero clasificación de rentabilidad reimplementada en el cliente.

Columnas, en este orden (identidad primero, métricas después — la spec pone la identidad en
primera fila):

| Columna | Campo | Formato / regla |
| :--- | :--- | :--- |
| Identificador | `candidate_id` | mono, truncado con tooltip completo |
| Símbolo · TF | `symbol`, `timeframe` | texto gris |
| Arquetipo | `archetype` | gris; `NO EVIDENCE` si `null` |
| Ruta | `route` | `FONDEO` / `ULTRA`. Las ULTRA se muestran atenuadas con la etiqueta **EN CONSTRUCCIÓN**, nunca ocultas ni borradas |
| Estado | `status` | `CERTIFIED_CURRENT` verde · `REJECTED_*`/`BUSTED` rojo · **todo lo demás gris**. Texto plano, jamás chips de colores |
| Gates | `gates_passed_count` | `n/11`. **`null` ⇒ `NO EVIDENCE`; `0` ⇒ `0/11`.** Son cosas distintas y la tabla debe distinguirlas (ver §4) |
| PF OOS | `profit_factor_oos` | 2 decimales, tabular. Verde si ≥1, rojo si <1, gris si `null` ⇒ `NO EVIDENCE` |
| Ops OOS | `trades_oos` | entero tabular. **El criterio 1.1 pide ≥200**: por debajo se muestra el número real en gris, sin adorno ni alarma |
| DD OOS | `max_dd_oos_pct` | rojo (es pérdida por definición); `null` ⇒ `NO EVIDENCE` |
| Hash | `strategy_sha256` | mono, 8 primeros caracteres + copia al portapapeles |
| Dataset | `dataset_id` | mono truncado; `NO EVIDENCE` si `null` |

Filtros (spec 18, función 1): texto libre sobre id/símbolo/arquetipo, y selects nativos de
`route`, `status` y `timeframe`. **Sin filtro por exchange/venue/capital** — está prohibido por
la spec. Orden por columna, nativo, sin librería de tablas.

## 3. Las cuatro secciones modulares

Cada una es un panel plegable bajo el catálogo. **Ninguna inventa datos**: si el endpoint no
existe todavía, la sección dice qué falta y por qué, en gris.

| Sección | Qué muestra | Origen HOY | Deuda declarada |
| :--- | :--- | :--- | :--- |
| **M1 Generación (StrategyQuant X)** | Estado de SQX, proyecto/databank de procedencia, caudal de crudas, y las extracciones con su linaje | `getStrategyLabSQXStatus()`, `getStrategyLabStrategies()` (trae `source_project`, `source_databank`, `source_strategy_name`, `strategy_hash`, `dataset_hash`) | El "caudal por hora de CPU" (la métrica que pide M1) no tiene endpoint: se muestra `NO DISPONIBLE` hasta que exista |
| **M2 Mejora** | El loop por candidata: iteración, gate que falló, historial de linaje | `getLineageTree(strategyId)` existe y da padres/hijos/generación/mutaciones | `services/improvement/` **aún no existe** (se sella tras I2). La sección se maqueta con el árbol de linaje real y declara el resto `EN CONSTRUCCIÓN`. **No se simula un loop que no corre** |
| **M3 Valoración fondeo** | Ranking estrategia × firma, P(pasar), P(ruina), horarios | `getCertifiedStrategies()` | Bloqueada de raíz: **requiere ≥1 certificada y hoy hay 0**. La sección muestra el objetivo sellado (≥20 % mensual sobre la mediana, P(ruina) ≤20 %, examen en 3-8 días) y, debajo, "sin candidatas que valorar". El catálogo de firmas llega de I4 por API, **nunca** desde `lib/prop-firms.ts` |
| **M4 Meta** | Composiciones, correlaciones verificadas, examen de la meta | `getCertifiedMetaStrategies()` | Requiere ≥2 certificadas. Muestra el requisito y el marcador real (0/2) |

**Regla transversal**: una sección vacía se explica. `NO EVIDENCE` a secas es correcto en una
celda de tabla; en una sección entera se escribe la razón ("necesita ≥2 certificadas; hay 0").

## 4. La distinción que no se puede perder: `null` ≠ `0`

Es el punto donde esta página puede volverse deshonesta sin que se note, así que se sella aquí:

- `null` / campo ausente ⇒ **`NO EVIDENCE`** en `--text-3`. Significa *no lo hemos medido*.
- `0` ⇒ **`0`**, en el color que le toque. Significa *lo hemos medido y es cero*.

Nunca se colapsan en el mismo símbolo, y **jamás** se sustituye una ausencia por `0`, por un
guion ambiguo o por un valor derivado (spec 18, "Métricas"; spec 19 §1.4).

Aviso operativo para quien implemente: hoy existe el bug **W4.4** (`gates_passed=0` escrito por
tres sitios cuando el conteo real es otro), en reparación por el agente AG-C. La página **no debe
compensarlo**: si la API devuelve `0`, se pinta `0/11`. Maquillar el dato en el cliente sería
exactamente la clase de mentira que la doctrina prohíbe; el arreglo va en el backend.

## 5. Estética (spec 19, resumen operativo)

Todo gris sobre `--bg #0f0f0f`. Los **únicos** colores son `--profit #34d399` y `--loss #f87171`,
y solo para: PnL, PF, drawdown, estado `CERTIFIED_CURRENT` / `REJECTED_*`, y el punto de conexión
de la API. Cero azules, ámbar o morados; un aviso se escribe en gris ("⚠ datos 08-2026 sin
re-verificar"), no en amarillo.

Números en tablas con `font-variant-numeric: tabular-nums` y alineados a la derecha. Mono solo
para hashes e ids. Bordes de 1px con `--border`. Radios 8px. Transiciones ≤150 ms. Nada parpadea.

## 6. ULTRA en esta página — presente, atenuado, nunca borrado

Mandato explícito: ULTRA queda **EN CONSTRUCCIÓN** y visible en todo el proyecto, y nada de lo
que se construya ahora puede cerrarle la puerta. En esta página, en concreto:

1. La columna `route` **no se filtra por defecto a FONDEO**: se muestran las dos rutas, y las
   filas `ULTRA` salen atenuadas con su etiqueta EN CONSTRUCCIÓN.
2. El embudo de estados y el catálogo son **agnósticos al track** (decisión sellada #24: el
   descubrimiento es el mismo, la diferencia está en la envolvente). No se codifica ninguna
   suposición de "solo FONDEO" en los tipos ni en los componentes.
3. Las secciones M1 y M2 sirven a los dos tracks sin cambios. Solo M3 y M4 son específicas de
   fondeo, y sus gemelas ULTRA (F05 envolvente de balas, F06 meta-router) se nombran como
   EN CONSTRUCCIÓN en el pie de esas secciones, con enlace a `state/PUNTO_GUARDADO_ULTRA.md`.

Prueba de que no se cierra la puerta: reactivar ULTRA no debe exigir tocar esta página más que
para quitar la atenuación.

## 7. Qué se conserva del código actual y qué se tira

**Se conserva**: `apps/web/lib/api.ts` (cliente canónico tipado, `fetchJson` ya fail-closed) y
`apps/web/app/estrategias/verificacion.ts` (125 LOC). El shell, el header y el sidebar se
mantienen y solo se re-estilan.

**Se reescribe de cero**: el contenido de `apps/web/app/estrategias/page.tsx` (374 LOC).

**Se replantea**: `SQXToolsPanel.tsx` (16 KB) pasa a ser el cuerpo de la sección M1 en vez de un
panel suelto — mismo código, nuevo sitio, re-estilado a los tokens.

**Se aparca**: `components/MotorBacktestView.tsx` (458 LOC, cero importadores) → cuarentena con
manifiesto SHA-256. Nunca `rm`.

## 8. Checklist de aceptación (lo re-ejecuta el orquestador)

1. `grep -rniE "#[0-9a-f]{3,8}|blue|amber|purple|indigo|yellow" apps/web/app/estrategias/` → solo
   los tokens de la spec 19. Cero colores ajenos.
2. `grep -rn "5\.4\.0" apps/web/` → cero apariciones (la versión se lee de la API).
3. `grep -rn "BingX\|venue\|initial_capital\|25K\|50K" apps/web/app/estrategias/` → cero: la spec
   18 lo prohíbe en esta página.
4. Ninguna llamada `fetch(` cruda dentro de `app/estrategias/`: todo pasa por `lib/api.ts`.
5. Con la API caída, la página muestra el error literal y **ninguna métrica inventada**
   (prueba: apagar la API y cargar).
6. Con la API viva, ninguna celda muestra `0` donde la API devuelve `null` (prueba dirigida sobre
   una fila con `profit_factor_oos: null`).
7. Las filas `route=ULTRA` aparecen, atenuadas y etiquetadas EN CONSTRUCCIÓN.
8. `npm run build` sin errores ni imports rotos.
9. Repaso punto por punto contra `18_STRATEGIES_PAGE_SPEC.md` y el checklist §5 de
   `19_UI_STYLE_SPEC.md`, escrito en el informe del agente.

## 9. Lo que este diseño NO resuelve (deuda declarada)

- **La métrica de caudal de M1** (crudas viables por hora de CPU) no tiene endpoint. Hace falta
  uno; hasta entonces, `NO DISPONIBLE`.
- **M2 no tiene backend**: `services/improvement/` se crea tras cerrar I2. La sección existirá con
  el árbol de linaje real y el resto declarado EN CONSTRUCCIÓN.
- **M3 y M4 están vacías por causa real** (0 certificadas), no por falta de UI. Cuando exista la
  primera certificada, esta página es donde se verá — sin tocar el diseño.
- **El catálogo de prop firms** llega de I4; hasta que se sirva por API, la sección M3 muestra el
  aviso gris "datos 08-2026 sin re-verificar" y no lee `lib/prop-firms.ts`.
