# FASE ACTUAL — BALANCE 2026-09-01 (sesión FONDEO) · actualizado 10:00 UTC

> **FOCO 100 % EN FONDEO** por orden de Emilio (2026-09-01). El track ULTRA queda pausado con
> todo su estado en `orchestration/state/PUNTO_GUARDADO_ULTRA.md` — nada a medias, nada perdido.
> Objetivos de rentabilidad SELLADOS y ya verificables (ver `plan_maestro.md`):
> ULTRA ~100 %/mes y **FONDEO ≥20 % mensual SOSTENIBLE con P(romper cuenta) ≤20 % a 6 meses**,
> medidos sobre la MEDIANA de la distribución, nunca la media.


## ACTUALIZACIÓN 2026-09-01 ~10:00 — segunda tanda (30 agentes en 4 workflows)

| Qué | Evidencia |
| :--- | :--- |
| **Datos de ES desbloqueados**: 16 chunks trimestrales fusionados en un dataset único. 250.009 barras en 5m (83.377 en 15m, 1.230.396 en 1m), rango 2023-01 → 2026-08, SHA-256 reproducible, `gaps_filled=false`, huecos clasificados por **calendario de sesión**. Los 36 anómalos son festivos reales | `scripts/herramientas/consolidar_dukascopy.py` · manifiestos en `data/normalized/` |
| **200 operaciones OOS pasan a ser alcanzables**: con 50.101 barras OOS en 5m basta 1 operación cada 250 barras. Antes hacía falta 1 cada 13,7, matemáticamente imposible | `mine.py --dataset-source dukascopy --dry-run` resuelve 13.723 KB frente a 963 KB |
| **El discovery continuo llevaba >24 h sin evaluar FONDEO**: la rama por defecto exigía `"fondeo" in fname` en un `else` que sólo se alcanza cuando eso ya es falso. Todo dataset de FONDEO se evaluaba como ULTRA, con 1.000 USD de capital y 25 % de techo de drawdown en vez de 50.000 y 4,5 % | commit `1956e3816` · `orchestration/results/embudo_fondeo_forense.md` §5 |
| **El repositorio de datasets fabricaba velas**: devolvía 100 barras en rampa ascendente ante cualquier fallo de lectura, leía `timestamp` en vez de `timestamp_utc_ms` (todas las velas con marca 0) y su "hash SHA-256 verificado" era de metadatos. Su guard llevaba en verde vigilando una **copia muerta** | commit `08058feff` · `tests/test_data_pipeline.py` (10 passed) |
| **Meta-estrategia fantasma**: con ≤2 pasos de retorno alineados se fabricaba una correlación de 0,15, y sin periodos perdedores un profit factor de 5,0. Ahora falla cerrado | `tests/test_meta_strategy_engine.py` (5 passed) |
| **Motor 5.17.0**: dos arquetipos intradía para futuros de índice. Regla 26 cumplida, **15/15 celdas idénticas** | `orchestration/results/verificacion_f02_diff_5.16.0_vs_5.17.0.md` |
| **Web reorganizada**: 16 rutas duplicadas y huérfanas a cuarentena con manifiesto; el plan se lee de estos bloques en `/plan` vía `/api/plan` en vez de duplicar estados a mano | commit `08058feff` |
| **Historia de git adelgazada**: el push pendiente pasa de 1.324 MB a 3,1 MB. `.gitignore` no aplicaba a los 302 datasets ya rastreados | commits `20bdadf6e` y anteriores |

### Corrección de cifras que se habían dado por buenas

- La campaña evaluó **14.352** configuraciones, no 13.504.
- De las 24 celdas, sólo **18 son evidencia válida**: las 6 de forex corrieron con el motor anterior
  al arreglo de la comisión, así que su veredicto sobre la ventaja no vale.

### Deuda abierta y declarada

- **Build de producción de la web NO ejecutado.** Los revisores verificaron por lectura que ningún
  import queda colgando, pero eso no sustituye al build. La VPS está a 14 de carga por procesos
  ajenos (`sqcli` al 115 %, `discovery` al 31 %) y lanzar `next build` encima sería justo lo que hay
  que evitar.
- **La telemetría del embudo se calcula y se tira**: `mine.py` produce el desglose completo por
  configuración y nunca lo escribe a disco. De 14.352 configuraciones sobreviven 20 puntos de datos
  en los logs. Sin eso, cada campaña fallida es indiagnosticable.
- **Liberar la VPS sigue pendiente de sudo de Emilio** (comandos en `orchestration/OPERACION_VPS.md`).

## Hallazgo que define el estado de FONDEO

**FONDEO no está limitado por falta de edge: está limitado por falta de BARRAS.** Aritmética:

```
criterio 1.1 (SELLADO):   >=200 operaciones OOS
ritmo observado:          1 operacion cada ~61 barras (mejor caso real, RTY/CL; el ~101 previo
                          era solo el mejor caso por PF, ver embudo_fondeo_forense.md)
barras OOS necesarias:    ~20.200  ->  dataset de ~101.000 barras
disponible hoy (Yahoo):      13.800 barras   (7,3x por debajo)
Dukascopy 5m desde 2023:   ~250.000 barras   (~495 operaciones OOS)
```

El 5m de Yahoo NO es alternativa: tiene 13.813 barras, casi las mismas que 1h (13.701), porque
su API sólo sirve 60 días de intradía fino. **Dukascopy es la única vía**. Iba a 174 ficheros/hora;
tras sustituir `urlopen` por una `requests.Session` reutilizada va a **6.984/hora medidos en
producción**, y ES ya está completo y consolidado. Deja de ser el cuello de botella nº 1.

Matiz importante: el ritmo de operación varía mucho por familia (EURUSD REVERSION_ATR hace 447
operaciones en 10.341 barras IS = 1 cada 23). El **forex tiene 17.236 barras (6,3x más historia
que los futuros)** y es donde puede aparecer la primera candidata evaluable.

## HECHO en esta sesión (con evidencia en disco)

| Qué | Evidencia |
| :--- | :--- |
| **Gate 9 corregido**: el DoF devolvía 1 para estrategias de 3-5 dimensiones (`archetype_params` anidado) y la perturbación de vecindario ni pasaba esos parámetros → test de estabilidad era un no-op | `tests/test_red_team_adversarial.py` (9 passed) |
| **`risk_pct` cuenta como DoF** en todos los arquetipos (lo barre `mine.py` y con compounding altera PF/DD) | conteos 3→4, 5→6, 5→6, 4→5, 4→5, 7→8 |
| **F02.3**: reglas prop (trailing DD intradiario, pérdida diaria, cierre de sesión) sobre equity FLOTANTE en el motor. Opt-in | motor **5.15.0**, identidad **15/15 idéntica** |
| **BUG CRÍTICO forex**: `es_futuro = point_value != 1.0` clasificaba las divisas como CME → comisión `2,50 $ × qty` = **11.692 $ por lado**. Una operación ganadora perdía 11.670 $ | motor **5.16.0**, identidad 15/15 · `orchestration/results/bug_comision_forex_5_16_0.md` |
| **Bloqueo TRADFI levantado**: el "64-73 % de cobertura" medía contra calendario 24/7; el techo estructural de un futuro CME es 68,5 %. ES 1h tiene **95,45 % de contigüidad real** y 31 huecos anómalos que son festivos de mercado | `orchestration/results/desbloqueo_tradfi_calidad_datos.md` |
| **4h de TRADFI CONTAMINADO**: se remuestrea de 1h; 750/3.714 barras (20,2 %) con menos de 4 velas, 145 con UNA sola | mismo informe; aviso en `scripts/cola_mineria.py` |
| **Volumen de forex FABRICADO** (`or 100.0`): EURUSD 1h tiene un único valor distinto. Impacto hoy nulo (el motor no consume volumen) | mismo informe |
| **`fondeo_examen.py`**: el límite de pérdida diaria nunca se aplicaba (`pnl_dia += 0.0`) → P(romper cuenta) medida pasa de **0,27 % a 48,9 %**; y el ritmo de operaciones se asumía (60 días) en vez de deducirse | `tests/test_fondeo_examen_bugs.py` (7 passed) |
| **Pipeline de examen completo**: `PROP_FIRM_CATALOG` → evaluador (`--firma "Apex 50K"`, fail-closed ante ambigüedad) → `PropFirmProfile` del motor; regla de consistencia; **ranking** ordenado por el objetivo sellado | 29 passed |
| `median_days_to_target=22.0` inventado | corregido (violación REAL-ONLY) |
| Perfil `arquetipos` era **imposible de invocar** (faltaba en los `choices` de `cola_mineria.py` Y de `mine.py`) | corregido; campaña lanzada |

## Campaña FONDEO 1h — resultado honesto

**Perfil `arquetipos`: 12 celdas, 4.176 backtests, 0 certificadas.** Las 6 celdas de forex de esa
tanda son inválidas (bug de comisión, motor ≤5.15.0). Las 6 de futuros son veredicto válido.
Mejores casos en OOS: 24, 27, 8, 4, 0 operaciones — contra un mínimo de 100 y un criterio de 200.
**No pierden: apenas operan.**

**Perfil `amplio` (848 configs, 7 familias) en curso**, con el motor 5.16.0. Re-mina el forex con
números honestos y explora `INSTITUTIONAL_SESSION_MOMENTUM`, `TREND_FOLLOWING` y `MEAN_REVERSION`.

## PENDIENTE (camino crítico al goal)

0. **ANTES de minar con datos Dukascopy — dos cosas que hay que resolver primero:**
   a) **El mapeo símbolo→dataset NO reconoce Dukascopy.** `scripts/mine.py::resolve_dataset_file`
      busca por patrón `*{sym}*{tf}*.json` y elige el fichero **más grande** que coincida. Para
      `ES` el patrón `*es*5m*` NO casa con `ds_dukascopy_usa500idxusd_5m_*.json`, así que
      seguiría usando `ds_trad_es_5m_*.json` (Yahoo, 13.813 barras) **en silencio**. Hace falta
      un mapeo explícito FONDEO→Dukascopy: ES→USA500IDXUSD, NQ→USATECHIDXUSD, YM→USA30IDXUSD,
      GC→XAUUSD, SI→XAGUSD, CL→LIGHTCMDUSD (el mapeo ya existe como `proxy_for` en
      `services/data_ingestion/dukascopy_feed.py:76-84`). **RTY no tiene equivalente en
      Dukascopy** — o se acepta el Yahoo o sale del universo FONDEO.
   b) **Decisión doctrinal pendiente: los datos de Dukascopy son CFDs proxy, NO futuros CME.**
      Sustituir `ES=F` (el futuro real de Yahoo) por `USA500IDXUSD` (un CFD) **no es un ascenso
      automático de fidelidad** aunque tenga 18x más barras. Antes de certificar nada con ellos
      hay que validar correlación y spread contra el futuro real en el tramo que solapan
      (2024-03→2026-08, donde existen ambas series). Si divergen, certificar sobre el CFD y
      operar el futuro sería un autoengaño. **Esta validación es requisito previo, no opcional.**

1. **Acelerar Dukascopy** — cuello nº 1. Hay ~47 s por fichero perdidos en reintentos (latencia
   real del servidor: 15 s). Sospecha principal: backoff exponencial gastado en horas de mercado
   cerrado que devuelven 404 legítimo. Agente midiéndolo.
2. **Liberar la máquina** (requiere Emilio): `sqx.service` lleva horas al 105 % de CPU con
   **0 % de aceptación** sobre AUDUSD_H1, y un cron (`improve_cycle.sh`, minuto :40) reinicia el
   bucle de basura cada 20-30 min. Comandos en el informe de la sesión.
3. **SQX sobre ES/NQ/YM**: 97 Setups cargados pero usa sólo el primero por orden alfabético
   (AUDUSD_H1). Los CSVs de futuros ya están listos en `data/sqx_imports/`.
4. **Cablear F02.3 al ranking**: hoy el examen usa PnL realizado; el motor con equity flotante
   está construido pero no enchufado (`fondeo_examen.py` sólo recibe `oos_returns`, no velas).
5. Corregir `MarketDataAuditor.audit` para medir cobertura contra calendario de sesión por venue.
6. Push a GitHub pendiente (causa raíz diagnosticada, `.gitignore` y `filter-repo` preparados).

---

## Histórico anterior

# FASE ACTUAL — BALANCE 2026-08-31 ~18:45 UTC (plan v4 por bloques)

> **PAUSA ORDENADA v2 (19:20 UTC).** Cambios desde la nota anterior: la release 5.14.0 quedó
> CERRADA y COMMITEADA (identidad 15/15 idéntica, smoke 4 familias OK, 21 tests verdes,
> mensajes "wer"/"werwe" reescritos, merge -s ours con origin hecho — main local ahead 13).
> **El push a origin ABORTÓ por timeout de 10 min** (pack ~307 MB con la CPU colapsada):
> reintentarlo con la máquina descargada, es el primer paso de la próxima sesión.
> **Sobrecarga del VPS detectada:** al reiniciar la máquina ~18:17 systemd resucitó
> `ultrarentable-discovery.service` (enabled) y `sqx.service` (Build a 82% CPU), y quedó un
> minero huérfano sin gobernanza (PID variable, `run_continuous_pipeline`, ~5,8 GB RAM).
> El orquestador no puede pararlos (permisos): Emilio debe ejecutar
> `sudo systemctl stop ultrarentable-discovery.service sqx.service && sudo systemctl disable ultrarentable-discovery.service`
> y matar el minero huérfano (`pkill -f run_continuous_pipeline`). La web pasó a build de
> producción (`npm run build && npm run start -p 3000`, en marcha al pausar) con watchdog de
> auth de 6 s; causa raíz Firebase pendiente (claves .env.local mezclan proyectos).
> Gate 9 (novelty/DoF) NO conoce las dimensiones `archetype_params` de las 4 familias nuevas:
> corregirlo ANTES de la re-campaña `arquetipos` o el conteo de DoF será falso.
>
> Nota anterior (18:50 UTC), pasos 1-3 siguen válidos con lo de arriba:
> 1. La release **5.14.0 ya está en el árbol** (motor pineado, manifest y test de gobernanza
>    actualizados, fix del lookahead del TP de reversion_atr aplicado en
>    `event_backtest_engine.py:879`). Al pausar estaba corriendo la verificación de identidad
>    (`.venv/bin/python scripts/verificacion_f02.py`); si no dejó JSON de 5.14.0 en
>    `orchestration/results/`, re-ejecutarla y comparar con 5.13.0 (`--comparar`): las 15
>    celdas deben salir IDÉNTICAS. Falta también el smoke de las 4 familias
>    (`orchestration/results/smoke_arquetipos_5_14_0.md` aún no existe).
> 2. Con identidad + smoke verdes: commit temático de la 5.14.0, reword de los mensajes
>    "wer"/"werwe" (aún no publicados), `git merge -s ours origin/main` (análisis hecho: cero
>    contenido único en origin; push ~307 MB, ningún blob >100 MB) y **push a main**.
> 3. Después: re-campaña perfil `arquetipos` (encolar + trabajar), censo 1.1.
> Servicios: API :8000 activa; web Next.js lanzada en dev en :3000; sqx.service activo.

> Fuente de verdad por fase: `state/plan/bloques/Fxx_*.md`. Índice: `state/plan_maestro.md`.
> Ejecución: Hermes (orquestador) + subagentes de Claude, EN PARALELO. **Antigravity queda
> retirado del todo (orden expresa 2026-08-31): no se espera ni se integra nada suyo.**

## HECHO (hoy, con evidencia)

| Qué | Evidencia |
| :--- | :--- |
| F00 limpieza C–G + DB_PATH unificado (SSOT `services/api/app/config.py::STATE_DB_PATH`) | `cuarentena/*/MANIFEST*`, bloque F00 |
| F01 censo criterio 1.1: **0 supervivientes de 728**; regla #26 aplicada | `orchestration/results/censo_f01.md` |
| F02.1 motor honesto **5.7.0 → 5.13.0** (spread medido, comisión por lado, latencia next-bar-open, riesgo=FRACCIÓN, point_value, spread+funding reales BingX) | `orchestration/results/verificacion_f02_diff_*.md` (ledger a ledger) |
| F03.1 backfill profundo Binance **COMPLETADO**: 18 datasets 15m/5m desde 2021, 0 gaps | `data/binance_backfill_profundo.log` + manifiestos |
| F03.2 cola gobernada con heartbeat, anti-duplicados y `cancelar --motivo` | `scripts/cola_mineria.py`; cola: 20 COMPLETED / 7 CANCELLED |
| F03.3 campañas honestas 4h/1h (18 celdas, ~36k configs) y 15m profundo: **0 certificadas** → diagnóstico: familia EMA/RSI/Donchian agotada | bloque F03; `orchestration/results/cola_mineria.jsonl` |
| Diseño 5.14.0 sellado (4 familias nuevas de arquetipos) e implementación de señales en HEAD | `orchestration/reviews/diseno_arquetipos_5_14.md` |
| QA del orquestador sobre 5.14.0: entradas de las 4 familias causales y de evento correcto; 1 defecto hallado (lookahead en TP dinámico de reversion_atr) y pasado al agente que cierra la release | este documento; fix en curso |
| SQX: 2.035 .sqx de ToImprove materializados a disco + **export CSV de métricas HECHO** (2.035 filas, 44 columnas) | `data/sqx_exports/toimprove_2026-08-31.csv` |
| Registro de fricción BingX (9 pares, spread+funding, capturado 13:43Z) | `data/registry/bingx_friction.json` |

## EN VUELO (subagentes en paralelo, ahora mismo)

1. **Cierre release 5.14.0** (agente): fix del TP dinámico + bump `CURRENT_ENGINE_VERSION`
   5.13.0→5.14.0 + VERSION_HISTORY + pin de tests + verificación de identidad 5.13.0→5.14.0
   (15 celdas IDÉNTICAS = aceptación) + smoke real de las 4 familias.
2. **Análisis divergencia git** (agente read-only): main local ahead 8 / behind 2 de
   `origin/main`; los 2 de atrás son commits viejos de Antigravity deshechos en local.
   Verifica que descartar su contenido no pierde nada y estima el tamaño del push
   (datasets ~1 GB en `data/normalized/`, ningún blob puede superar 100 MB).
3. **Backfill Dukascopy** (nohup externo): solo `USA500IDXUSD` avanza (~1.155 .bi5);
   los otros 6 proxies + forex siguen a cero. Días de descarga. FONDEO bloqueado hasta esto.

Coordinación: hay una segunda sesión de Claude (01-ultrarentable-9a) en el repo, avisada y en
espera; los commits `60fd76bf8 "werwe"` y `5fcfea9ce` los hizo el usuario u otra vía (la
identidad git "Hermes User" es compartida). Reparto: esta sesión lleva 5.14.0, push,
re-campaña y SQX.

## PENDIENTE (en orden, camino crítico al goal ULTRA / ULTRA-meta / FONDEO / FONDEO-meta)

1. **Aterrizar 5.14.0** (identidad + smoke verdes) → commit temático + reconciliar divergencia
   con origin y **push a main** (autorizado expresamente; commits temáticos, nunca releases a
   medias).
2. **Re-campaña perfil `arquetipos`**: cripto 15m + 4h con datos profundos (encolar + trabajar
   con la cola gobernada, concurrencia 2).
3. **Censo criterio 1.1** sobre el resultado (sin relajar NADA). Si hay supervivientes →
   F04 (mejora inteligente) → F05 (envolvente ULTRA) → F06 (meta-router) = ULTRA y ULTRA-meta.
4. **Carril SQX**: cruzar el CSV de métricas con los 2.035 .sqx; parser AST → validación con
   motor propio (11 gates). Materia prima adicional para F04.
5. **FONDEO**: espera backfill Dukascopy verificado → campaña TRADFI → F07 exámenes prop =
   FONDEO y FONDEO-meta. Antes: F02.3 (trailing DD intradía, reglas prop).
6. F02.2 restante: cap apalancamiento real BingX (bloqueado: requiere API key del usuario) y
   liquidación con margen aislado.
7. Fase I restantes de F00: unificación 0.4 (entradas de minería) y 0.6 (dos motores de
   backtest); fusión learning_store (F04).

## Reglas vigentes

1. Git: push a main **autorizado** (2026-08-31) — commits temáticos descriptivos; decidir con
   criterio los artefactos pesados; nunca subir árboles incoherentes.
2. CERO `rm` — todo a `cuarentena/` con manifiesto SHA-256.
3. REAL-ONLY: cero mocks, cero datos sintéticos; criterio 1.1 SELLADO (no se relaja).
4. Regla #26: todo cambio que altere operaciones sube versión de motor; nada se borra.
5. Multiagentes simultáneos para lo mecánico; el orquestador analiza, investiga y prueba.
