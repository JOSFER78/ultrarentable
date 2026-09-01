# FASE ACTUAL — 2026-09-01, 10:20 UTC

> **MANDATO ACTIVO: 100 % FONDEO.** Estrategias para futuros CME de prop firms y sus
> meta-estrategias. **ULTRA y META-ULTRA quedan APARCADOS**, con su estado íntegro congelado en
> `PUNTO_GUARDADO_ULTRA.md` y sus fases F05/F06 marcadas `aparcado: true`. Aparcado no es
> abandonado: la tesis de la envolvente de balas sigue sellada y válida, simplemente no es el
> trabajo de ahora.

## 1. Dónde estamos con el objetivo, sin adornos

**Estrategias FONDEO certificadas: 0. Meta-estrategias FONDEO: 0.**

No es un matiz de redacción. Contra la BD canónica de producción, medido hoy:

- `route='FONDEO'` con cualquier estado certificado: **0 filas**. Todas son `REJECTED_*`,
  `LEGACY_*` o `BLOCKED_NO_EVIDENCE`, y bajo motor 5.4.0, obsoleto.
- `route='ULTRA'` con `APPROVED_CURRENT_ENGINE`: 5 filas, pero **ninguna alcanza las 200
  operaciones OOS** del Criterio 1.1 (rango real 25-68). Ese estado NO implica certificación: es
  un listón más débil, y conviene no confundirlos nunca más.

Todo el trabajo de hoy ha sido **quitar lo que impedía siquiera intentarlo**. No se ha conseguido
todavía ninguna estrategia.

## 2. La cadena hacia el objetivo, eslabón por eslabón

| # | Eslabón | Estado | Evidencia |
| :-- | :--- | :--- | :--- |
| 1 | Datos con presupuesto de barras suficiente | ✅ | 250.009 barras 5m de ES consolidadas; 200 ops OOS exigen 1 cada 250, antes 1 cada 13,7 |
| 2 | El proxy CFD representa al futuro | ✅ | Validación doctrinal: correlación de retornos 0,9747, peor subperiodo 0,9016 |
| 3 | `--dataset-source` viaja de la cola a `mine.py` | ✅ | Verificado extremo a extremo contra BD temporal |
| 4 | La deduplicación permite re-encolar con otra fuente | ✅ | Antes: 34 de 34 celdas omitidas en silencio. Ahora: 34 lanzables |
| 5 | El discovery continuo ve FONDEO | ✅ | Bug de enrutamiento corregido (`1956e3816`) |
| 6 | Arquetipos que operan lo suficiente intradía | ✅ | ORB y VWAP_REVERSION en motor 5.17.0, identidad 15/15 |
| 7 | El motor cobra bien las comisiones | ✅ | 5.16.0: el forex pagaba 11.692 USD por lado |
| 8 | Reglas de prop firm sobre equity flotante | ⚠️ PARCIAL | El motor las evalúa (5.15.0) pero **el examen no las usa para decidir**, ver §5 |
| 9 | **Máquina capaz de correr la campaña** | ❌ **BLOQUEADO** | Swap 1 MB libre, carga 10,05, `sqcli` al 115 % |
| 10 | Campaña FONDEO 5m/15m ejecutada | ⛔ no lanzada | Depende del 9 |
| 11 | Meta-estrategias ensamblables | ❌ | Necesita ≥2 certificadas. Además, ver §5 |

**El único eslabón roto que no depende de código es el 9**, y depende de comandos con sudo que
sólo puede ejecutar Emilio. Están en `../OPERACION_VPS.md`.

Comando exacto en cuanto la máquina lo admita:

```bash
python -m services.ops.gobernanza_recursos ejecutar --nombre campana-fondeo-5m -- \
  python scripts/cola_mineria.py encolar --solo-track fondeo --dataset-source dukascopy --ver
```

## 3. LA PREGUNTA ABIERTA QUE PUEDE INVALIDAR EL PLAN

La narrativa que este documento sostenía —*"FONDEO no está limitado por falta de edge, sino por
falta de barras"*— **no está sostenida por los propios datos de la campaña**, y hay que decirlo.

Medido sobre `cola_mineria.jsonl` en GC y ES a 1h con perfil `arquetipos`, las dos únicas celdas de
futuros limpias (sin el bug de comisión del forex):

```
GC: 341 de 348 configuraciones mueren ya en IS
ES: 345 de 348 configuraciones mueren ya en IS
    con 8.220-8.242 barras IS disponibles
    y un filtro trivialmente laxo: total_trades < 5 or profit_factor < 1.05
```

Eso **no** es escasez de barras OOS: es que casi ninguna combinación de EMA-cross / RSI / ATR
alcanza un PF de 1,05 **en su propia muestra de entrenamiento**. Más barras resuelven el problema
del recuento de operaciones; no resuelven la ausencia de ventaja.

Las dos hipótesis siguen vivas y son distinguibles, pero **nadie las ha distinguido todavía**,
porque no se sabe si mueren por `trades < 5` o por `PF < 1,05`. Y no se sabe porque la telemetría
del embudo **se calcula y se tira**: `run_mining_pipeline()` produce un registro por configuración
descartada (`strategy_id`, `etapa`, `motivo`) y lo devuelve en un `dict` que nadie serializa; la
cola sólo guarda las 3 últimas líneas de stdout truncadas a 500 caracteres. De 14.352
configuraciones evaluadas sobreviven **20 puntos de datos**.

**Acción declarada como siguiente:** persistir esa telemetría antes de lanzar la campaña grande.
Sin eso, la próxima campaña será tan indiagnosticable como la anterior, y si vuelve a dar cero no
sabremos si el problema son los datos, los arquetipos o el filtro.

## 4. Lo hecho hoy, con evidencia en disco

### Datos

- **ES completo y consolidado**: 16 chunks trimestrales fusionados. 250.009 barras en 5m, 83.377
  en 15m, 1.230.396 en 1m. Rango 2023-01 → 2026-08, SHA-256 reproducible, `gaps_filled=false`,
  huecos clasificados por **calendario de sesión**: los 36 anómalos son festivos reales de mercado.
- **Ingesta 40x más rápida**: `urlopen` por petición → `requests.Session` reutilizada. De 174 a
  **6.984 ficheros/hora medidos en producción**.
- **Fusión no destructiva**: `ingest()` abría el CSV en modo `"w"` y volcaba sólo las barras de la
  llamada en curso; cualquier ingesta parcial destruía el fichero entero.

### Motor — tres releases, todas con identidad 15/15

| Versión | Qué cambia |
| :--- | :--- |
| 5.15.0 | Reglas de prop firm evaluadas barra a barra sobre equity **flotante** (opt-in) |
| 5.16.0 | `es_futuro = point_value != 1.0` clasificaba el forex como CME: un EURUSD con +32,1 USD brutos pagaba 11.692,5 USD de comisión por lado |
| 5.17.0 | Arquetipos ORB y VWAP_REVERSION para futuros intradía de índice |

### Defectos graves corregidos fuera del motor

- **El discovery llevaba >24 h sin evaluar FONDEO**: la rama por defecto exigía `"fondeo" in fname`
  dentro de un `else` que sólo se alcanza cuando eso ya es falso. Todo dataset de FONDEO se
  evaluaba como ULTRA, con 1.000 USD de capital y 25 % de techo de drawdown en vez de 50.000 y
  4,5 %.
- **El repositorio de datasets fabricaba velas**: 100 barras en rampa ascendente perfecta ante
  cualquier fallo de lectura, campo `timestamp` en vez de `timestamp_utc_ms` (todas las velas con
  marca 0), y un "hash SHA-256 verificado" calculado sobre metadatos. Su guard llevaba en verde
  vigilando una **copia muerta**.
- **Meta-estrategia fantasma**: con ≤2 pasos de retorno alineados se fabricaba una correlación de
  0,15; sin periodos perdedores, un profit factor de 5,0.
- **`fondeo_examen.py`**: el límite de pérdida diaria no se aplicaba nunca. P(romper cuenta) medida
  pasó de 0,27 % a 48,9 %.

### Infraestructura y orden

- **Gobernanza de recursos** (`services/ops/gobernanza_recursos.py`): turno único con `flock` y
  puerta de admisión que rechaza arrancar con la máquina saturada. Ver `../OPERACION_VPS.md`.
- **Web**: 16 rutas duplicadas y huérfanas a cuarentena con manifiesto verificado una a una; el
  plan se lee de estos bloques en `/plan`.
- **Git**: el push pendiente pasó de 1.324 MB a 3,1 MB.

## 5. Deuda abierta, declarada y sin disimular

| Deuda | Por qué importa |
| :--- | :--- |
| **Telemetría del embudo no persistida** | Sin ella la próxima campaña vuelve a ser indiagnosticable. Es el §3 |
| **El examen de fondeo no gatea con la verificación honesta** | `reejecutar_examen_barra_a_barra()` se calcula pero **no decide**: el ranking sigue usando el bootstrap optimista. Hoy es inerte con 0 candidatas, pero en cuanto haya una podrá imprimir "CUMPLE" para una cuenta que la verificación marca como reventada |
| **Meta: versión de motor escrita a mano** | `meta_ensemble_service.py` y `meta_strategy_pipeline.py` filtran por `engine_version == '5.4.0'` con el motor en 5.17.0. Descartarían siempre cualquier candidata nueva, y el endpoint lo envuelve en un `except Exception: pass` mudo |
| **Dos pipelines de validación** | El que certifica es `services/api/app/validation/gates/`; el que ve la web cuelga de `services/validation/engines/`, con umbrales distintos en su gate 3 |
| **Build de producción de la web sin ejecutar** | Verificado sólo por lectura de código |
| **Cifra "18/24 celdas válidas" mal clasificada** | El bug de comisión afecta a **las 12** celdas de forex, no sólo a 6. Corregir en el forense |
| **VPS pendiente de sudo** | Eslabón 9 de la cadena |

## 6. Dónde está cada cosa

Ver `../README.md` para el mapa completo de `orchestration/`.

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
