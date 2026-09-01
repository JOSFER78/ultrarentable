# EXPEDIENTE I5 — ¿La web se reescribe de cero o se repara? (2026-09-01)

> Investigación ejecutada sobre el código real de `apps/web` (copia local, HEAD `7b7e7311e`).
> Método I0: medición directa, cero asunciones. Comandos: `wc -l`, `find`, `grep` sobre el árbol.

## 1. Los números medidos

| Zona | LOC TS/TSX | Lectura |
| :--- | ---: | :--- |
| `app/` (35 rutas con page.tsx) | 20.566 | El grueso |
| `components/` | 4.001 | Shell + tablas + auth |
| `lib/` | 4.797 | **4.307 son `prop-firms.ts`** (BD de firmas hardcodeada en cliente); `api.ts` solo 148 |
| `hooks/` | 409 | — |
| **Total** | **29.773** | |

**Lo que la misión FONDEO necesita** (catálogo, gates, fondeo, plan, shell, login):

| Pieza | LOC | Estado real |
| :--- | ---: | :--- |
| `/estrategias` (page 374 + SQXToolsPanel 382 + verificacion 125) | 909 | Vivo; lee el catálogo canónico vía `lib/api.ts` (`/api/v1/candidates`, verificado contra BD 578 filas); NO implementa aún los 4 estados de la spec |
| `/gates` + detalle | 1.621 | Vivo; badge `5.4.0` hardcodeado |
| `/fondeo` | 305 | Vivo |
| `/candidatos` | 7 | Wrapper |
| `/plan` + PlanGraph | ~400 | Recién hecho; lee los bloques de orchestration (correcto por doctrina) |
| Shell (AppShell+Header+Sidebar) + AuthModal | ~1.760 | Sano; Sidebar enlaza rutas muertas |
| `lib/api.ts` cliente canónico tipado | 148 | Sano; `fetchJson` ya es fail-closed (fix 01-09) |
| **Núcleo útil total** | **~5.200** | **El 17 % del código** |

**El peso muerto para el mandato actual** (~12.500 LOC, el 42 %): `trading-desk` 3.885,
`research(+lab)` 1.160, `ejecucion` 1.073, `tradesfera` 846, `bifurcacion` 748, `proveedores`
623, `portfolio` 556, `robots` 373, `ultra` 358, `nautilus` 340, `backtest` 337, `strategyquant`,
`leaderboard`, `campaigns`, `seguimiento`, `data`… Ninguna la exige FONDEO hoy.

## 2. Lo roto de verdad, enumerado (y su tamaño)

1. `lib/firebase.ts` mezcla dos proyectos (goalskid + pecemi) — 29 LOC, fix de `.env.local`.
2. Badges `v5.4.0` hardcodeados en `layout.tsx`, `app/page.tsx`, `app/gates/page.tsx` — 5 puntos.
3. `/estrategias` no modela los estados de la spec (`EXTRACTED → STRUCTURALLY_VERIFIED →
   BACKTEST_VERIFIED → CERTIFIED_CURRENT`) ni el `NO EVIDENCE` sistemático — es reescritura de
   CONTENIDO de una página de 374 líneas, no de la app.
4. `components/MotorBacktestView.tsx` (458 LOC): **cero importadores** — muerto, a cuarentena
   (la spec prohíbe reintroducirlo; hoy solo estorba).
5. `lib/prop-firms.ts` (4.307 LOC): base de datos de firmas como código de cliente — duplicada
   respecto al backend y además caducará con I4; debe pasar a servirse por API desde
   `PROP_FIRM_CATALOG` re-verificado.
6. `fetch()` crudo disperso (9 en `ejecucion`, 8 en `trading-desk`, 5 en `research`…) saltándose
   `lib/api.ts` — casi todo en zonas de peso muerto que se van a aparcar igualmente.
7. Build de producción aún sin ejecutar (pendiente W5.5, se hace en el PC).

**Sano y moderno**: Next 14.2 + React 18 + Tailwind 4, dependencias mínimas (5), tipos
canónicos completos en `lib/api.ts`, el patrón cuarentena-con-manifiesto ya rodado (16 rutas
retiradas el 01-09).

## 3. VEREDICTO: PODAR Y REPARAR EN SITIO. NO reescribir la app de cero.

**Por qué NO de cero:**

1. El problema es de **anchura** (35 rutas, 42 % peso muerto), no de podredumbre del núcleo. La
   anchura se corta con cuarentena en horas; una reescritura no corta nada que la poda no corte.
2. El núcleo útil (~5.200 LOC) es delgado, tipado y ya apunta a la API canónica con fail-closed.
   Una app nueva acabaría siendo *esto mismo* reescrito, perdiendo `/plan` (recién alineado con
   la doctrina), el shell/auth y los fixes auditados (fetch fail-closed, force-static).
3. **El riesgo histórico nº 1 de este repo es la dualidad** (dos suites de gates, dos entradas
   de minería, dos nombres de databank…). "Web nueva junto a web vieja" crea exactamente otra
   dualidad mientras conviven — el fallo que F00 lleva semanas extirpando.
4. Lo roto real (§2) son ~6 items acotados; coste estimado 1-2 días de agente. Paridad de una
   reescritura: 1-2 semanas + riesgo de regresión sin test suite de UI.

**Pero con dos reescrituras QUIRÚRGICAS dentro de la app (aquí sí, de cero):**

- **El contenido de `/estrategias`** (374 LOC) se reescribe desde cero contra
  `docs/18_STRATEGIES_PAGE_SPEC.md`: modelo de 4 estados, `NO EVIDENCE` nunca 0, identidad
  (hash, dataset_hash, procedencia) en primera fila, sin venue/capital. Conserva `lib/api.ts`
  y `verificacion.ts` como base.
- **La home** (`app/page.tsx`): pasa de escaparate v5.4.0 a panel FONDEO honesto (versión de
  motor dinámica, marcador real de certificadas — aunque sea 0 —, estado de campañas/cola).

## 4. Plan de obra resultante (sustituye a W5.1-W5.3 del plan de ejecución)

| Paso | Qué | Tamaño |
| :-- | :--- | :--- |
| 1 | Cuarentena con manifiesto de ~15 rutas fuera de misión (trading-desk, research(-lab), ejecucion, tradesfera, bifurcacion, proveedores, portfolio, robots, nautilus, backtest, strategyquant, leaderboard, campaigns, seguimiento, data) + `MotorBacktestView.tsx`; Sidebar reducido a: Inicio · Estrategias · Candidatos · Gates · Fondeo · Prop-firms · Plan · Sistema. Rutas ULTRA restantes con banner EN CONSTRUCCIÓN | horas |
| 2 | Reescritura in-situ de `/estrategias` contra la spec (de cero, 374→nuevas) | 1 día agente |
| 3 | Fixes enumerados: firebase env, badges dinámicos desde `engine_version`, home honesta | horas |
| 4 | `lib/prop-firms.ts` → endpoint desde `PROP_FIRM_CATALOG` cuando I4 entregue el catálogo re-verificado (mientras, banner "datos 08-2026 sin re-verificar") | tras I4 |
| 5 | `next build` de producción EN EL PC + deploy (VPS y/o Firebase Hosting) | horas |

## 5. Afirmaciones previas del repo: contrastadas

- "16 rutas duplicadas retiradas" (F09) — CONFIRMADO (cuarentena con manifiesto existe).
- "fetchJson fail-open corregido" — CONFIRMADO en `lib/api.ts`.
- "La web debe leerse desde una sola API" (spec) — INCUMPLIDO hoy en zonas muertas (fetch
  disperso); se cumple podando + paso 2.
- "No reintroducir MotorBacktestView" (spec) — el fichero EXISTE pero sin importadores;
  se cumple llevándolo a cuarentena.
