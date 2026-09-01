# FASE ACTUAL — 2026-09-01, ~19:00 UTC · CICLO 1 DE LA ERA LOCAL (orquestador Opus 5 en el PC)

> **MANDATO ACTIVO: FONDEO + META-FONDEO + arreglar `/estrategias`.** ULTRA queda **EN
> CONSTRUCCIÓN, presente y visible en todo el proyecto**, nunca borrado y sin cerrarle puertas
> (`PUNTO_GUARDADO_ULTRA.md`; F05/F06 con `aparcado: true`).
>
> Método: loop no bloqueante. Este ciclo corrieron **5 subagentes** con contrato mientras el
> orquestador trabajaba su cola propia. Todo aterrizaje se auditó con comandos propios ANTES de
> darlo por bueno; dos afirmaciones heredadas cayeron en esa auditoría (§3).

## 1. El marcador, sin adornos

**Estrategias FONDEO certificadas: 0. Meta-estrategias: 0.** No ha cambiado y no se ha maquillado.
Lo que sí ha cambiado es que ahora sabemos que **parte de lo que creíamos saber sobre POR QUÉ era
0 estaba mal medido** (§3).

## 1.b HITO DEL CICLO — W0.2 CERRADO: el motor es IDÉNTICO en este PC (15/15)

Era la puerta que bloqueaba toda la minería local ("15/15 idénticas o STOP"). **Pasada.**

```
baseline sellado : 2026-09-01T09:26:12Z   (generado en el VPS)   celdas=15
ejecución en PC  : 2026-09-01T17:05:39Z                          celdas=15
  BTCUSDT 4h c1/c2/c3 · ETHUSDT 4h c1/c2/c3 · LINKUSDT 1h c1/c2/c3
  ES 4h c1/c2/c3 · GC 4h c1/c2/c3          →  todas IDÉNTICAS
VEREDICTO W0.2: 15/15 IDENTICAS, 0 diferentes  =>  IDENTIDAD CONFIRMADA
```

La comparación es campo a campo e incluye la **huella SHA-256 del ledger de operaciones** de cada
celda, no solo las métricas agregadas: el motor 5.17.0 en Windows nativo produce las mismas
operaciones, una a una, que el que selló el baseline. **Desde ahora, minar en el PC es legítimo.**

Evidencia: `results/verificacion_f02_5.17.0_EJECUCION_PC_2026-09-01.json` (la ejecución del PC,
guardada aparte) y `results/verificacion_f02_5.17.0.json` (el baseline sellado, intacto:
`c1c3a7bbff2309...`).

Cómo se consiguió: los 5 datasets de referencia se trajeron del VPS por `scp` y **verifican 5/5
contra el `checksum_sha256` de su manifiesto**, hash a hash. Sin esa verificación previa el
resultado no valdría nada (§3.3).

## 2. Lo que se ha desbloqueado hoy (verificado en esta máquina)

| # | Hecho | Evidencia |
| :-- | :--- | :--- |
| 1 | **El entorno del PC funciona** — sin WSL, en Windows nativo | `.venv` con Python 3.11.8, `import services` OK, `CURRENT_ENGINE_VERSION = 5.17.0` |
| 2 | **El ssh PC→VPS ya funciona sin contraseña** (W0.3 HECHO, no requería a Emilio) | `ssh -o BatchMode=yes oracle-vps 'echo ok'` → OK, clave `id_rsa_openclaw` |
| 3 | **El sudo del VPS NO pide contraseña** — el bloqueo de días era falso | `sudo -n true` → `SUDO_NOPASSWD_OK` |
| 4 | **Los datos SÍ existen: 1,9 GB de velas reales en el VPS**, incluidos los 5 datasets de identidad y el consolidado Dukascopy de ES (5m 42 MB, 15m 14 MB) | inventario por ssh, tamaños fichero a fichero |
| 5 | **SQX está instalado en el PC y su licencia es una PRUEBA que caduca el 2026-09-05** | `sqcli.exe -license action=info` → `Pro Build 144 (Trial license) - valid until 05.09.2026` |
| 6 | **Grafo de imports completo**: 310 nodos (= `find services scripts -name "*.py" \| wc -l`), 1.003 aristas | `results/grafo_imports_2026-09-01.{json,md}` |
| 7 | **Catálogo de prop firms 2026 re-verificado contra ToS oficiales**, con cita y fecha por parámetro | `results/I4_prop_firms_hallazgos.md` |

## 3. LAS DOS CORRECCIONES DEL CICLO (evidencia contra documento; manda la evidencia)

### 3.1 El "20/20 sin_ventaja" no demostraba lo que decíamos — REFUTADO

`current_phase` §3 (versión anterior) y la evaluación externa elevaban a "pregunta que puede
invalidar el plan" la telemetría de ES 4h. Medido hoy: **evaluó 20 de 420 configuraciones y las
20 son de UNA sola familia (`REVERSION_ATR`)**, porque `mine.py` trunca por **prefijo** con
`--max-candidates`, cuyo valor por defecto es **20**. `OPENING_RANGE_BREAKOUT` y `VWAP_REVERSION`
—las dos familias creadas expresamente para FONDEO en 5.17.0— **no se han ejecutado nunca** ahí.

Cobertura real: **4,8 % del espacio, 1 de 6 familias**, en un timeframe (4h) para el que esas
familias no están diseñadas y sobre el dataset Yahoo 4h ya declarado contaminado.

**Consecuencia de plan (D1, sellada):** la regla pre-sellada *"≥80 % de muertes por `sin_ventaja`
⇒ familia agotada"* **queda suspendida** hasta que la telemetría registre cobertura por familia:
aplicada sobre un embudo truncado por prefijo, abandonaría una celda habiendo probado una sexta
parte. **(D2)** Toda campaña se lanza con el espacio completo o con muestreo estratificado, nunca
con el default. Expediente: `reviews/forense_telemetria_2026-09-01.md`.

### 3.3 El `checksum_sha256` de los manifiestos nuevos NO valida el contenido — DEFECTO REAL

Encontrado por el agente de datos y **confirmado por mí leyendo el código**:
`services/data/market_ingestor.py:104` calcula lo que llama "Checksum SHA-256 determinista" así:

```python
payload = f"{venue}:{symbol}:{interval}:{len(unique_bars)}:{start_ts}:{end_ts}"
sha_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
```

Es un hash de **metadatos**, no del contenido: dos ficheros con las mismas velas contadas pero
valores de precio distintos producen el mismo "checksum". Un dataset corrupto pasaría la custodia.

**Matiz importante, medido:** los manifiestos **canónicos** del repo NO tienen este problema — sus
checksums SÍ son del contenido, verificado 5/5 por `sha256sum` contra fichero real. Y otra ruta de
código (`services/api/app/api/routes.py:168`) compara el hash del contenido. Es decir: **hay dos
formas de calcular el checksum conviviendo**, y la de `market_ingestor` es la mala. Todo dataset
ingerido por esa vía lleva un sello que no certifica nada. Va al backlog como deuda W1.6.

### 3.2 Las dos suites de gates SÍ están entrelazadas — y peor de lo que decía el expediente

> **Corrección de una afirmación mía anterior.** En la primera versión de este checkpoint escribí
> que el enredo entre las dos suites quedaba REFUTADO porque "ningún fichero importa las dos".
> **Era falso, por un error de medición mío**: grepeé el subpaquete `services.validation.engines`
> cuando el expediente I7 habla del paquete `services.validation` **entero**. Midiendo lo que
> tocaba, el resultado se invierte. Queda escrito así, con el error a la vista, porque la
> doctrina de esta casa vale también para el orquestador.

Medición correcta — ficheros que importan **ambas** (`services.validation.*` y
`services.api.app.validation.gates.*`): **19**, entre ellos dos que están en el camino crítico:

```
scripts/mine.py                                    <-- el minero
services/discovery/discovery_validation_pipeline.py
services/optimization/expert_refinement_loop.py
services/optimization/universal_optimizer_engine.py
services/semantic_ai/autonomous_discovery_engine.py
services/validation/legacy_revalidation_service.py
+ 13 scripts de diagnóstico/certificación
```

El expediente I7 decía "un router importa las dos". El detalle es inexacto —
`candidates_router.py` importa `services.api.app.validation.market_specs` (no los gates) y
`services.validation.legacy_revalidation_service`— pero **la tesis de fondo se CONFIRMA y se
agrava**: no es un router, son 19 ficheros, y uno es `mine.py`. "Mejorar solo las puertas" hoy es
imposible, tal como sostiene I7.

Matiz útil que sí se sostiene: el subpaquete `services/validation/engines/` tiene **un único
importador externo** (`validation_router.py`), así que **ESE** trozo concreto sí se puede extraer
barato. Es por dónde conviene empezar el movimiento 1.

CONFIRMADO además el tamaño del monolito: `services/api/` = **29.478 LOC** exactos.

## 4. Deuda y bloqueos vivos

| Bloqueo | Estado real |
| :--- | :--- |
| ~~W0.2 identidad del motor~~ | ✅ **CERRADA: 15/15 idénticas** (§1.b). Ya no bloquea |
| **Datos para minar de verdad** | Solo están los 5 datasets de identidad. Falta traer el consolidado Dukascopy de ES (5m 42 MB / 15m 14 MB, ya existe en el VPS) y completar el backfill del resto de símbolos. **Es ahora el único bloqueo de la campaña** |
| **`verificacion_f02.py` destruye su propio baseline** | Defecto nuevo encontrado al ejecutarlo: sobrescribió el fichero sellado de 5.17.0 con `SIN DATOS`. Recuperado por `git restore`, salida mala en `cuarentena/verificacion_f02_sobrescritura_2026-09-01/` con manifiesto. Corrección despachada (W4.6) |
| **VPS saturado** | Confirmado en vivo: swap 4,0/4,0 GB, load 3,2 sobre 4 núcleos, `sqcli` al 58,9 % y 4,5 GB, `memory.events high` = **7.575.123** (eran 713.626). Los comandos están listos; **falta autorización de Emilio** (no contraseña) |
| **Licencia SQX** | Caduca **2026-09-05**. Decisión de Emilio en `VENTANA_EMILIO.md` §3 |
| **Login de la web** | Causa raíz CONFIRMADA leyendo `apps/web/lib/firebase.ts:5-13`: mezcla `goalskid-app` (apiKey/authDomain/projectId) con `pecemi` (databaseURL), y **no existe `.env.local`** |
| Deudas W4.1/4.2/4.4 | En reparación (AG-C) |

## 5. Hallazgo que cambia la arquitectura de ejecución

**Topstep y TradeDay prohíben operar desde un VPS**, verificado por mí contra la página oficial de
Topstep (no me fié del informe del agente):

> "All trading activity must originate from your personal device. The use of VPS, VPNs, and remote
> servers is prohibited by Topstep's Terms of Use." … "your server can watch and record, but it
> cannot trade."

**Consecuencia:** el vigía Hermes del VPS se queda en **V0 (solo lectura) de forma permanente**
mientras esas firmas estén en juego; V1/V2 (ajustar órdenes) **no pueden vivir en el VPS**. Todo
envío de órdenes tendrá que salir de este PC, que además es el que tiene IP residencial. Pendiente
de reflejar en `HERMES_VPS_VIGIA.md`.

## 6. Estado de los agentes de este ciclo

| Agente | Contrato | Estado | Auditoría del ORQ |
| :--- | :--- | :--- | :--- |
| AG-10 | I4 prop firms 2026 | ✅ aterrizado | **Verificadas 2 citas** por fetch propio (Topstep y MFFU): literales exactos. Informe fiable, con marcadores honestos `[FETCH]` / `NO VERIFICABLE` |
| AG-9 | I1 StrategyQuant X | ✅ aterrizado | **Licencia re-verificada por mí** ejecutando `sqcli.exe`: coincide. Refuta `MaxTradesPerDay=1` del repo (el valor real es 0) |
| AG-5 | I7 grafo de imports | ✅ aterrizado | **Re-contado por mí**: 310 nodos = 310 ficheros; 29.478 LOC exactos; el fichero-bisagra está en la línea 31 declarada. Correcto |
| AG-D | Datos (rsync + backfill) | ✅ aterrizado, lote parcialmente rechazado | **Rechacé sus 5 datasets**: no cuadraban con el manifiesto canónico (los re-generó en vez de copiarlos). A cuarentena con manifiesto; los canónicos los traje yo del VPS y verifican 5/5. **A su favor**: encontró el defecto real del §3.3 y dejó el backfill Dukascopy corriendo con crecimiento medido (692→2.131 ficheros). **Nota de proceso**: rechazó mis dos mensajes de corrección por considerarlos un canal lateral no contemplado en su contrato — cautela correcta por su parte, pero cuesta un ciclo: los contratos futuros deben declarar de entrada que el ORQ puede reorientar en marcha |
| AG-C | Deudas de certificación | 🔄 corriendo | ya se ve `scripts/fondeo_examen.py` modificado |

## 7. Siguiente ciclo (orden)

1. **Traer el consolidado Dukascopy de ES del VPS** (5m/15m) y verificarlo. Es lo único que separa
   de la primera campaña legítima.
2. Auditar AG-C y commitear el lote de honestidad (primer commit temático del ciclo).
3. **Experimento E1**: re-ejecutar las 20 `REVERSION_ATR` de ES sobre Dukascopy 5m/15m y comparar
   con el PF 0,03-0,19 de Yahoo 4h. Separa "familia mala" de "dataset contaminado" de "bug de
   coste". Nota: la ejecución de identidad de hoy da para ES 4h PF 1,01 / 0,55 / 1,83 y para GC 4h
   PF 0,20 / 0,24 / 0,32 con el perfil `champions`, lo que refuerza que el 0,03-0,19 del embudo
   `arquetipos` merece explicación propia.
4. **Campaña E2**: ES 5m/15m con las **6 familias completas** (`--max-candidates 0`) y telemetría
   con cobertura. Solo entonces "¿dato o edge?" tiene respuesta legítima.
5. Web: poda + reescritura de `/estrategias` según `reviews/diseno_pagina_estrategias_2026-09-01.md`.
6. Si Emilio autoriza: limpieza del VPS y experimentos SQX **antes del 5 de septiembre**.

---

## Histórico anterior

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
