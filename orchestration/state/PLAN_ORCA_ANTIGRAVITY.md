# PLAN ORCA + ANTIGRAVITY — ciclo 3 de la era local (2026-09-02)

> **Para el orquestador que arranca en Orca** (worktree `C:/Users/yo/orca/workspaces/ultrarentable/devilray`,
> rama `JOSFER78/orquesta-antigravity-max-10`, hoy al mismo commit que `main`: `a1564650f`).
> **Regla de Emilio para este ciclo: TODO se ejecuta con agentes Antigravity (AGY) — mínimo 10 en
> vuelo — porque son rapidísimos, pero ATADOS.** El orquestador (**Claude Fable 5.1 en Orca**, que
> releva a Opus) planifica, despacha, audita, integra y commitea; **no ejecuta él lo mecánico**.
> Emilio no ejecuta nada (ventana única). Todo lo que en los documentos previos dice "Opus" como
> orquestador se lee "Fable 5.1": el rol es el mismo, cambia el modelo.
>
> Este documento se apoya en la auditoría de lo que hizo Opus en los ciclos 1-2 (§1) y sustituye el
> reparto de agentes de `DESPACHO_MULTIAGENTE.md` (que era para subagentes Sonnet). La doctrina
> (`DOCTRINA_ORQUESTADOR_LOCAL.md`), los planes (`PLAN_INVESTIGACION_PROFUNDA.md`,
> `PLAN_LOCAL_FONDEO.md`), la arquitectura (`ARQUITECTURA_MODULAR_ESTRATEGIAS.md`) y las decisiones
> D1-D10 de `current_phase.md` siguen mandando.

---

## 0. Primer acto del orquestador en Orca: integrar y verificar (antes de despachar nada)

1. `git status` en `main` (el repo raíz `…/UltrarentablePC/ultrarentable`): quedan cambios sin
   commitear de los ciclos 1-2 (AG-C sobre `scripts/fondeo_examen.py`, hooks `.githooks/`,
   plantillas `orchestration/agy/`, este plan, `reviews/EVALUACION_EXTERNA_2026-09-01.md`,
   `ARRANQUE_RAPIDO_ORQUESTADOR.md`). **Auditar AG-C con comandos propios** (W4.1: caso
   `prop_firm_busted=True` jamás imprime CUMPLE) y commitear en `main` en lotes temáticos:
   `docs(orquestación)`, `feat(arnés AGY)`, `fix(examen honesto)`.
   *(Aviso: una sesión Linux montada sobre la carpeta Windows ve ~1.500 ficheros "modificados"
   por finales de línea; no es real. Commitear siempre desde Windows/Orca.)*
2. Traer el worktree a `main`: en devilray, `git merge --ff-only main` (o rebase de la rama
   `JOSFER78/orquesta-antigravity-max-10` sobre `main`). Devilray es el puesto del orquestador;
   los agentes AGY NO trabajan ahí (cada uno en su worktree `agy/<ID>`, §2).
3. Activar el arnés: `git config core.hooksPath .githooks` (afecta a todos los worktrees del
   repo) y comprobar que un `git commit` de prueba en una rama `agy/test` **falla** con el mensaje
   `[ARNÉS]`. Sin esa prueba verde, no se despacha ningún agente.
4. Publicar `VENTANA_EMILIO.md` actualizada (§5) y seguir con lo no bloqueado.

## 1. Auditoría de lo hecho por Opus (ciclos 1-2, 2026-09-01) — punto de partida real

**Veredicto: trabajo de alta calidad y honesto; 9 commits temáticos en `main`; se corrigió a sí
mismo dos veces por escrito.** Lo verificado leyendo `current_phase.md`, `git log`, results/ y reviews/:

| Hito | Estado | Evidencia |
| :--- | :--- | :--- |
| **W0.2 identidad del motor en el PC** | ✅ 15/15 idénticas, incluida huella SHA-256 del ledger. **Minar en el PC es legítimo.** Windows nativo, sin WSL (Python 3.11.8) | `results/verificacion_f02_5.17.0_EJECUCION_PC_2026-09-01.json` |
| ssh PC→VPS y sudo | ✅ ssh sin contraseña; **sudo del VPS sin contraseña** (el "bloqueo de días" era falso). Falta solo AUTORIZACIÓN de Emilio (guardián de la sesión) | `VENTANA_EMILIO.md` §1 |
| VPS | ❌ sigue ahogado: swap 4/4 GB, `memory.events high` = **7.575.123** (eran 713.626) | medido por ssh |
| Datos | ✅ 5 datasets de identidad + YM y NQ rescatados y consolidados (hash 5/5 y 155/155); backfill W1.7 **parado** porque degradaba datasets (contrato escrito); **defecto W1.6**: `market_ingestor` calcula el checksum sobre METADATOS, no contenido | `results/AG-D_datos_2026-09-01.md`, `state/contratos/W17_*` |
| I1 SQX | ✅ expediente; **licencia SQX del PC es TRIAL y caduca el 2026-09-05**; refutado `MaxTradesPerDay=1` (real 0) | `results/I1_sqx_hallazgos.md` |
| I4 prop firms | ✅ catálogo re-verificado contra ToS; **Topstep y TradeDay prohíben operar desde VPS** → vigía V0 permanente, órdenes desde el PC | `results/I4_prop_firms_hallazgos.md`, `HERMES_VPS_VIGIA.md` |
| I7 arquitectura | ✅ grafo 310 nodos/1.003 aristas; conclusión final: las suites NO comparten importadores, pero **divergen en los 11 gates** (4 con fórmulas distintas), la que certifica (B) vive en el monolito con 19 importadores y el catálogo de la web miente (gate 10: 75 vs 40 real). **D5**: registro v1 = paridad con B | `results/grafo_imports_*`, `results/W43_spec_registro_gates.md` |
| I2 mejora | ✅ diseño; `deep_strategy_improver` **fabricaba métricas** → cuarentena | `results/I2_diseno_mejora.md` |
| I3 meta | ✅ diseño; 4 fabricadores de portafolio/meta → cuarentena (**D8**); `services/meta/` nacerá de los 2 módulos vivos; **D9** asignación estática hasta respuesta 5.2 | `results/I3_diseno_meta.md` |
| M3 firmas | ✅ plan de catálogo v2 con `SourceRef` (**D6**, **D7**) | `results/M3_plan_catalogo_firmas.md` |
| FORENSE | ✅ **bug de DST** en la sesión (13:30 UTC fijo) → contrato **motor 5.18.0** (**D10**); E1/E2 se repetirán con 5.18.0 | `state/contratos/W29_motor_5_18_sesiones_dst.md` |
| Telemetría | ✅ el "20/20 sin_ventaja" era artefacto de `--max-candidates` (default 20, trunca por prefijo, 1 familia de 6) → **D1** regla suspendida, **D2** espacio completo o estratificado | `reviews/forense_telemetria_2026-09-01.md` |
| Web | ✅ poda hecha y **primer build de producción verde** (W5.1/5.4/5.6); diseño de la página maestra escrito; falta reescritura (W5.2) y `.env.local` (no existe) | commit `9fa727e7c`, `reviews/diseno_pagina_estrategias_2026-09-01.md` |
| Git | ✅ `main` local == remoto (W0.7); `origin/tmp-sync` intacto | `current_phase` §9 |
| Máquina | ⚠ PC al 100 % con 6 agentes + backfill + Orca×3 + Antigravity IDE ×14 → regla: **2 ejecuciones pesadas + 1 NOHUP** mientras Emilio use el PC | `current_phase` §8 |

**Lecciones de proceso que este plan incorpora**: (a) un agente rechazó correcciones en marcha por
no estar en su contrato → el GO declara que el ORQ puede reorientar; (b) un agente re-generó
datasets en vez de copiarlos → la aceptación compara hash contra manifiesto canónico, siempre;
(c) el ORQ se equivocó midiendo dos veces y lo dejó escrito → la auditoría cruzada (refutadores)
se mantiene.

## 2. EL ARNÉS: cómo se ata a Antigravity (mecánico, no de palabra)

AGY incumplió 5/5 veces el protocolo escrito en 4 documentos. Por eso ahora el protocolo **se
impone por máquina** y los documentos solo lo explican:

| Atadura | Mecanismo | Qué impide |
| :--- | :--- | :--- |
| **1. Aislamiento físico** | Cada agente trabaja en SU worktree de Orca sobre rama `agy/<ID>`; jamás en `main` ni en devilray. `AGY_AGENT=<ID>` en su entorno | Pisar el árbol del orquestador o de otro agente |
| **2. Sin commit** | Hook `.githooks/pre-commit`: bloquea todo commit en ramas `agy/*` o con `AGY_AGENT` definido salvo `ORQ_COMMIT=1`; bloquea datasets pesados en el índice y borrados sin MANIFEST | Los commits "para cerrar" que destruían la revisión de Emilio |
| **3. Sin push** | Hook `.githooks/pre-push`: bloquea cualquier push sin `ORQ_PUSH=1` y todo push de `agy/*` | Publicar en GitHub por su cuenta |
| **4. Contrato GO/DONE** | `orchestration/agy/GO_<ID>.md` obligatorio (plantilla); sin GO no arranca; termina con `DONE_<ID>.md` + informe con salida CRUDA. El GO admite `## CORRECCION_n` del ORQ en marcha | Auto-despacharse; inventar alcance; ignorar correcciones |
| **5. Territorio verificado** | Aceptación automática: `git diff --name-only` ⊆ TERRITORIO del GO; un fichero fuera ⇒ RECHAZO sin leer más | Tocar el motor de gates "de paso" |
| **6. Aceptación re-ejecutada** | El ORQ corre él mismo los comandos de ACEPTACIÓN; el informe del agente es hipótesis, no prueba. Añade greps de la lista negra (`git commit`, `rm -`, `mock`, `random`, `synthetic`, `default=`) sobre el diff | Fraude por dato inventado |
| **7. Puerta de admisión** | Nada pesado (pytest completo, `next build`, campañas, backfills) fuera de `python -m services.ops.gobernanza_recursos ejecutar`; semáforo **2 pesados + 1 NOHUP** | Tumbar el PC (lo que pasó con 6 agentes) |
| **8. Regla #26 explícita** | Si el GO dice que toca semántica del motor, exige bump + baseline F02 + identidad; si no lo dice y el diff toca `services/validation/engine/` o `engine_version.py` ⇒ RECHAZO automático | Cambios de motor silenciosos |
| **9. Timebox + heartbeat** | 45 min; sin DONE al vencer ⇒ el ORQ cierra la sesión, marca `REPITE` con causa y re-despacha | Agentes colgados quemando contexto |
| **10. Refutadores** | Toda tarea de investigación o de motor lleva un segundo agente AGY "refutador" con GO propio: su único objetivo es demostrar que el primero se equivoca | Los errores de medición que ya hemos tenido (los del ORQ incluidos) |

**≥10 agentes sin saturar el PC**: 10-12 agentes AGY en vuelo consumen sobre todo nube; lo que
satura son sus pytest/builds locales. Por eso la atadura 7: diez agentes pensando y editando,
**dos ejecutando cosas pesadas a la vez**. La cola la reparte el ORQ, no los agentes.

## 3. OLA A — 12 agentes AGY (arranque inmediato; independientes entre sí por territorio)

| ID | Objetivo | Territorio | Aceptación (el ORQ la re-ejecuta) |
| :-- | :--- | :--- | :--- |
| **A01 Arnés-aceptación** | `scripts/aceptar_agy.py <ID>`: lee GO, verifica territorio (`git diff --name-only`), corre comandos de aceptación, greps de lista negra, comprueba DONE; veredicto JSON en `results/agy/` | `scripts/aceptar_agy.py`, `tests/test_aceptar_agy.py` | GO de prueba con fichero fuera de territorio ⇒ RECHAZO; con todo dentro ⇒ ACEPTA. **El ORQ lo audita línea a línea: es el arnés** |
| **A02 Refutador de A01** | Intentar burlar el arnés (commit en `agy/*`, push, fichero fuera de territorio, dataset pesado) y documentar cada intento | `results/agy/A02.md` | Cada intento bloqueado con mensaje `[ARNÉS]`; los que pasen ⇒ agujero a cerrar por A01 |
| **A03 W4.6** | `verificacion_f02.py` no sobrescribe jamás su baseline sellado (escribe en `*_EJECUCION_<fecha>.json`) | `scripts/verificacion_f02.py`, su test | ejecutar 2 veces: baseline intacto (sha igual); `--comparar` funciona |
| **A04 W1.6** | Checksum de CONTENIDO en `market_ingestor` (hash de las velas, no metadatos) + verificación contra manifiesto | `services/data/market_ingestor.py`, test | dos series con precios distintos ⇒ hashes distintos; los 5 canónicos verifican |
| **A05 W1.7** | Backfill idempotente que NO degrada datasets (contrato `W17_backfill_idempotente.md`) | `services/data_ingestion/`, test | re-ejecutar sobre símbolo ya consolidado ⇒ 0 cambios; hashes iguales |
| **A06 W4.7 registro de gates v1** | Movimiento 1 de I7 con **D5**: `services/validation/` como registro plugin-style con paridad EXACTA con la suite B; A detrás de adaptador (1 importador); `contracts/gate_directory.py` regenerado desde B; **test de sustitución nº1** | `services/validation/`, `contracts/gate_directory.py`, tests | 11 gates dan el mismo veredicto que B sobre las 15 celdas de identidad; cambiar un gate = diff de 2 ficheros; web gate 10 = 40 |
| **A07 Refutador de A06** | Buscar cualquier gate cuyo resultado difiera entre registro y suite B sobre candidatas reales de la BD | `results/agy/A07.md` | 0 divergencias o lista exacta ⇒ A06 REPITE |
| **A08 W2.9 motor 5.18.0** | Sesiones con DST (hora local + `zoneinfo`), familias con Globex + flat 15:10 CT, bump `5.18.0`, baseline F02 nuevo (contrato `W29_*`). **Toca semántica: regla #26** | `services/validation/engine/`, `services/engine_version.py`, `scripts/verificacion_f02.py` (solo lectura), tests | picos de sesión en 14:30/13:30 UTC ene/jul reproducidos; identidad 5.17→5.18 documentada celda a celda (se ESPERA cambio en las de sesión, cero en las demás) |
| **A09 Refutador de A08** | Demostrar que 5.18.0 cambia operaciones donde NO debería (celdas sin sesión) o no las cambia donde debería | `results/agy/A09.md` | informe con diff de ledgers por celda |
| **A10 W4.2 + W4.4** | Fuera hardcode `5.4.0` (6 ficheros) y `except` mudos; los 3 escritores escriben `gates_passed` real | ficheros listados en `PLAN_LOCAL_FONDEO.md` W4.2/W4.4, tests | grep sin `5.4.0` hardcodeado; fila nueva 11/11 refleja 11 |
| **A11 Telemetría D2 + W27** | `--max-candidates 0` = espacio completo por defecto en campañas; cobertura por familia en cada embudo; bruto/neto por config | `scripts/mine.py`, `scripts/cola_mineria.py`, `services/ops/telemetria*` | embudo JSON con `cobertura_por_familia` 6/6; sin flag ⇒ 420 configs, no 20 |
| **A12 Web W5.2** | Reescritura de `/estrategias` como página maestra M1-M4 según `reviews/diseno_pagina_estrategias_2026-09-01.md` + `docs/18` + `docs/19` (grises, verde/rojo solo P&L); home honesta; "Ultra — EN CONSTRUCCIÓN" visible | `apps/web/app/estrategias/`, `apps/web/app/page.tsx`, `apps/web/components/`, `apps/web/lib/` | checklist §5 de la 19 (grep cero colores fuera de tokens); `next build` verde vía puerta de admisión |

El ORQ, mientras vuelan: auditar A01 en cuanto aterrice (es el arnés de todos los demás), preparar
GOs de la Ola B, releer telemetría E1 si existe, y mantener `VENTANA_EMILIO.md`.

## 4. OLA B — 12 agentes (al aterrizar A01/A06/A08 y con datos de ES en el PC)

| ID | Objetivo | Depende de |
| :-- | :--- | :--- |
| **B01 Datos-ES** | Traer consolidado Dukascopy ES 5m/15m del VPS (42+14 MB) y verificar hash; traer GC/SI/CL si existen; inventario disco PC | ssh (ya OK) |
| **B02 Runner E1** | Experimento E1: 20 `REVERSION_ATR` de ES sobre Dukascopy 5m/15m vs Yahoo 4h — separa familia mala / dataset contaminado / bug de coste. **Único proceso pesado; vía puerta de admisión** | B01, A08 (5.18.0) |
| **B03 Runner E2** | Campaña ES 5m/15m, 6 familias completas, telemetría con cobertura (D2) | B02, A11 |
| **B04 Forense E1/E2** (refutador) | Leer telemetría y refutar la lectura del ORQ | B02/B03 |
| **B05 Parser .sqx piloto (W3.3)** | 20 de las 2.035 → AST → registro de gates; coste medido | A06 |
| **B06 SQX config (I1→W3.2)** | Config del Builder corregida (fusible MC, MinTradesInRun, fitness con proxy del criterio 1.1); Build de prueba **antes del 5-sep** | licencia (ventana Emilio) |
| **B07 `services/improvement/` esqueleto (W3.5.b)** | Frontera limpia (solo `contracts/` + registro); test de sustitución nº2 | A06 |
| **B08 `services/meta/` nacimiento (W6.0, D8/D9)** | Desde `meta_strategy_pipeline` + `meta_ensemble_service`; HRP + mín-varianza del examen; correlación honesta con solape (W4.5) | A06 |
| **B09 Catálogo firmas v2 (W4.8/W4.9, D6)** | `PROP_FIRM_CATALOG` con `SourceRef`, test valor≠None ⇒ fuente verificada; endpoint API | I4 |
| **B10 Web `/prop-firms` (W5.8, D7)** | Consume el catálogo v2; cupones fuera; `.env.local` con claves de Emilio | B09, ventana |
| **B11 Consolidación resto símbolos (W1.2/W1.3)** | GC/SI/CL/forex al llegar; correlación proxy↔CME ≥0,90 o NO APTO | A05 |
| **B12 Vigía V0 (W7)** | Unit systemd read-only + informe diario a `results/vigia/`; lo instala el ORQ por ssh tras la limpieza | limpieza VPS (ventana) |

## 5. VENTANA EMILIO (vigente, una sola; el resto NO le toca)

1. **Autorizar la limpieza del VPS** ("autorizado limpiar el VPS", opción A) o pegar los comandos
   de la opción B de `VENTANA_EMILIO.md`. Sin esto, 7,5 M de frenazos siguen creciendo.
2. **Licencia StrategyQuant X antes del 2026-09-05** (trial en el PC): comprar/transferir el seat
   del VPS al PC. Sin ella, M1 (Generación) muere el día 5.
3. **Claves Firebase** en `apps/web/.env.local` (no existe; `firebase.ts` mezcla dos proyectos).
4. **Pregunta 5.2 de I3** (router dinámico de meta vs asignación estática D9).
5. Confirmar que la rama de devilray se integra a `main` por fast-forward (el ORQ lo hace).

## 6. Integración y ritmo del orquestador

- Cada aterrizaje: `aceptar_agy.py` → auditoría propia → veredicto (`ACEPTA` / `REPITE` con causa)
  → `git merge --no-ff agy/<ID>` en devilray **solo con ORQ_COMMIT=1** → commit temático → al
  cerrar la ola, `main` ← devilray (ff) y `ORQ_PUSH=1 git push` (autorizado desde 2026-08-31).
- Checkpoint en `current_phase.md` por ola; decisiones nuevas numeradas (D11…).
- Si un experimento (E1/E2) contradice el plan, **manda la evidencia**: se actualiza
  `PLAN_LOCAL_FONDEO.md` y este fichero en el mismo commit.

## 7. Definición de hecho del ciclo 3

1. Arnés activo y probado (A01/A02 verdes). 2. Motor 5.18.0 con baseline nuevo. 3. Registro de
gates v1 con paridad y test de sustitución. 4. E1 y E2 ejecutadas con telemetría completa y
veredicto data-vs-edge **legítimo** por celda. 5. `/estrategias` reescrita y build verde.
6. `services/improvement/` y `services/meta/` nacidos en frontera limpia. 7. VPS liberado y vigía
V0 informando. 8. Marcador honesto publicado (aunque siga en 0).
