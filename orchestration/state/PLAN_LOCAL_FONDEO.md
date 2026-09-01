# PLAN LOCAL FONDEO — plan de ejecución detallado (2026-09-01)

> **Objetivo único**: (1) estrategias FONDEO certificadas bajo criterio 1.1, (2) META-FONDEO
> ensamblada y examinada honestamente, (3) la página `/estrategias` arreglada según
> `docs/18_STRATEGIES_PAGE_SPEC.md`. **ULTRA/META-ULTRA: EN CONSTRUCCIÓN, aparcado.**
> Ejecuta: el ORQUESTADOR local (Opus 5) según `DOCTRINA_ORQUESTADOR_LOCAL.md`, con el loop
> no bloqueante. Este documento mapea sobre los bloques F00-F09 sin sustituirlos: cuando un
> carril cierra algo de un bloque, se actualiza el bloque (esa sigue siendo la fuente de verdad
> por fase).
>
> Objetivo sellado de F07 que gobierna todo: **≥20 % mensual SOSTENIBLE (mediana), P(romper
> cuenta) ≤20 % a 6 meses, examen superado en 3-8 días.** Sin maquillar jamás la cifra real.

Dueños: `ORQ` = orquestador en persona · `SUB` = subagente con contrato · `NOHUP` = proceso
largo supervisado · `SSH` = orquestador operando el VPS · `[E]` = requiere ventana Emilio.

> **Columna vertebral: la arquitectura modular M1-M4** (`ARQUITECTURA_MODULAR_ESTRATEGIAS.md`):
> M1 Generación (Strategy One/SQX) · M2 Mejora (loop iterativo con revisión) · M3 Valoración
> para fondeo (firmas, horarios, examen honesto) · M4 Metaestrategias. Cada carril de abajo
> sirve a un módulo (W3→M1/M2, W4+W6→M3/M4, W5→la web de los cuatro con la estética de
> `docs/19_UI_STYLE_SPEC.md`), y ningún módulo se sella sin su expediente de investigación.

---

## W0 — ARRANQUE LOCAL (Día 0; bloquea todo lo demás)

| id | Tarea | Dueño | Verificación |
| :-- | :--- | :-- | :--- |
| W0.1 | WSL2 + `.venv` desde `uv.lock`; Node para la web | SUB | `python -c "import services"`, `npm --version` |
| W0.2 | ✅ **HECHO 2026-09-01** — Identidad del motor en el PC | ORQ | **15/15 IDÉNTICAS**, comparando también la huella SHA-256 del ledger de cada celda. Evidencia: `results/verificacion_f02_5.17.0_EJECUCION_PC_2026-09-01.json` vs el baseline sellado. **Minar en el PC es legítimo desde ahora** |
| W0.3 | ssh PC→VPS con clave | ORQ `[E]` una vez | `ssh ubuntu@vps 'echo ok'` |
| W0.4 | Traer datasets ya descargados del VPS (ES 1m/5m/15m consolidados, NQ parcial, cripto profundo si cabe) | NOHUP | hash de cada fichero == manifiesto |
| W0.5 | BD de trabajo local inicializada + `cola_mineria.py estado` | SUB | comando responde; 0 jobs |
| W0.6 | Ventana sudo VPS: sección A de `OPERACION_VPS.md` + optimización corregida + backup `/tmp` | SSH `[E]` | `free -h` con swap liberándose; `memory.events` sin crecer; servicios apagados |
| W0.7 | `git push origin main` desde el PC (reconciliar con `origin/tmp-sync`) | ORQ | `git ls-remote` == HEAD local; tmp-sync intacto hasta verificar |
| **W0.8** | **La puerta de admisión no existe en el PC.** `services/ops/gobernanza_recursos.py` importa `fcntl` (solo Unix) ⇒ `ModuleNotFoundError` en Windows. El plan asumía WSL2 y **en este PC no hay ninguna distro instalada**; el entorno real es Windows nativo (que por lo demás funciona: `.venv` 3.11.8, identidad 15/15). Hasta que se porte (candado por fichero `msvcrt.locking` o `portalocker`, y lectura de recursos vía `psutil` en vez de `/proc`), **el turno único y la admisión los gobierna el orquestador a mano**: máximo 1 campaña + 1 backfill, concurrencia = núcleos − 2 | SUB | `python -m services.ops.gobernanza_recursos estado` responde en Windows |

**Mientras corren W0.4/W0.6**, el ORQ ya trabaja su cola: redactar contratos de W1-W5, diseñar
la página (W5), y el forense de la última telemetría.

## W1 — DATOS FONDEO (Día 0 → continuo; NOHUP en el PC)

| id | Tarea | Dueño | Verificación |
| :-- | :--- | :-- | :--- |
| W1.1 | Backfill Dukascopy 2023→hoy de lo que falta: completar `USATECHIDXUSD` (NQ), `USA30IDXUSD` (YM), `XAUUSD` (GC), `XAGUSD` (SI), `LIGHTCMDUSD` (CL) + 6 majors forex, `--concurrency 3` | NOHUP | `dukascopy_backfill_progress.json` trimestres completos por símbolo |
| W1.2 | Consolidar 5m/15m por símbolo al terminar (`consolidar_dukascopy.py`), manifiesto SHA-256, huecos clasificados por calendario de sesión (patrón del inventario del 01-09) | SUB | bar_count reproducible dígito a dígito; anómalos = festivos |
| W1.3 | Control divergencia proxy↔CME por símbolo nuevo (patrón ES: correlación retornos, peor subperiodo) usando la muestra Yahoo como control | SUB | correlación ≥0,90; si no ⇒ el símbolo se marca NO APTO y se reporta |
| W1.4 | Reparar tabla `datasets` de la BD (filas Dukascopy corruptas, alias duplicados) — F03.1(b) | SUB | conteo BD == conteo disco; 0 filas `record_count=0 APPROVED` |
| W1.5 | RTY: sin proxy Dukascopy (confirmado). Se declara fuera del universo salvo dato de pago | ORQ | decisión escrita; NO se compra dato sin `[E]` |
| **W1.6** | **El "checksum" de los manifiestos nuevos no valida el contenido.** `services/data/market_ingestor.py:104` calcula el sello sobre METADATOS (`venue:symbol:interval:n_barras:start:end`), no sobre los bytes: un dataset con las mismas velas contadas pero precios corruptos pasa la custodia. Los manifiestos canónicos antiguos SÍ llevan hash de contenido (verificado 5/5), y `api/routes.py:168` compara contenido ⇒ **hay dos criterios conviviendo**. Unificar sobre hash de CONTENIDO y re-sellar lo ingerido por la vía mala | SUB | test: alterar un precio de un dataset y comprobar que el checksum cambia y la custodia lo rechaza |

| **W1.7** | **El backfill no es idempotente y DEGRADA datos versionados** (defecto hallado el 01-09 a las 21:10): `services/data_ingestion/run_dukascopy_backfill.py` re-descarga trimestres que ya existen con manifiesto y los sobrescribe sin comparar, aceptando `hours_failed>0`. Resultado medido: 20 chunks de ES y NQ (2023 Q1-Q2, 5 TF) pasaron de 17.010 barras / 0 horas fallidas a 16.986 / 2, y de 1 a 4 fallos en ES. Rescatados 20/20 desde el VPS con hash idéntico al de HEAD; los degradados en `data/quarantine/backfill_degradado_20260901/`. Arreglo: saltar chunk si existe manifiesto con hash de contenido válido; escribir a temporal y sustituir SOLO si `hours_failed` no empeora y `bar_count` no baja; reintentar horas fallidas antes de sellar; `--force` explícito para regenerar | SUB | test: chunk existente + descarga peor ⇒ el fichero en disco no cambia y el log lo dice |
| **W1.8** | **Rescate desde el VPS en vez de 40 h de backfill**: el VPS tiene `USA30IDXUSD` (YM) y `USATECHIDXUSD` (NQ) completos 2023-01→2026-08 en 5 TF (268 + 267 MB) y `XAUUSD` 1 trimestre, con manifiestos de hash de contenido (muestra verificada). Sincronización `tar` por ssh con `nice 19` lanzada el 01-09 21:30 (`results/setup/orq_sync_vps_datasets_20260901.log`); verificación hash a hash al terminar. El backfill queda SOLO para lo que el VPS no tiene (XAG, CL, forex) y **no se relanza hasta W1.7** | ORQ | log con `OK=n BAD=0`; consolidar 5m/15m de YM y NQ (W1.2) después |

Regla: **ninguna celda entra en campaña sin consolidado + manifiesto + W1.3 aprobado.**

## W2 — CAMPAÑA DE DESCUBRIMIENTO FONDEO (arranca con ES ya en Día 0-1)

| id | Tarea | Dueño | Verificación |
| :-- | :--- | :-- | :--- |
| W2.1 | Campaña ES 5m + 15m, perfiles `arquetipos` (ORB/VWAP_REVERSION 5.17.0) y `amplio`, `--dataset-source dukascopy` SIEMPRE explícito | NOHUP (lanza ORQ) | telemetría completa por job en `results/telemetria/`; 0 celdas con dataset `ds_trad_*` (Yahoo) |
| W2.2 | Supervisión de campaña: heartbeat de la cola, lectura de telemetría según cae | SUB | cada celda con veredicto data-vs-edge anotado |
| W2.3 | Extender a NQ/YM/GC/SI/CL + forex según W1 entregue celdas aptas | NOHUP | ídem W2.1 |
| W2.4 | Censo criterio 1.1 tras cada tanda (`scripts/censo_f01.py`), sin relajar nada | ORQ | informe en `results/`; near-misses etiquetados para W3 |
| W2.5 | 4h de Yahoo PROHIBIDO (remuestreo contaminado); 4h solo desde consolidación Dukascopy propia | — | grep de datasets usados en telemetría |

| W2.6 | **Telemetría con cobertura declarada**: el embudo debe persistir `max_candidates`, `espacio_total`, `truncado` y el histograma de familias evaluadas/muertas | SUB | los campos aparecen en el JSON; test unitario del constructor de telemetría |

> ### ⚠ CORRECCIÓN DEL 2026-09-01 (ciclo 1) — por qué cambian las reglas de abajo
>
> Medido por el orquestador (`reviews/forense_telemetria_2026-09-01.md`): `mine.py` trunca el
> espacio de búsqueda **por PREFIJO** (`search_space[:max_candidates]`) y `--max-candidates` vale
> **20 por defecto**. Como el perfil `arquetipos` emite primero las 108 configuraciones de
> `REVERSION_ATR`, **toda campaña por defecto prueba UNA familia de seis** y su telemetría no lo
> dice. La única telemetría persistida (ES 4h) cubría el **4,8 % del espacio, 1 de 6 familias**.
>
> - **D1** — La regla de "familia agotada" **queda SUSPENDIDA** hasta que W2.6 esté hecho. Con un
>   embudo truncado por prefijo, esa regla abandonaría una celda habiendo probado una sexta parte.
> - **D2** — Toda campaña se lanza con `--max-candidates 0` (espacio completo) o con muestreo
>   **estratificado por familia**. Nunca con el valor por defecto.

**Reglas de decisión PRE-SELLADAS** (el ORQ decide solo, sin esperar a Emilio):

- ~~Celda con ≥80 % de muertes IS por `sin_ventaja` (con ≥50k barras) ⇒ familia agotada~~
  **SUSPENDIDA por D1.** Redacción vigente: una celda solo puede declararse agotada cuando el
  embudo demuestre que **las 6 familias** estuvieron representadas y ≥80 % murió por
  `sin_ventaja`. Mientras W2.6 no exista, ninguna celda se declara agotada.
- Celda con ≥50 % `pocas_operaciones` ⇒ falta frecuencia/datos: se revisa arquetipo de sesión o
  se amplía histórico (W1), no el espacio de parámetros.
- Dos celdas consecutivas de un símbolo con embudo completo `{'IS': N}` y PF máximo <0,9 ⇒ las
  demás TF de ese símbolo bajan de prioridad (se registra, no se borra).
- Aparece un near-miss (≥7/11 gates o PF OOS ≥1,25 con <200 ops) ⇒ alta inmediata en la lista
  de semillas de W3/F04.
- **Nunca** se toca un umbral del criterio 1.1. Si todo da 0, el plan sigue por W3 y se reporta.

## W3 — EDGE NUEVO (el carril de verdad difícil; empieza Día 1 en paralelo)

| id | Tarea | Dueño | Verificación |
| :-- | :--- | :-- | :--- |
| W3.1 | SQX en el PC: instalar, importar datasets FONDEO con naming `<SYM>_<TF>` `[E si licencia]` | SUB+ORQ | `-databank action=list` responde en local |
| W3.2 | **Arreglar la config del Builder** (la esterilidad documentada en `estrategias_um`): fusible MC vs `MinTradesInRun>20` × `MaxTradesPerDay=1` incompatibles; bancos con nombre direccionable; persistencia a disco de databanks | ORQ (diseño) + SUB | un Build de prueba con aceptación >0 % y banco en disco |
| W3.3 | Parser carril SQX: `data/sqx_exports/toimprove_2026-08-31.csv` (2.035) + .sqx → AST canónico → validación motor propio 11 gates. **Piloto: 20 estrategias**, medir, luego escalar | SUB (piloto) → NOHUP (escala) | 20/20 con veredicto honesto (aunque sea 0 aptas); coste por estrategia medido |
| W3.4 | Nuevas familias de arquetipos FONDEO si W2 dicta "sin_ventaja" (diseño ORQ estilo `reviews/diseno_arquetipos_5_17_0.md`; implementación SUB; regla #26 + gate 9 con sus DoF ANTES de campaña) | ORQ+SUB | identidad 15/15; smoke con trades; DoF registrados |
| W3.5 | F04 mejora inteligente sobre near-misses reales: hipótesis semántica → experimento parametrizado → blind holdout + DSR + walk-forward. `SIN MEJORA` es un resultado válido | ORQ+SUB | ninguna mejora aceptada sin holdout intacto |
| W3.5.b | **Base verificada para `services/improvement/` (I2, 01-09)**: `deep_strategy_improver.py` fabricaba métricas (×1,30, `CERTIFIED_PASS` forzado) ⇒ **en cuarentena** (`cuarentena/fabricador_metricas_20260901/`). Reutilizables: `factory/optimizer.py` (Optuna real, 0 llamadores), `factory/optimization_loop.py` (bucle genérico, hoy cableado al `FastEngine` no canónico), `optimization/quantitative_arsenal.py` (régimen honesto). NO reutilizable: `expert_refinement_loop.py` (lee el blind OOS dentro del bucle y pasa `trials_tested=iteration`). El contrato de entrada de M2 exige `trials_tested_upstream` y lo suma antes de Gate 8 | SUB | test: near-miss de 420 configs + 3 iteraciones ⇒ Gate 8 recibe 423 |

## W4 — DEUDAS QUE BLOQUEAN CERTIFICAR (Día 0-2, SUB en paralelo; TODAS antes de la primera certificación)

| id | Tarea | Verificación |
| :-- | :--- | :--- |
| W4.1 | `fondeo_examen`: que la decisión/ranking use `reejecutar_examen_barra_a_barra()` (equity flotante), no el bootstrap optimista. Fail-closed si no puede | test: caso con `prop_firm_busted=True` jamás imprime CUMPLE |
| W4.2 | Eliminar hardcode `engine_version 5.4.0` (meta_ensemble, meta_strategy_pipeline, fast_engine_adapter, funding/strategy_research_loop, excel_master_catalog) → leer `services/engine_version.py`; quitar `except Exception: pass` mudos | grep sin '5.4.0' hardcodeado; error explícito en fallo |
| W4.3 | Cerrar F00.1 según la auditoría del 31-08 (dos suites de gates AMBAS vivas): designar canónica la que certifica, adaptar/cuarentenar la otra, un solo umbral por gate | `grep -rn "from services.*validation"` coherente; la web muestra el mismo veredicto que certifica |
| W4.4 | Bug `gates_passed=0`: los 3 escritores (`mine.py`, `discovery_validation_pipeline`, `legacy_revalidation_service`) escriben el conteo real | fila nueva con 11/11 refleja 11 |
| W4.5 | Meta-correlación honesta: prohibir la correlación fabricada (0,15 con ≤2 pasos) y el PF 5,0 sin perdedoras; exigir solape temporal real mínimo | test con series cortas ⇒ `NO_EVALUABLE` |
| **W4.6** | **`verificacion_f02.py` no puede destruir su propio baseline** (defecto hallado el 01-09: una ejecución sin datos sobrescribió el fichero sellado de 5.17.0 con `SIN DATOS`; recuperado por git). Añadir `--out`, negarse a sobrescribir sin `--force`, y **abortar con exit≠0 sin escribir** si alguna celda sale `SIN DATOS` | ejecutar sin datasets deja el baseline intacto (mismo `sha256`) y falla ruidosamente |

| **W4.7** | **Decisión D5 (01-09, tras W43)**: el registro de gates v1 es **paridad exacta con la suite B** (la que certifica), `VERSION=1.0.0` por gate; `contracts/gate_directory.py` se regenera desde los valores reales de B (hoy la web enseña 75 en el gate 10 y el corte real es 40; ningún gate coincide); la reconciliación con el criterio 1.1 (PF OOS ≥1,25 vive en `certification_registry`, gate 2 exige 1,10) se audita gate a gate DESPUÉS, cada cambio con bump de `VERSION` del gate y re-censo | `/gates` muestra los umbrales que certifican; diff de un cambio de umbral = 1 gate + su test |

## W5 — PÁGINA /ESTRATEGIAS + FRONT FONDEO (Día 1-3, SUB de front; el entregable visible)

| id | Tarea | Verificación |
| :-- | :--- | :--- |
| W5.0 | **Veredicto I5 (HECHO): podar y reparar, NO web de cero** — ver `reviews/investigacion_I5_web.md` | expediente cerrado |
| W5.1 | Poda: cuarentena con manifiesto de ~15 rutas fuera de misión (trading-desk, research(-lab), ejecucion, tradesfera, bifurcacion, proveedores, portfolio, robots, nautilus, backtest, strategyquant, leaderboard, campaigns, seguimiento, data) + `MotorBacktestView.tsx` (0 importadores); Sidebar = Inicio·Estrategias·Candidatos·Gates·Fondeo·Prop-firms·Plan·Sistema **+ "Ultra — EN CONSTRUCCIÓN" siempre visible al final (atenuada)**; la ruta `/ultra` se conserva con banner gris y enlace al PUNTO_GUARDADO (ULTRA presente en todo el proyecto, nunca borrado) | manifiesto SHA-256 verificado; build sin imports rotos; /ultra responde con su banner |
| W5.2 | **Reescritura in-situ de `/estrategias` como página MAESTRA de los módulos M1-M4** (de cero contra `18_STRATEGIES_PAGE_SPEC.md` + secciones Generación/Mejora/Valoración/Meta de `ARQUITECTURA_MODULAR_ESTRATEGIAS.md`, con la estética `docs/19_UI_STYLE_SPEC.md`: grises/negro/blanco, verde-rojo solo P&L): estados `EXTRACTED → STRUCTURALLY_VERIFIED → BACKTEST_VERIFIED → CERTIFIED_CURRENT`, `NO EVIDENCE` nunca 0, identidad (hash, dataset_hash, procedencia), sin venue/capital; conserva `lib/api.ts` + `verificacion.ts`. Home reescrita a panel FONDEO honesto con los mismos tokens | revisión contra ambas specs punto por punto + checklist §5 de la 19 (cero colores fuera de tokens) |
| W5.3 | `lib/prop-firms.ts` (4.307 LOC en cliente) → endpoint desde `PROP_FIRM_CATALOG` cuando I4 entregue el catálogo re-verificado; mientras, banner "datos 08-2026 sin re-verificar" | grep sin BD hardcodeada en cliente |
| W5.4 | Badge de versión dinámico (hoy miente: v5.4.0) leyendo `engine_version` real | UI == `CURRENT_ENGINE_VERSION` |
| W5.5 | `next build` de producción EN EL PC; deploy: VPS (`npm run start`) y/o export estático a Firebase Hosting `ultrafondeo` | build sin errores; página viva |
| W5.6 | `firebase.ts` sin fallbacks mezclados; claves por `.env.local` con fallo explícito `[E: pegar claves]`; login operativo | login sin watchdog de 6 s |
| W5.7 | `/plan` renderiza también este plan local (los bloques ya se leen de `state/plan/bloques/`) | página muestra estado real |

## W6 — META-FONDEO Y EXAMEN (bloqueado hasta ≥1 certificada; diseño se adelanta)

| id | Tarea | Dueño | Verificación |
| :-- | :--- | :-- | :--- |
| W6.1 | Ensamblador meta-FONDEO: candidatas certificadas, correlación por solape temporal real (W4.5), objetivo = bajar varianza del examen | SUB | rechaza pares sin solape; pesos reproducibles |
| W6.2 | Examen F07 honesto por Monte Carlo remuestreando operaciones reales: mediana, p5, p95, P(romper cuenta), días esperados | ORQ | decide la verificación barra a barra (W4.1); nada de bootstrap optimista |
| W6.3 | Ranking final: `≥20 % mensual sostenible (mediana)` + `P(ruina) ≤20 %` + `pasar en 3-8 días` | ORQ | cifra real reportada, cumpla o no |
| W6.4 | Export a PickMyTrade/Tradovate (ya configurado, decisión #12) — SOLO demo/paper | SSH `[E para real]` | primera señal en demo registrada por el vigía |

## W7 — VPS + VIGÍA HERMES (tras W0.6; detalle en `HERMES_VPS_VIGIA.md`)

V0 monitor read-only (systemd, trading.slice) → V1 ajustes en demo dentro de límites duros →
V2 real solo con autorización explícita. El vigía consume el espejo y el feed del broker; jamás
toca el descubrimiento ni la BD de trabajo.

---

## CRONOLOGÍA REALISTA (con el loop no bloqueante)

| Día | En marcha (NOHUP/SUB) | El ORQ mientras tanto |
| :-- | :--- | :--- |
| **D0** | W0 completo; W1.1 lanzado; W2.1 (ES) lanzado en cuanto W0.2+W0.4 cierran; W4.1-W4.2 despachados | Contratos, ventana Emilio única, forense telemetría previa, diseño W5.1 |
| **D1** | W1 sigue; W2 ES termina; W3.1/W3.3-piloto; W4.3-W4.5; W5.1-W5.4 | Auditar aterrizajes W4; veredicto data-vs-edge de ES 5m/15m con reglas pre-selladas |
| **D2-3** | W2.3 según lleguen símbolos; W3.2 SQX Build de prueba; W5.5-W5.7 | QA adversarial de la página contra la spec; diseño W3.4 si telemetría lo pide |
| **D4-7** | Campañas resto de universo; W3.3 a escala; SQX Build nocturno en PC | Censos 1.1; primer informe honesto de la semana; preparar W6 |
| **>D7** | Lo que dicte la evidencia: más familias (W3.4), F04 sobre near-misses, o W6 si hay certificadas | Examen F07, meta, vigía V1 |

**El marcador se mueve cuando lo diga el censo, no el calendario.** Si a D7 sigue en 0
certificadas, el informe dirá exactamente por qué celda a celda (la telemetría ya lo permite), y
el esfuerzo se concentra en W3 — jamás en relajar el criterio.

## DEFINICIÓN DE HECHO (global)

1. ≥1 estrategia FONDEO `CERTIFIED_CURRENT` con 11/11 gates, evidencia física y motor vigente.
2. META-FONDEO ensamblada (≥2 certificadas) con examen F07 honesto y ranking publicado.
3. `/estrategias` cumpliendo la spec, sirviendo desde la API canónica, en build de producción.
4. Vigía V0 operativo en el VPS informando de la demo.
5. Todo lo anterior con evidencia en `results/` y sin una sola violación REAL-ONLY.
