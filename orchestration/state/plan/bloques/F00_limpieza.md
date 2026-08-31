---
id: F00
titulo: "Limpieza del código"
estado: EN_CURSO
depende_de: []
desbloquea: ["F01", "F02"]
verificacion_global: "Un mapa de una página de qué es el sistema, sin ambigüedad."
actualizado: "2026-08-31"
---

# FASE 0 — LIMPIEZA DEL CÓDIGO

> Petición explícita del usuario: *"primero deberías limpiar el proyecto de ruido y dejarlo claro,
> en código y luego en front"*. Front va en la Fase 9.

## 0.1 Resolver los dos árboles de validación

**Estado:** EN_CURSO — auditoría con verificación adversarial lanzada 2026-08-31.

Existen `services/validation/` y `services/api/app/validation/`. `gate_09` vive en el segundo.
Hay que determinar cuál está vivo (quién lo importa desde `main.py`, `mine.py` y los tests),
comparar los gates duplicados fichero a fichero, y **dejar uno solo**. El otro a `cuarentena/`.

- **Verificación:** `grep -rn "from services.*validation"` da un único árbol. Los 11 gates existen
  una sola vez. `pytest` no empeora respecto al estado actual.
- **Riesgo si no se hace:** dos pipelines de certificación distintos ⇒ una estrategia puede estar
  "certificada" por el árbol muerto. Es el fallo más grave que puede tener este repo.

## 0.2 Cuarentena de servicios muertos

**Estado:** EN_CURSO — auditoría de alcanzabilidad lanzada 2026-08-31.

`services/` tiene ~25 subdirectorios. Determinar cuáles son alcanzables desde los puntos de
entrada vivos (`services/api/app/main.py`, `scripts/mine.py`, `services/background_searcher.py`,
`tests/`). Lo no alcanzable va a `cuarentena/services_muertos/` con manifiesto SHA-256.

- **Verificación:** el árbol de imports desde los 4 puntos de entrada cubre el 100 % de lo que
  queda en `services/`. Cero borrados.

## 0.3 Una sola base de datos canónica

**Estado:** EN_CURSO — inventario de referencias lanzado 2026-08-31.

Hoy hay 5 ficheros de BD y **3 están vacíos** (`data/sqlite.db`, `data/candidates.db`,
`data/state.db`: 0 bytes, 0 tablas). La real es
`~/.local/state/ultrarentable/ultrarentable.sqlite3` (64 MB, 33 tablas).

- Las vacías a cuarentena. `learning_store.sqlite` (280 KB, 11 tablas): determinar si vive.
- **Verificación:** un solo `DB_PATH` en todo el código; `grep -rn "sqlite" --include=*.py` no
  apunta a ninguna ruta muerta.

## 0.4 Un solo punto de entrada de minería

**Estado:** EN_CURSO — auditoría de solapamiento lanzada 2026-08-31.

`scripts/mine.py` ya consolida los 26 legacy (hecho, manifiesto 26/26 verificado). Falta cerrar:
`services/background_searcher.py` y `mine.py` no pueden ser dos caminos distintos hacia SQX.

- **Verificación:** `mine.py --dry-run` funciona en los dos tracks; el searcher lo invoca a él
  o queda documentado por qué son dos cosas distintas.

## 0.5 Filas 5.5.0 y estado del servicio de discovery (corregido tras la auditoría)

**Estado:** ACLARADO por la auditoría adversarial del 31-08 (16 agentes).

**Corrección de atribución:** las 120 filas `APPROVED_CURRENT_ENGINE@5.5.0` las escribió
**`scripts/campana.py → scripts/mine.py`** entre 06:46 y 07:17 (formato de ID `_cNNN`, log
`campana_03.log`), **no** el daemon `ultrarentable-discovery` como se afirmó aquí inicialmente.
El 5.5.0 era el SSOT legítimamente vigente en ese momento (el bump a 5.6.0 llegó una hora
después): fue carrera de versiones, no código rancio en memoria. Parar el daemon no evita la
repetición; lo que la evita es la regla #26 aplicada tras cada bump (`scripts/gobernanza_regla26.py`).

**`gates_passed=0` es un BUG DE PERSISTENCIA, no aprobación laxa:** la columna tiene DEFAULT 0
y NINGUNO de los 3 escritores vivos (`mine.py`, `discovery_validation_pipeline.py`,
`legacy_revalidation_service.py`) la escribe. El scorecard de las 120 confirma 11/11 gates.
Su reclasificación a `LEGACY_MOTOR_VERSION_OBSOLETA` sigue siendo correcta por la regla #26
(motor no vigente), pero el motivo "sin gates" de la razón escrita queda matizado. Fix del bug:
Fase F del plan de acción (escribir `gates_passed` en los 3 escritores).

- El daemon `ultrarentable-discovery` sigue siendo un orquestador CLON de `mine.py` (misma
  certificación); su unificación queda en 0.4/Fase I. Pararlo ya no es urgente, es opcional
  mientras dure la limpieza (sigue quemando CPU en celdas cripto ya barridas).

---

## RESULTADO DE LA AUDITORÍA (2026-08-31, 16 agentes + verificación adversarial)

**0.1 — RESUELTO con criterio redefinido.** Los dos árboles NO son duplicados: son dos
implementaciones distintas de los 11 gates, AMBAS vivas. `services/validation/` está montado en
la API (`/api/v2/validation`, gates "suite A" ejecutados por `validation_router.py`) y contiene
el motor oficial (`engine/event_backtest_engine.py`). `services/api/app/validation/` es el
pipeline de certificación de facto (`GatePipelineOrchestrator`) usado por `mine.py` y discovery.
El criterio original ("un único árbol en grep") es INALCANZABLE sin romper producción; el
criterio vigente pasa a ser: *ningún fichero fuera de cuarentena queda sin importador vivo* +
el catálogo desinformante `GET /api/v2/validation/engines` se corrige en tarea separada auditada.
Único huérfano real del árbol A: `certify_all_strategies_v540.py` (a cuarentena en Fase C).

**0.2/0.3 — EN EJECUCIÓN** por subagente (Fases C–G del plan de acción): ~14 huérfanos
confirmados a `cuarentena/servicios_muertos/`, BDs muertas/rancias a `cuarentena/bd_vacias/`
(con fix previo de `services/core/runtime_paths.py` y des-listado de la BD canónica en 2
scripts de mantenimiento), literales muertos, y fix del bug de persistencia `gates_passed`
en los 3 escritores. Tests de código ya cuarentenado → `cuarentena/tests_muertos/`.

**0.4 — MAPA CERRADO, unificación pendiente (Fase I).** Dos orquestadores CLÓNICOS
(`mine.py` CLI y `discovery_validation_pipeline.py` systemd) sobre el mismo motor y misma
certificación; `background_searcher.py` es un camino DISTINTO (SQX vía MCP) con proxy web vivo.
Además hay DOS motores de backtest vivos (`EventBacktestEngine` oficial y
`UniversalDeterministicBacktestEngine` en `services/engine/` + adapter).

## Decisiones de Fase I (selladas por el orquestador, 2026-08-31)

1. **`scripts/meta.py` y `scripts/fondeo_examen.py` son puntos de entrada VIVOS** (corrieron el
   31-08 y alimentan F06/F07). No se toca `services/portfolio/meta_strategy_engine.py`.
2. **`services/sqx_bridge/` NO se mueve** (`sqx_gui_automation.py` es procedimiento operativo P1
   documentado en `docs/Estado/auditoria/17B_SUPERFICIE_UI_SQX.md`).
3. **`background_searcher.py` se conserva** hasta la unificación 0.4 (tiene proxy Next.js vivo y
   es el único camino a SQX por MCP); la unificación se hará con sus 3 piezas a la vez (servicio,
   endpoint `routes.py:1424-1439`, `apps/web/app/api/search/background/route.ts`).
4. **`data/db/learning_store.sqlite` (28 MB, 7.852 debates, 2.827 autopsias) NO SE BORRA NUNCA**
   (no está en git, irreversible). Decisión de fusión con el `learning_store.sqlite` vivo de la
   raíz: pospuesta a F04 (capa semántica), que es su consumidor natural.
5. **Unificación de `DB_PATH`: HECHA (2026-08-31 tarde).** Inventario propio ejecutado y los 7
   cambios aplicados: SSOT único `services/api/app/config.py::STATE_DB_PATH` (con alias legacy
   `ULTRARENTABLE_DB_PATH`; `ULTRA_DB` eliminado), 11 literales de `services/` y 12 scripts
   migrados, el singleton de `expert_refinement_loop` ya no congela la ruta en import (era el
   canal por el que DOS tests escribían en la BD de producción — verificado cerrado con
   `strace`: 0 aperturas RDWR de la canónica en toda la suite), guardrail
   `r0_forbidden_literal_scan` ampliado a todo services/+scripts/ (0 hits), rutas muertas
   des-listadas, y `learning_store.sqlite` movido a `~/.local/state/ultrarentable/` con
   `LEARNING_DB_PATH` en config. pytest: 25 fallos (mejora desde 28). El histórico
   `data/db/learning_store.sqlite` intacto (sha256 verificado).
6. **Unificación de los 2 motores de backtest:** entra como subfase nueva 0.6, DESPUÉS de que
   F02 termine sus releases sobre `EventBacktestEngine` (evitar carreras de edición).

## Notas de ejecución

- 2026-08-31: workflow `fase0-auditoria-limpieza` completado (16 agentes, 0 errores). Síntesis
  y plan de acción A–I archivados en el journal del workflow; refutados relevantes: DB-04
  (mecanismo falso), CL-05 (`paper_executor.py` tiene importador vivo), 0.4-C1 (no vio el
  segundo motor), y la nota `reviews/limpieza_01_arboles_validacion.md` (marcada como superada).
