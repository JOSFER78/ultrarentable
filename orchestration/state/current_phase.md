# FASE ACTUAL — 2026-09-02, ~11:30 UTC · CICLO 3 DE LA ERA LOCAL (orquestador Fable 5.1 en Orca; agentes Antigravity atados)

> **MANDATO ACTIVO (sin cambios): FONDEO + META-FONDEO + `/estrategias`.** ULTRA EN CONSTRUCCIÓN,
> presente y visible, nunca borrado. **Regla de este ciclo (Emilio):** todo lo mecánico lo
> ejecutan hasta 10 agentes en vuelo por el sistema multiagente de Orca (todos `agy` con Gemini 3.7
> Flash; Hermes cuando Emilio lo diga; **nunca codex**, orden de Emilio del 02-09); el orquestador planifica, despacha, audita
> re-ejecutando, integra y commitea. Punto de entrada: `PLAN_ORCA_ANTIGRAVITY.md`.

## 0. Marcador, sin adornos

**Estrategias FONDEO certificadas: 0. Meta-estrategias: 0.** Sin cambios.

## 1. §0 del plan (integrar y verificar) — HECHO, con dos correcciones al arnés

| Paso | Estado | Evidencia |
| :-- | :--- | :--- |
| Commits de los ciclos 1-2 en `main` | ✅ 4 commits temáticos: arnés+plantillas, docs ciclo 3, telemetría W2.7 (auditada: 8/8 + 3/3 tests, diff aditivo), `export_to_sqx.py` (verificado: 83.377 filas = barras ES 15m) | `234d48d0f`, `8fd3c9334`, `06b46b579`, `98450ec90` |
| Arnés activado y probado | ✅ pero **el arnés original NO ataba nada en el montaje real** (ver §2) → corregido y re-probado en la rama real de un agente: commit de agente BLOQUEADO, commit del ORQ PASA, push bloqueado con y sin `ORQ_PUSH`, dataset pesado BLOQUEADO | `9e63ba021`; `orchestration/results/agy/SMOKE.md` |
| devilray ← main (ff) | ✅ | `git log` devilray |
| `VENTANA_EMILIO.md` | ✅ actualizada (SQX caduca el 05-09; pregunta 5.2 añadida) | `4366f8903` |

## 2. Decisiones nuevas (D11-D14) — todas nacidas de evidencia

- **D11 — pre-commit en lista blanca.** Un agente de humo (`SMOKE`, primer worker real por el
  camino nativo de Orca) commiteó de verdad: Orca nombra las ramas `JOSFER78/agy-<ID>` (el patrón
  `agy/*` nunca casaba) y `worker-start` no propaga `AGY_AGENT`. Ahora nadie commitea sin
  `ORQ_COMMIT=1`, sea cual sea la rama o el entorno. El pre-push casa `agy` en cualquier posición.
- **D12 — hooks fuera de los worktrees.** `core.hooksPath=.githooks` (relativa) hacía que cada
  worktree ejecutara la copia del hook de SU rama, editable por el agente. Ahora
  `core.hooksPath=C:/Users/yo/.orq-hooks` (absoluta; los ficheros del repo son la fuente y se
  copian ahí tras cada cambio). Agujero conocido y aceptado: `--no-verify` y `-c core.hooksPath=`
  saltan cualquier hook de git; la defensa es que ninguna rama de agente se integra sin auditar
  y sin comprobar que no trae commits.
- **D13 — despacho nativo de Orca, receta de 5 pasos.** Documentada en la skill `orquesta` §7 ter:
  worktree propio (`--setup skip`: Orca lanzaba `npm install` en cada worktree), terminal con
  comando PURO (`agy …`; con prefijo de entorno Orca no reconoce al agente), confianza sembrada en
  `~/.gemini/antigravity-cli/settings.json`, `tui-idle`, `worker-start --worktree … --terminal …`.
  El entorno por worktree (`AGY_AGENT`, `PYTHONPATH`, `A06_DATASET_FILE`) lo pone un bloque
  acotado por ruta en el perfil de PowerShell.
- **D14 — Ola A re-planificada sobre lo ya hecho.** AG-C ya cerró W4.1/W4.2/W4.4/W4.6 (commit
  `ad9e179ff`): A03 pasa a **W0.8** (portar la puerta de admisión a Windows: hoy revienta por
  `fcntl`, y sin ella no hay semáforo de pesados), A10 audita esas deudas **con tests**, A11 cierra
  D2 + W2.8. Hasta que A03 aterrice, la admisión de pesados la da el ORQ a mano vía
  `orca orchestration ask`.

## 3. Ola A — en vuelo (Run `run_19da24acd52a`)

Contratos en `orchestration/agy/GO_A01..A12.md` (commit `f92b192cc`).

**Aterrizajes auditados e integrados en devilray (12:10 UTC):**

| ID | Qué | Veredicto del ORQ (re-ejecutado) | Merge |
| :-- | :--- | :--- | :--- |
| A04 | W1.6 checksum de contenido | ACEPTA; 176/176 datasets reales verifican | `afecc3ee3` |
| A03 | W0.8 puerta de admisión en Windows | ACEPTA; umbrales intactos; candado real | `11de1dfa6` |
| A05 | W1.7 backfill idempotente | ACEPTA; 8/8 tests; dry-run real 10 PENDIENTE | `695ecee7b` |
| A01 | arnés `aceptar_agy.py` | REPITE 1 (comillas rompían el parser; ignorados en data/) → ACEPTA 7/7 | `85ae6deb4` |
| A11 | telemetría D2 + W2.8 | ACEPTA; 21/21 tests; espacio arquetipos = 420 | `1b9d189b3` |
| A06 | W4.7 registro de gates v1 (D5) | ACEPTA; paridad con B, gate 10 = 40; dataset real 4/4 | `9f1e33ef2` |
| A10 | tests de W4.2/W4.4/W4.6 | ACEPTA tras apartar un artefacto del `--comparar`; **deuda W4.2-bis** (except mudo en discovery) | `e88b1de81` |
| A08 | motor 5.18.0 (regla #26, D10) | ACEPTA; 9 ULTRA idénticas, 6 FONDEO explicadas; territorio ampliado por W29 | `19b39b596` |

| A12 | W5.2 web maestra + home | ACEPTA; tsc limpio, 0 colores fuera de tokens; build ORQ 23 rutas | `fe686c0de` |
| A07 | refutador de A06 | CONFIRMADO: 0 divergencias en 3 evidencias, determinista (reproducido) | `b8c2686b9` |
| A09 | refutador de A08 | CONFIRMADO: 9 ULTRA idénticas, 6 FONDEO explicadas (reproducido) | `ef1d8ed37` |
| A01 | CORRECCION_2 (UTF-8 en subprocess) | ACEPTA 8/8; el arnés ya no muere con salidas no ASCII | `61bd2f273` |

**Integración global verificada** en devilray: 78 tests (todos los nuevos + suites tocadas) en verde,
`next build` 23 rutas. **`main` ← devilray (ff) y push a origin: `a1564650f..ef1d8ed37`** (12:30 UTC).
Pendiente de la Ola A: A02 (`agy`, refutador del arnés: hooks + `aceptar_agy.py`).

**Seguimiento para Emilio: GitHub Issues del repo (pestaña Tareas de Orca):** tablero #23, un issue por
agente (#3-#21, #24-#28), ventana única #22 asignada a él. Orden de Emilio (12:45): **nunca codex**;
A02 relanzado en `agy`. B07 (`services/improvement`) integrado (`cf91ac01b`).

## 3 bis. Ola B — aterrizajes auditados e integrados (13:05 UTC)

| ID | Qué | Veredicto del ORQ (re-ejecutado) | Merge |
| :-- | :--- | :--- | :--- |
| B07 | `services/improvement` (M2, W3.5.b) | ACEPTA; frontera limpia por AST; 423 trials al gate 8 | `cf91ac01b` |
| B05 | parser `.sqx` piloto (W3.3) | ACEPTA; 20 en 3,15 s, 9 AST completos, 0/11 gates sin backtest propio. **Hallazgo: 117 `.sqx` en el PC, no 2.035** (databanks en el VPS) | `a5eebf31b` |
| B02 | **E1** (20 configs `reversion` ES 5m/15m, 5.18.0) | ACEPTA. **20/20 `sin_ventaja_bruta` en 5m y 15m** con 1.143-4.097 ops por config: **familia mala, no dataset ni coste**. La lectura "PF 0,03-0,19 del 4h Yahoo" era muestra pequeña; en datos reales la señal sigue sin ventaja antes de costes | `dbbe0b693` |
| B08 | `services/meta` (M4, W6.0, D8/D9) | ACEPTA; 10/10; correlación fail-closed; HRP/mín-var deterministas; sin router | `00175aff9` |

| B09 | catálogo de prop firms v2 con SourceRef (W4.8/W4.9a, D6) | ACEPTA; 5 tests reales; sync 501; motor intacto | `7e754d9c5` |
| B11 | inventario de datos PC+VPS (W1.2/W1.3) | ACEPTA; custodia 6/6; ES r=0,9916 APTO; 165 datasets solo en VPS | `96ceecba9` |
| B10 | `/prop-firms` sobre el catálogo v2 con `SourceRef` (W5.8, D7) | ACEPTA; tsc rc=0; 0 importadores de `lib/prop-firms`; 3 `NO EVIDENCE`; 0 colores fuera de tokens; `lib/prop-firms.ts` (4.307 LOC comerciales) a `cuarentena/web_prop_firms_ts_20260902/` con SHA-256; `next build` rc=0 tras integrar | `d611f73cc` |
| B14 | arnés de aceptación v2 (D16) | ACEPTA; 12 passed; rechaza `commits_del_agente` y `go_alterado`; se acepta a sí mismo | `109046478` |
| B12 | vigía V0 solo lectura + unit/timer systemd en seco (W7) | ACEPTA (continuación en agy limpio tras morir el agente original); 5 passed; `NO DATA` honesto; 0 vías de envío de órdenes | `0f6d0e41c` |
| B17 | `/estrategias` sobria estilo terminal | ACEPTA; 566 líneas (antes 1.909); 0 colores/sombras/emojis; mismos 6 endpoints; ULTRA EN CONSTRUCCIÓN; cuarentena SHA-256; `next build` rc=0 | `2872c8597` |
| B15 | higiene sostenible de agentes agy (`scripts/orq/`, OPERACION_AGENTES.md) | ACEPTA; 5 tests reales (agy_matar protege pesados + ancestros); mcp_vacio; censo JSON; lanzador con medición de hijos | `500f85031` |
| B16 | localhost de ULTRARENTABLE en el PC (`web_local.ps1`, 3100/8100, BACKEND_URL) | ACEPTA; tsc rc=0; valores por defecto intactos; el agente arrancó, comprobó y paró la instancia | `c294b51ca` |
| B06 | config B de SQX (A/B) + build headless (W3.2) | **RECHAZA ×2** (13:50 y 17:05): 1ª ronda el build no se ejecutó; 2ª ronda arrancó con `NumberFormatException: "auto"` en la config de datos y ranking Fit Portfolio sin databank, 0 estrategias en 31 min, proceso parado por el ORQ tras 2 h a 4 núcleos; ambos informes dijeron PASA con causa inventada. Vale: config B, tabla A→B, export ES 15m. `CORRECCION_2` en vuelo (3ª y última ronda); decisión en VENTANA_EMILIO §6 | — |
| A02 | refutador del arnés | ACEPTA; 7/10 bloqueos; agujeros de cliente documentados; k5: el agente puede ampliar su TERRITORIO → **D16** | `552ce5c11` |
| B13 | W4.2-bis candado del discovery | ACEPTA; aviso explícito sin fcntl; resto se propaga | `405ff4095` |

**Decisión D16 (nace de A02):** los bypass de cliente (`--no-verify`, `-c core.hooksPath`, `ORQ_COMMIT=1`
puesto por el agente) no se pueden impedir con hooks; la soberanía está en la aceptación: el arnés
exige **0 commits del agente sobre la base** y **GO íntegro** (TERRITORIO/ACEPTACIÓN/RIESGO idénticos a
HEAD; solo se toleran `## CORRECCION_n` al final). Lo implementa B14 (#29).

**Incidente 13:02 UTC:** Orca se auto-actualizó (`orca-windows-setup`; `Orca.exe` desapareció ~5 min).
Los workers sobrevivieron en `orca-terminal-daemon`; los despachos siguieron válidos; el CLI nuevo
imprime una línea de `crashpad` por stderr (parsear con `2>/dev/null`). `main` publicado
`ef1d8ed37..29b37ba72` con B02/B05/B07/B08 (37 tests verdes).

**Decisión D15 (nace de E1):** la pregunta "¿dato o edge?" para la familia `reversion` de ES queda
respondida: **es edge** (la familia no tiene ventaja bruta). E2 (B03, en vuelo) lo mide sobre las 6
familias con espacio completo; si confirma `AGOTADA` por familia, el siguiente paso es **W3.4 (diseño
de familias nuevas, tarea del ORQ)** y el carril SQX (B06), no más barridos de parámetros.

En vuelo a 17:15 (todos en agy limpios, 0 hijos): B03 CONTINUACION `ctx_b4973eb21529` (E2 5m corriendo bajo gobernanza desde las 14:01 UTC, latidos cada 4 min) y B06 CORRECCION_2 (3ª ronda SQX, acotada). Integrados hoy: B10, B14, B12, B17, B15, B16. Pendiente: B04 (tras B03). Localhost de ULTRARENTABLE: `scripts/orq/web_local.ps1 -Arrancar` desde devilray → http://localhost:3100 (web producción) + http://127.0.0.1:8100 (API); el túnel sshd 3000/8000 al VPS no se toca. Limpieza de Orca: 46 workers muertos liberados; 18 registros de runs anteriores no cambian de estado (sus terminales ya no existen).

**Ola B (adaptativa) lanzada a 12:35 UTC** con contratos en `GO_B02/B03/B05/B07/B08/B09/B11.md`
(`cd94632c9`): B02 = E1 (20 REVERSION_ATR de ES en 5m/15m con 5.18.0), B07 improvement, B08 meta,
B09 catálogo v2, B05 parser .sqx, B11 inventario/consolidación; B03 (E2) tras B02; B04/B06/B10/B12
al aterrizar sus dependencias. Guarda de máquina: RAM <78 % y CPU real <80 % entre lanzamientos;
un solo proceso pesado a la vez vía `gobernanza_recursos` (ya operativa en Windows). Cada aterrizaje: `aceptar_agy.py` (A01) o auditoría manual → veredicto →
`git merge --no-ff` en devilray con `ORQ_COMMIT=1` → al cerrar la ola, `main` ← devilray (ff).
Informes: `orchestration/results/agy/<ID>.md`. Despachos: Panel de agentes y Tareas de Orca.

## 4. Deuda y bloqueos vivos

| Bloqueo | Estado real |
| :--- | :--- |
| Puerta de admisión en Windows | ✅ A03 integrada: `gobernanza_recursos estado/ejecutar` funciona; los agentes siguen pidiendo `ask` antes de lo pesado y el ORQ concede uno a la vez (registro en el scratchpad `semaforo_pesados.txt`) |
| VPS saturado / licencia SQX (05-09) / Firebase / pregunta 5.2 | ⏳ `VENTANA_EMILIO.md` (sin cambios; sigue siendo lo único que necesita a Emilio) |
| Datos ES/YM/NQ 5m-15m en el PC | ✅ ya estaban consolidados en `data/normalized` del checkout principal y verifican 176/176 con hash de contenido (A04); B11 hace el inventario del resto (GC/SI/CL/forex) |
| Deuda W4.2-bis | ❌ `except (ImportError, OSError): pass` mudo en `discovery_validation_pipeline._acquire_singleton_lock` (A10); corregir en Ola B |
| Capacidad del PC | ✅ **D17 (13:45): los agentes salen ligeros.** Un `agy` recién arrancado cargaba 18-20 procesos hijo (1,4-1,5 GB: gbrain/bun, shadcn, firebase, stitch, supabase, playwright, chrome-devtools, tradingview, notebooklm, obsidian, github) aunque `agy mcp list` los mostrara `disabled`: la CLI 1.1.24 ignora `disabled`. Arreglo verificado: `~/.gemini/config/mcp_config.json` **y** `~/.gemini/antigravity-ide/mcp_config.json` vaciados a `{"mcpServers": {}}` (backups `mcp_config.backup_ORQ_12srv_20260902.json` junto a cada uno); agy nuevo = 0 hijos / 209 MB. Riesgo: el IDE de Antigravity (abierto desde las 13:10) reescribió ambos ficheros a las 13:30:52 con los 12 servidores; si vuelve a hacerlo, repetir el vaciado. Regla: ≤6-7 agentes; cerrar terminales al integrar (`terminal stop --worktree path:<ruta>`); los agentes arrancados con la config vieja se cierran al aterrizar, no se reutilizan |

---

## Histórico anterior

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

> **Segunda corrección de §3.2 (ciclo 2, 21:30) — y esta vez la detecta un subagente, no yo.** El
> carril GATES (`results/W43_spec_registro_gates.md` §4) demuestra que mi "medición correcta" de
> arriba también estaba mal planteada: los 19 ficheros importan
> `services.validation.engine.event_backtest_engine` (el **motor**) y
> `services.validation.certification_registry`, **no la suite A de gates**
> (`services.validation.engines`, con "s"). Re-medido con mis comandos: de los 20 ficheros que
> importan la suite B, **ninguno** importa `services.validation.engines`; la suite A tiene **un
> único importador externo** (`services/validation/validation_router.py`) y **cero consumidores en
> `apps/web`**. Conclusión honesta: **las dos suites NO están entrelazadas en los mismos ficheros**;
> mi primera versión ("REFUTADO") tenía razón en el dato y se equivocaba en la conclusión, y mi
> "corrección" se equivocaba en el dato. El problema real es otro, y más simple: (1) la suite que
> certifica (B) vive dentro del monolito `api` con 19 importadores; (2) **las dos suites divergen
> en los 11 gates** (en 4 de ellos con fórmulas distintas bajo el mismo nombre); (3) el catálogo
> que ve la web (`contracts/gate_directory.py`) no coincide con la suite que certifica en ningún
> gate — el caso grave es el gate 10: la web dice 75, el corte real es 40. "Mejorar solo las
> puertas" sigue siendo imposible hoy, por esas tres razones. Y el Movimiento 1 sale **más barato**
> de lo que estimaba I7 §7.2: A se cuarentena detrás de un adaptador con 1 importador; B conserva
> su ruta de import por re-export. Decisión D5 (umbrales) en
> `reviews/investigacion_I7_arquitectura_codigo.md` §7.4.

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

## 8. Presupuesto de máquina — corrección del ciclo 2 (Emilio: "va lento, quizás sobrecargas")

Medido: CPU al **100 %** con la ola 2 lanzada como workflow de 6 agentes en paralelo (cada uno
con pytest/build), más el backfill Dukascopy, más herramientas ajenas al proyecto corriendo a la
vez (Orca ×3 con 1 GB, Antigravity IDE ×14 procesos, NordVPN) y un `TextInputHost` de Windows
desbocado con 4.452 s de CPU.

Aplicado: (1) workflow parado y relanzado con **semáforo de 2 agentes** (doctrina §2: "si Emilio
está usando el PC, la mitad"), tests solo del propio carril, un único `npm run build`, SQX capado
a ≤4 núcleos antes de cualquier build; (2) `TextInputHost` reiniciado (Windows lo relanza: 4.452 s
→ 4 s). Resultado: 100 % → 65 % con el workflow en marcha. Lo que queda es de Emilio (Orca /
Antigravity) y no se toca. Regla desde ahora: **2 agentes + 1 NOHUP mientras el PC esté en uso.**

---

## 9. Ciclo 2 (21:00-22:00) — aterrizajes auditados y decisiones D5-D9

**Ola 2 en marcha con semáforo de 2** (workflow `wf_32b93e71`, 8 carriles, pipeline
investigar → 3 refutadores → implementar → aceptación+3 revisores). Aterrizajes de la etapa
"investigar" auditados con comandos propios del orquestador (todas las afirmaciones clave
reproducidas; las discrepancias, anotadas):

| Carril | Informe | Auditoría ORQ | Lo que cambia |
| :--- | :--- | :--- | :--- |
| GATES | `results/W43_spec_registro_gates.md` | CONFIRMADO (gate 10: 40 real vs 75 web; 11/11 divergen; 1 importador de A). **Me corrige a mí** (§3.2) | D5; W4.7 |
| MEJORA | `results/I2_diseno_mejora.md` | CONFIRMADO (fabricación en `deep_strategy_improver`, `trials_tested=iteration`, blind OOS dentro del bucle, `venue=BINGX`) | cuarentena hecha; W3.5.b; W2.8 |
| META | `results/I3_diseno_meta.md` | CONFIRMADO salvo un matiz: `portfolio_engine` no es "huérfano total" — lo exporta `services/portfolio/__init__.py` y lo usa un test multi-módulo (ningún código de producción lo usa) | W6.0; D8; pregunta 5.2 a Emilio |
| FONDEO | `results/M3_plan_catalogo_firmas.md` | CONFIRMADO (5 catálogos, ruta Linux en `/research-doc`, `verified_at` repintado, consistencia 40/30 en el motor) | D6, D7; W4.8, W4.9, W5.8 |

**Decisiones del orquestador** (las peticiones que los carriles no podían decidir):

- **D5 — umbrales canónicos**: registro v1 = paridad exacta con la suite B; `gate_directory.py`
  regenerado desde B; reconciliación con criterio 1.1 después, gate a gate, con bump (I7 §7.4).
- **D6 — dato no verificable en el catálogo de firmas**: el valor raíz es `None` **y** se conserva
  un `SourceRef(confidence="unverified", url=None, note=...)` para distinguir "buscado y no
  encontrado" de "nunca buscado". Test: valor distinto de None ⇒ confidence en {fetch, ws_official}
  y url no vacía. Nunca `url=""`.
- **D7 — página `/prop-firms`**: muestra el catálogo v2 verificado; cupones/afiliados fuera hasta
  re-verificarse aparte (W5.8). No se mete la parte comercial en `PROP_FIRM_CATALOG`.
- **D8 — fabricadores meta**: `portfolio_engine.py`, `portfolio_combiner.py`,
  `factory/portfolio_sprint_engine.py`, `factory/ultra_portfolio_engine.py` a cuarentena con sus
  tests dedicados; el daemon meta se retira del arranque (W6.0). `services/meta/` nace de
  `meta_strategy_pipeline` + `meta_ensemble_service` (los dos vivos y REAL-ONLY).
- **D9 — meta FONDEO sin router hasta que Emilio conteste 5.2**: asignación estática (HRP +
  mínima varianza del examen); el router queda diseñado, no construido.
- **D10 — motor 5.18.0 (regla #26)**: el FORENSE encontró un bug de DST (sesión fija 13:30 UTC; 1 de cada 3 días desplazado 1 h) y que `funding_discovery` pone la ventana RTH a las 6 familias. Reproducido por el ORQ (picos 14:30/13:30 UTC en ene/jul; 381/1.141 días). Contrato `state/contratos/W29_motor_5_18_sesiones_dst.md`: hora local + `zoneinfo`, familias A/B/D con Globex + flat 15:10 CT (no `None`, porque Topstep exige flat diario), bump + baseline F02 nuevo. **E1/E2 quedan etiquetadas 'sesión sin DST' y se repiten con 5.18.0.** Mi hipótesis del `volume` por defecto quedó REFUTADA con datos (volumen real, 0 ceros).
- **W0.7 hecho**: `main` local == remoto (`df3906745`), rebase limpio sobre el commit de Hermes
  (15 manifiestos NQ 2026 verificados byte a byte); `origin/tmp-sync` intacto (22 commits/829
  ficheros de datos por reconciliar: tarea aparte, no se toca sin verificar).
- **Datos**: W1.7 (backfill degradante, parado), W1.8 (YM+NQ+XAU rescatados del VPS 155/155),
  YM y NQ consolidados 5m/15m (0 conflictos). El backfill no se relanza hasta arreglar W1.7.

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
