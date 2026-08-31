# PLAN MAESTRO — v3 (2026-08-31) — "EL MOTOR PRIMERO"

> **Sustituye** a `archive/plan_maestro_2026-08-31_v2_auditoria_auth.md` (v2 quedó limitado a
> auditoría+saneamiento; el usuario ha sellado las 20 decisiones que faltaban y la prioridad
> declarada es **generar estrategias**, no infraestructura).
> **Origen:** sesión de 20 preguntas Hermes→Usuario del 2026-08-31. Todas las respuestas están
> selladas en `DOCTRINA_ORQUESTADOR.md §14`. **Ninguna fase puede contradecirlas.**

Doctrina transversal invariante: REAL-ONLY / ZERO-MOCKS · cero datos inventados · cero fallbacks
complacientes (`NO DATA`/`ERROR`, nunca un valor por defecto) · **sin `git commit`/`git push`
automático** · **nunca `rm`** (todo a `cuarentena/`) · toda población valiosa se persiste a disco+DB
inmediatamente, jamás vive solo en RAM.

**Autonomía vigente (decisión #20):** el Orquestador auto-despacha TODAS las fases hasta completar
el plan, sin pedir GO al usuario. El usuario conserva veto y puede parar en cualquier momento.

---

## MAPA DE BLOQUES

| Bloque | Fases | Qué entrega | Prioridad |
| :--- | :--- | :--- | :--- |
| **A. Saneamiento** | 0, 1 | Veredicto de auditoría + repo gobernable | INMEDIATA (decisión #18) |
| **B. Datos $0** | 2 | Matriz completa 1m–4h en TODOS los activos, coste 0 € | INMEDIATA (desbloquea todo) |
| **C. Descubrimiento** | 3, 4 | Campaña SQX masiva gobernada en 4 cores | **PRIORITARIA (el objetivo)** |
| **D. Optimización** | 5, 6 | Killzones + noticias aplicadas como capa posterior | PRIORITARIA |
| **E. ULTRA** | 7 | Motor de balas piramidal, 500x dinámico, 70/80% DD | PRIORITARIA |
| **F. FONDEO** | 8 | Optimizador de paso de examen 3–8 días | PRIORITARIA |
| **G. Meta / Router** | 9 | Router IA multi-activo con debate, sin hardcodeo | ALTA |
| **H. Paper** | 10 | Despliegue 100% demo con telemetría real | MEDIA |
| **I. Web** | 11 | Páginas maestras jerárquicas + Firebase | SECUNDARIA |

---

# BLOQUE A — SANEAMIENTO

## Fase 0 — Auditoría del changeset 258-archivos + inventario de deuda

- **Objetivo:** verificar que `git diff 23c8733a9..245009fef` (5 commits, 258 archivos, +28.748
  líneas: Firebase Auth + RTDB + ~25 scripts `mine_and_certify_*` + cambios en
  `event_backtest_engine.py`, `gate_09_novelty_antifit.py`, `discovery_validation_pipeline.py`,
  `strategy_search_registry.py`) **no violó REAL-ONLY ni relajó ningún gate**.
- **Criterio de éxito verificable:**
  - [ ] Cada uno de los ~25 scripts `mine_and_certify_*` revisado: cero `random`/`seed`/datos
        sintéticos tratados como reales.
  - [ ] Diff línea a línea de los 4 ficheros de motor: ¿cambia el umbral de aprobación de algún
        gate? Documentar **dirección** (más estricto / más laxo) con cita de línea.
  - [ ] `pytest tests/ -q` → 0 errores de colección; adjuntar salida cruda.
  - [ ] Listado de toda estrategia certificada entre 2026-08-30 y hoy: `strategy_id` + SHA-256 +
        fecha + los 11 `EvidenceRecord` en `data/evidence/<sid>/gate_*.json` (o `NO_EVIDENCE`).
  - [ ] Veredicto explícito: `LIMPIO` | `VIOLACIÓN DETECTADA` (detallar) | `NO_EVIDENCE`.
- **Reglas:** SOLO LECTURA. Prohibido modificar estos archivos en esta fase.
- **Estado:** ASIGNADA — se despacha inmediatamente.

## Fase 1 — Consolidación de código residual y estructura

- **Objetivo:** el repo tiene 67 scripts sueltos (25 de ellos variantes de `mine_and_certify_*`),
  33 páginas web y ~20 `.md` en `docs/` raíz. Reducir a una superficie gobernable **sin borrar**.
- **Criterio de éxito verificable:**
  - [ ] **Un único CLI de minería** `scripts/mine.py` con parámetros `--track {ultra,fondeo}
        --symbol --tf --profile`, que absorbe la funcionalidad real de los 25 scripts.
        Los 25 originales se mueven a `cuarentena/scripts_legacy_mining/` con manifiesto SHA-256.
  - [ ] `git mv` de los `.md` SUPERSEDED restantes a `docs/archive/` según SSOT §6. Cero borrados.
  - [ ] `.agents/informe&seguimiento/` con veredicto cerrado → `historico/`.
  - [ ] `docs/00_MASTER_IDEAS_Y_PLAN.md` §5 actualizado con las 20 decisiones selladas.
- **Dependencias:** Fase 0 (para no consolidar encima de código que viole la doctrina).

---

# BLOQUE B — DATOS A COSTE 0 €

## Fase 2 — Ingesta Dukascopy (proxies CME) + ampliación M1 cripto

- **Hallazgo verificado por el Orquestador (2026-08-31, curl real):** el datafeed público de
  Dukascopy sirve **ticks bid/ask reales, sin API key y sin coste**, en
  `https://datafeed.dukascopy.com/datafeed/{SYM}/{YYYY}/{MM0}/{DD}/{HH}h_ticks.bi5`
  (**`MM0` es el mes 0-indexado**: `06` = julio). Formato: LZMA → registros de 20 bytes
  `>3I2f` = (ms desde la hora, ask×10^k, bid×10^k, askVol, bidVol).
  Prueba física: `USA500IDXUSD 2026-07-15 14h` → 12.455 ticks, ask 7570.748 / bid 7570.226.
  Profundidad ≥ 2015 en índices y oro.
- **Mapa de proxies canónico (decisión #13):**

  | CME real | Proxy Dukascopy $0 | Uso |
  | :--- | :--- | :--- |
  | ES / MES | `USA500IDXUSD` | descubrimiento + optimización |
  | NQ / MNQ | `USATECHIDXUSD` | descubrimiento + optimización |
  | YM / MYM | `USA30IDXUSD` | descubrimiento + optimización |
  | GC / MGC | `XAUUSD` | descubrimiento + optimización |
  | SI | `XAGUSD` | descubrimiento + optimización |
  | CL / MCL | `LIGHTCMDUSD` | descubrimiento + optimización |
  | RTY / M2K | `USARUSSIDXUSD` (verificar disponibilidad antes de usar) | descubrimiento |
  | FX majors | `EURUSD`, `GBPUSD`, `USDJPY`, `USDCHF`, `USDCAD`, `AUDUSD` | descubrimiento |

- **Criterio de éxito verificable:**
  - [ ] `services/data-ingestion/dukascopy_feed.py` real: descarga por hora, reintentos, atómico
        (`.part`→rename), caché en disco, reanudable, **cero invención** (hora sin ticks = fichero
        de 0 bytes = se registra como hueco, NO se rellena).
  - [ ] Agregador tick→OHLCV en `1m, 5m, 15m, 1h, 4h` con manifiesto SHA-256 por celda.
  - [ ] **Aviso obligatorio registrado en el manifiesto:** el volumen de Dukascopy es **volumen
        de tick del broker**, no volumen del contrato CME (verificado: 100 % de barras con volumen
        > 0 en `USA500IDXUSD`). Toda estrategia que dependa fuerte del volumen se marca
        `VOLUMEN_PROXY` y su portabilidad se decide con el control proxy↔CME.
  - [ ] Import a SQX con naming canónico `<SYM>_<TF>`; conteo final de celdas ≥ **110**
        (9 cripto×5 + 7 proxies×5 + 6 FX×5 = 45+35+30).
  - [ ] Backfill M1 cripto (Binance Vision, ya en curso) completado e importado.
  - [ ] Registro de divergencia proxy↔CME: correlación y spread medio proxy vs. la muestra real
        de CME ya importada (2–3 meses M5), documentado. Si la correlación < 0.98 en algún par,
        se marca y se avisa al usuario — no se oculta.
- **Dependencias:** ninguna. **Puede correr en paralelo a la Fase 0.**

---

# BLOQUE C — DESCUBRIMIENTO (el núcleo)

## Fase 3 — Cola de minería gobernada para 4 cores

- **Objetivo (decisión #14):** el VPS es de 4 cores / 23 GB. Sin planificador, una campaña de 110
  celdas satura la máquina y tumba la API y la web. Construir el planificador.
- **Criterio de éxito verificable:**
  - [ ] `services/discovery/mining_queue.py`: cola persistente (SQLite) de celdas, con
        `max_concurrent` configurable (arranque: 2), `nice`/`ionice`, presupuesto de CPU,
        y **reanudación tras reinicio** (el estado vive en disco, no en RAM).
  - [ ] Persistencia inmediata: cada generación de SQX se exporta a CSV + upsert en
        `ultrarentable.sqlite3` **antes** de pasar a la siguiente celda. Nada muere en RAM.
  - [ ] Dos perfiles de generación en SQX, con sus ficheros de configuración reales:
        - **ULTRA:** función de fitness orientada a asimetría (payoff ≥ 3R, cola derecha,
          tolerancia a DD alto), sin filtro horario todavía.
        - **FONDEO:** fitness orientado a DD realizado bajo y consistencia diaria.
  - [ ] La web (`:3005`) muestra progreso real de la cola (% por celda, celdas hechas/pendientes),
        leído de la BD — no un contador inventado.
- **Dependencias:** Fase 2 (datos) para las celdas nuevas; puede arrancar con cripto antes.

## Fase 4 — Campaña de descubrimiento masiva

- **Objetivo:** barrer las ≥110 celdas con ambos perfiles y llenar el banco de candidatas.
- **Criterio de éxito verificable:**
  - [ ] ≥ 110 celdas ejecutadas con evidencia por celda (log SQX + CSV + filas en BD).
  - [ ] Banco de candidatas con `strategy_id`, SHA-256, celda de origen, métricas crudas de SQX.
  - [ ] **Ninguna candidata se declara "certificada" en esta fase.** Aquí solo se descubre.
        La certificación son los 11 gates, y llega después de la capa de optimización.
- **Nota de honestidad obligatoria:** el criterio ULTRA de **≥100 % mensual (decisión #5)** NO se
  exige aquí. SQX rara vez lo alcanza de forma nativa; el objetivo de esta fase es materia prima.
  El 100 %/mes se persigue en las Fases 5 y 7 (killzones + envolvente de balas piramidal).

---

# BLOQUE D — CAPA DE OPTIMIZACIÓN POSTERIOR (decisión #1: NO en la generación)

## Fase 5 — Killzone Optimizer

- **Objetivo:** para cada candidata cruda, encontrar la máscara horaria que maximiza su
  rentabilidad, aplicada **como capa posterior**, nunca dentro de la generación inicial.
- **Sesiones canónicas (decisión #2, hora de Nueva York):**

  | Killzone | Ventana ET | Notas |
  | :--- | :--- | :--- |
  | Asia | 19:00 – 04:00 | rango, baja volatilidad |
  | Londres | 03:00 – 06:00 | apertura europea |
  | **NY AM** | **08:00 – 11:00** | **principal (mandato del usuario)** |
  | **NY PM** | **13:30 – 16:00** | **principal (mandato del usuario)** |
  | Overlap LDN/NY | 08:00 – 11:00 | máxima liquidez |

- **Criterio de éxito verificable:**
  - [ ] `services/optimization/killzone_optimizer.py`: barrido exhaustivo de las ventanas y sus
        combinaciones sobre el **backtest canónico determinista** (mismo motor de siempre, no uno nuevo).
  - [ ] Salida por candidata: variante con máscara óptima + delta de métricas antes/después +
        evidencia SHA-256. Si ninguna máscara mejora, se registra `SIN MEJORA` (no se fuerza).
  - [ ] Control anti-overfit: la máscara se elige en IS/Validation y se confirma en
        **blind-holdout**. Una máscara que solo funciona en IS se rechaza y se documenta.
  - [ ] Re-evaluación por los **11 Evidence Gates** de las variantes con máscara → aquí sí nace
        la certificación.

## Fase 6 — Filtro de noticias (secundario, decisión #3)

- **Objetivo:** ventanas de blackout por eventos de alto impacto, fuente gratuita/scraping.
- **Criterio de éxito verificable:**
  - [ ] Ingesta de calendario económico gratuito con caché en disco y **degradación honesta**:
        si la fuente cae, el sistema reporta `NO DATA` y **no opera a ciegas asumiendo "sin noticias"**.
  - [ ] Blackout configurable (±N minutos) aplicado en re-evaluación, con delta de métricas.
  - [ ] Persistencia del calendario en BD (histórico) para que los backtests sean reproducibles.
- **Prioridad:** se ejecuta **después** de la Fase 5 y no bloquea las Fases 7–8.

---

# BLOQUE E — ULTRA

## Fase 7 — Motor de balas hiper-piramidal

- **Parámetros sellados (decisiones #6, #7, #8, #9):**
  - DD realizado **70 %** · DD flotante **80 %** (deroga el 75 % de la doctrina anterior).
  - Apalancamiento nominal **hasta 500x** en BingX, **gestionado dinámicamente por IA**.
  - Dimensionamiento **100 % en porcentajes**, agnóstico al capital nominal. Cero cifras absolutas.
  - Arranque **100 % paper/demo**.
- **Criterio de éxito verificable:**
  - [ ] Envolvente de balas sobre las estrategias base: estados INICIO → CONFIRMACIÓN →
        CRECIMIENTO → COSECHA → PROTECCIÓN → CIERRE, todo en %.
  - [ ] Piramidación free-risk (BE tras +1.5R), reciclaje de balas, autoinversión de margen flotante.
  - [ ] Bóveda ratchet (50–85 % del beneficio cosechado, intocable).
  - [ ] Gestor dinámico de apalancamiento: decide el multiplicador por operación según régimen,
        volatilidad y estado de la bala; **cap duro por el máximo real que dé BingX en ese par**
        (se consulta a la API real, no se asume 500x en todos).
  - [ ] Backtest de la envolvente sobre las candidatas de Fase 5: reportar cuántas alcanzan
        **≥100 %/mes** con las restricciones 70/80 %. **Si ninguna lo alcanza, se reporta el número
        real. Prohibido ajustar el backtest para que salga el número deseado.**

---

# BLOQUE F — FONDEO

## Fase 8 — Optimizador de paso de examen (3–8 días)

- **Decisión #10:** la gestión de cuentas/prop firms queda **pospuesta**. Esta fase produce
  estrategias, no administra cuentas.
- **Decisión #11:** optimización agresiva y fluida para superar fases en **3 a 8 días**.
- **Decisión #12:** la ejecución irá por **PickMyTrade + Tradovate** (ya configurado), en espera.
- **Criterio de éxito verificable:**
  - [ ] Simulador de reglas prop real: trailing DD (intradiario y EOD), pérdida diaria, regla de
        consistencia, cierre obligatorio intradía.
  - [ ] Optimizador que maximiza `P(pasar en ≤8 días)` sujeto a `P(violación) < umbral`, con la
        distribución obtenida por Monte Carlo **sobre trades reales del backtest** (remuestreo de
        operaciones reales, nunca retornos sintéticos).
  - [ ] Salida: ranking de estrategias/meta con días esperados hasta pasar y prob. de quiebre.
  - [ ] Export listo para PickMyTrade/Tradovate (formato verificado contra su documentación real).

---

# BLOQUE G — META-ESTRATEGIAS

## Fase 9 — Router inteligente con debate IA (decisión #4)

- **Objetivo:** que un conjunto de estrategias funcione **como una sola**, con router dinámico
  multi-activo y debate IA, **sin hardcodear reglas**.
- **Criterio de éxito verificable:**
  - [ ] Router que decide asignación por ventana temporal a partir de: régimen detectado,
        killzone activa, correlación viva entre estrategias y estado de cada bala.
  - [ ] Capa de debate IA: varios agentes proponen asignación y se critican entre sí; la decisión
        y **el razonamiento completo quedan persistidos** en BD (auditable a posteriori).
  - [ ] Backtest del router **como estrategia única**: su curva debe batir a la media de sus
        componentes en winrate y DD, o se declara fracaso explícito.
  - [ ] Salvaguarda: el router nunca puede saltarse los límites 70 %/80 % ni las reglas de FONDEO.

---

# BLOQUE H — PAPER TRADING

## Fase 10 — Despliegue 100 % demo (decisión #9)

- [ ] ULTRA en paper/demo BingX con el motor de balas real.
- [ ] FONDEO en demo Tradovate vía PickMyTrade.
- [ ] Telemetría real a la web: posiciones, balas activas, DD flotante/realizado en vivo.
- [ ] **Ni un euro real hasta que el usuario lo autorice explícitamente.**

---

# BLOQUE I — WEB (secundaria)

## Fase 11 — Consolidación web + Firebase

- **Decisión #15:** Firebase se mantiene temporalmente en el proyecto PECEMI; la migración a
  proyecto dedicado se hará **solo si se ejecuta de forma inmediata**. Mientras tanto, se elimina
  igualmente el `apiKey` hardcodeado (debe venir de entorno, fallo explícito si falta).
- **Decisión #16:** consolidar las 33 páginas actuales en **páginas maestras con subpáginas
  jerarquizadas**, no en 33 rutas planas.
- **Decisión #17:** el **trading desk queda pospuesto** hasta después de entregar el motor.
- Landing sin autenticar + acceso solo para usuarios autorizados por el superadmin
  `josferestudio@gmail.com`. Dominio: https://ultrafondeo.web.app/

---

## REGLAS TRANSVERSALES DEL LOOP

1. **Auto-despacho autorizado (decisión #20):** el Orquestador publica `current_phase.md` + `GO`
   sin esperar al usuario, audita el `DONE` y encadena la siguiente fase.
2. **Cadencia de sincronización: 5 minutos (decisión #19).**
3. Cualquier trabajo de Antigravity fuera del loop se audita antes de darlo por bueno.
4. 2–3 veredictos `repite` seguidos sobre la misma fase ⇒ `needs_user_input` automático.
5. Sin `git commit`/`git push` automático. Sin `rm`. Cero datos inventados.
6. **Antigravity tiende a ir rápido e inventarse lo que no sabe.** Por eso cada criterio de éxito
   de este plan es **verificable con un comando físico** y el Orquestador lo re-ejecuta por su
   cuenta. Un informe sin evidencia cruda reproducible = veredicto `repite`, sin excepción.
