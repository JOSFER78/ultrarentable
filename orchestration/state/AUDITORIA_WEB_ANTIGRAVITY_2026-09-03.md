# AUDITORÍA REAL-ONLY del `/plan` y de la web hecha por Antigravity (VS Code) — 2026-09-03 00:40 UTC

> Auditor: sesión Claude Code del PC (orquestador). Emilio trabaja en VS Code con Antigravity; el
> agente del IDE está editando `apps/web` en vivo (árbol sin commitear) y sirve la web con
> `next dev -p 3100`. Lo de abajo está **medido en ese árbol**, no supuesto. Cada punto lleva el
> comando con el que se ve. El bloque final es la instrucción lista para pegar en Antigravity.

## 1. Lo que ya está bien (verificado)

- `/api/plan` lee los 10 bloques `orchestration/state/plan/bloques/F*.md` (frontmatter + cuerpo)
  y `/api/plan/doc?name=` sirve `current_phase.md`, `ESPECIFICACION_WEB.md`, `plan_maestro.md`,
  `VENTANA_EMILIO.md`, los traspasos y cualquier `Fxx`. Esa es la sincronización con los MD que
  Emilio pide. (`curl http://127.0.0.1:3100/api/plan` → `count: 10`, con `content`.)
- Cada fase se despliega y muestra su cuerpo (PlanGraph con `expandedIds`); el visor de documentos
  (`DocViewer.tsx`) abre los MD. `tsc --noEmit` del árbol vivo: ver §4.

## 2. Lo que rompe REAL-ONLY (hay que corregir antes de dar `/plan` por bueno)

| # | Dónde | Qué pasa | Cómo se ve |
| :--- | :--- | :--- | :--- |
| 1 | `apps/web/app/api/plan/route.ts` líneas 399-413 (`const hud`) | El HUD lleva valores **escritos a mano**: `motor_version: "5.18.0"`, `vps_status: "OPERATIVO (…)"`, `api_status: "ACTIVA (…)"`, `campana_activa: "E2 …"`, `ultimo_hallazgo: "E2 5m: 400 …"`. Cuando el motor pase a 5.19.0 o el VPS se caiga, la página seguirá diciendo lo mismo. | `grep -n "motor_version\|vps_status\|api_status" apps/web/app/api/plan/route.ts` |
| 2 | `apps/web/app/plan/page.tsx` (`const hud = data?.hud ?? {...}`) | Mismo HUD duplicado como valor por defecto en el cliente: si la API falla, pinta "5.18.0 / OPERATIVO / ACTIVA" inventados en vez de "sin evidencia". | `grep -n "OPERATIVO\|5.18.0" apps/web/app/plan/page.tsx` |
| 3 | `route.ts` líneas 273-279 y `apps/web/app/estrategias/page.tsx` | "**578** candidatas" escrito a mano. La API real devuelve 728 hoy (`/api/v1/candidates`), y mañana otra cifra. | `grep -rn "578" apps/web/app apps/web/components` |
| 4 | `route.ts` líneas 305-355 (`rutas_web`) | Todas las rutas marcadas `estado: "IMPLEMENTADA"` a mano, incluidas Trading Desk (sin motor conectado) y Prop Firms (fuente sin verificar). El estado de cada página debe salir de `orchestration/state/ESPECIFICACION_WEB.md` §6, no de una constante. | `grep -n 'estado: "IMPLEMENTADA"' apps/web/app/api/plan/route.ts` |
| 5 | `route.ts` `tareas_totales: taskRows.length > 0 ? taskRows.length : 1` | Cuando un bloque no tiene tabla de tareas, inventa 1 tarea (barra de progreso 0/1 falsa). Debe ser 0 y la barra no pintarse. | leer la línea |
| 6 | `route.ts` `DOCTRINA_ITEMS` y `pipeline` (M1-M5) | Texto de doctrina y "estado" de cada módulo (`ACTIVO_VPS`, `EN_CURSO`…) escritos a mano en el código. Deben leerse de los MD (`plan_maestro.md`, `ARQUITECTURA_MODULAR_ESTRATEGIAS.md`, `ESPECIFICACION_WEB.md`) o, si son constantes de doctrina, marcarse como "texto sellado" con la fecha y el fichero del que se copiaron. | leer líneas 170-300 |
| 7 | `apps/web/app/estrategias/page.tsx` y `components/layout/Sidebar.tsx` | Los **4 bloques** acordados con Emilio (Generación, Mejora, Valoración, Meta) se han convertido en 5 ("Candidatos Estrategias" como 4 y "Candidatos Meta-Estrategias" como 5); el menú salta del 3 al 5. El archivo técnico de candidatas va en el pie de `/estrategias`, no como módulo. | `git diff apps/web/app/estrategias/page.tsx` |
| 8 | `Sidebar.tsx` | Submenús que prometen cosas sin datos vivos: Trading Desk "Terminal y DOM", "Sentinel de riesgo", "Conexión gateway"; Prop Firms con 7 vistas. Regla sellada: el menú solo enlaza lo IMPLEMENTADO (`ESPECIFICACION_WEB.md` §2.9 y §6). | `git diff apps/web/components/layout/Sidebar.tsx` |
| 9 | `orchestration/state/ESPECIFICACION_WEB.md` §3 | El agente reescribió el mapa del sitio con "5 módulos", "578 estrategias", "70 prop firms", "11 subpáginas de gates". Ninguna de esas cifras está medida en este documento; el mapa vuelve a los 4 módulos y las cifras salen. | `git diff orchestration/state/ESPECIFICACION_WEB.md` |

## 3. Cómo debe alimentarse el HUD (fuente real para cada dato)

| Dato del HUD | Fuente real | Si falla |
| :--- | :--- | :--- |
| Motor vigente | `GET /api/v1/discovery/status` → `current_engine_version` | "sin evidencia" |
| API / VPS | `GET /api/local/status` y el propio éxito de `discovery/status` (código 200 + latencia) | "sin conexión" en gris/rojo |
| Estrategias listas para FONDEO | `GET /api/v1/certified` filtrado en cliente con `esValidaFondeo` (`apps/web/app/estrategias/_bloques/comun.tsx`) | "sin evidencia" |
| Meta-estrategias aprobadas | `GET /api/v1/certified-meta` con `status === APPROVED_CURRENT_ENGINE` **y** `engine_version === motor vigente` | 0 real o "sin evidencia" |
| Campaña activa / último hallazgo | `GET /estrategias/api-telemetria` (`campanas[0]`) y la primera nota "LEER PRIMERO" de `orchestration/state/current_phase.md` (vía `/api/plan/doc?name=current_phase`, primeras líneas) | "sin evidencia" |
| Criterio sellado | texto fijo permitido, con cita: "criterio 1.1, `PLAN_LOCAL_FONDEO.md`" | — |
| Alertas | `VENTANA_EMILIO.md` §0 (decisiones pendientes de Emilio), leído del fichero | lista vacía |

## 4. Estado del árbol vivo en el momento de la auditoría

- `tsc --noEmit` (apps/web) sobre el árbol vivo a las 00:41 UTC: **rc=0** (compila con los cambios de Antigravity).
- Tres editores sobre el mismo checkout: Antigravity (IDE), sesión Claude `ultrarentablepc-12`
  (en pausa, solo lectura desde 00:35) y esta sesión (solo `orchestration/` y `services/`).
  Hasta que Antigravity commitee, nadie más toca `apps/web`.
- El build de producción no puede correr mientras `next dev` escribe en el mismo `apps/web/.next`
  (fallo verificado: `PageNotFoundError /_document`). Despliegue al VPS: después del commit.

## 5. Instrucción lista para pegar en Antigravity

```
Corrige /plan y la web según orchestration/state/AUDITORIA_WEB_ANTIGRAVITY_2026-09-03.md, puntos 1-9 de §2,
con las fuentes de §3. Reglas: REAL-ONLY (ninguna cifra ni estado escrito a mano; sin dato = "sin evidencia");
4 bloques (Generación, Mejora, Valoración, Meta), el archivo técnico de candidatas en el pie de /estrategias;
el menú solo enlaza páginas IMPLEMENTADAS según ESPECIFICACION_WEB.md §6; monocromo; tsc --noEmit rc=0.
No toques services/, orchestration/ ni scripts/. Al terminar: git add solo de apps/web y commit con
ORQ_COMMIT=1 git commit, push con ORQ_PUSH=1 git push, y escribe en ESPECIFICACION_WEB.md §8 el estado
real de cada W9.x que hayas cerrado.
```
