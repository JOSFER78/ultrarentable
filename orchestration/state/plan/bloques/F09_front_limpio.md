---
id: F09
titulo: "Front limpio"
estado: PARCIAL
depende_de: ["F08"]
desbloquea: []
verificacion_global: "Cero datos inventados en la web: sin dato ⇒ SIN DATOS. Acceso solo autorizados."
actualizado: "2026-09-02"
---

# FASE 9 — FRONT LIMPIO

> *"y luego en front"*.

- Consolidar las 33 páginas actuales en **páginas maestras con subpáginas jerarquizadas**.
- Cero datos inventados: si no hay dato, `SIN DATOS`, nunca un valor de relleno.
- Landing sin autenticar; acceso solo para autorizados por `josferestudio@gmail.com`.
- Firebase se mantiene en PECEMI de momento, pero el `apiKey` sale del código a variable de
  entorno con fallo explícito si falta.
- Trading desk (BingX para ULTRA, gestión de cuentas para FONDEO) **al final**, cuando haya
  algo real que mostrar.

## Integración con el plan por bloques (añadida 2026-08-31)

La página del plan en `apps/web` debe leer estos ficheros de `orchestration/state/plan/bloques/`
(frontmatter YAML: `id`, `titulo`, `estado`, `depende_de`, `desbloquea`, `verificacion_global`,
`actualizado`) y renderizar el grafo de fases con su estado real. Un bloque = una tarjeta
editable. Nada de estados duplicados a mano en el front: la fuente de verdad es el fichero del
bloque.

## Actualización 2026-09-01 — primera pasada de limpieza real

Auditoría en cuatro frentes paralelos sobre 54 rutas y 20.420 líneas de TSX, seguida de tres
carriles de ejecución con revisión adversarial.

- **Diez rutas eran envoltorios literales** de otras ya existentes: ficheros de 7 a 13 líneas que
  sólo hacen `import X from otra-ruta; return <X/>`. Dos de ellas reexportaban *la misma* página.
  Sobrevivían porque el Sidebar las enlazaba con nombres que ni siquiera coincidían con las
  carpetas reales.
- Se retiran **16 ficheros** a `cuarentena/web_superseded/2026-09-01/` con manifiesto SHA-256,
  verificado uno a uno: los 16 están en cuarentena y su hash coincide. No se borró nada.
- Los siete `route.ts` de la API dejan de declarar `force-static`, que congelaba en el build las
  respuestas de endpoints vivos.
- `fetchJson` deja de devolver `[]` en silencio ante un JSON inválido: era un fail-open que hacía
  indistinguible "no hay candidatas" de "la API no responde".
- **El plan se lee de estos bloques**: `/plan` y `/api/plan` parsean el frontmatter de
  `orchestration/state/plan/bloques/*.md` en vez de duplicar los estados a mano, que es lo que
  exige la doctrina.

**Deuda declarada**: el build de producción NO se ha ejecutado. Los revisores verificaron por
lectura que ningún import queda colgando, pero eso no lo sustituye. La VPS está saturada por
procesos ajenos y lanzar `next build` encima sería justo lo que hay que evitar.

## Actualización 2026-09-02 noche — rediseño "solo lo que funciona" y especificación de la web

Mandato de Emilio (02-09): el usuario no quiere ver estrategias fallidas ni menús a páginas que no
funcionan; quiere las estrategias que ya funcionan con todos sus datos, los 4 bloques explicados en
llano, y que `/plan` tenga el plan completo (tareas por fase con estado) sincronizado con los
ficheros de estado, más el concepto y la especificación detallada de la web.

- **Especificación de la web**: `orchestration/state/ESPECIFICACION_WEB.md` (concepto, reglas
  selladas, mapa del sitio, contrato página a página, fuentes de datos, estado de implementación,
  despliegue). Es la fuente de verdad de la web y se actualiza con cada cambio.
- **Hecho** (commit `a6acd91f3`): portada mínima y honesta; `/estrategias` con SOLO las válidas
  (definición sellada: ruta FONDEO, `APPROVED_CURRENT_ENGINE`, motor vigente, ≥200 ops OOS, PF OOS
  ≥1,25, 11 gates con evidencia) y 4 subpáginas `generacion`, `mejora`, `valoracion`, `meta`
  ("Qué hace / Qué necesita / Estado hoy / Qué falta"); la API publica `current_engine_version`.

| ID | Tarea | Estado | Dueño |
| :--- | :--- | :--- | :--- |
| W9.1 | Portada mínima y honesta (3 cifras reales + párrafo + enlaces a páginas que existen) | HECHO 02-09 | orquestador (sesión PC) |
| W9.2 | `/estrategias` solo válidas + 5 módulos explicados en llano (M1 a M5 con Candidatos) | HECHO 03-09 | orquestador (sesión PC) |
| W9.3 | Menú lateral: jerarquía con 16 módulos Tradesfera, 11 subpáginas Gates, M1-M5 Estrategias y 7 vistas Prop-firms | HECHO 03-09 | orquestador (sesión PC) |
| W9.4 | `/plan`: tareas por fase (filas de tablas con ID W/E/B/S) y cuerpo completo de cada bloque, leídos de `plan/bloques/*.md` | HECHO 03-09 | orquestador (sesión PC) |
| W9.5 | `/plan`: pestaña con `ESPECIFICACION_WEB.md` y la nota LEER PRIMERO de `current_phase.md` | HECHO 03-09 | orquestador (sesión PC) |
| W9.6 | Unidad de `net_profit_oos` y ROI con `roi_source` en todas las tablas | HECHO 03-09 | orquestador (sesión PC) |
| W9.7 | Desplegar PC (:3100) y VPS con el build nuevo; procedimiento repetible | EN CURSO | orquestador (sesión PC) |
| W9.8 | Armonizar `/prop-firms` (catálogo 70 cuentas, eliminación de barras superiores duplicadas, diseño sobrio) | HECHO 03-09 | orquestador (sesión PC) |
| W9.9 | Trading Desk: cabecera con estado real "sin motor conectado" hasta que haya una válida | HECHO 03-09 | orquestador (sesión PC) |
