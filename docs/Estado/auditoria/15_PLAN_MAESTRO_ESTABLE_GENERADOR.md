# PLAN MAESTRO ESTABLE — Generador de Balas Ultrarentables (SQX)

> **Proyecto:** 01 Ultrarentable · **Fecha:** 2026-08-09
> **Origen:** Consolidación de 4 análisis paralelos (A1-A4) verificados contra el XML real.
> **Doctrina:** REAL-ONLY, anti-overfit, el generador no es su propio validador.
> **Principio rector (usuario):** *"Si partes de un plan malo, todo va a salir mal."* Por eso este plan se construye sobre análisis, no sobre intuición.

---

## 0. Documentos fuente (todos verificados en disco)

| Código | Documento | Rol |
|---|---|---|
| A1 | `11_analisis_viabilidad_datos.md` | Define qué WFO/OOS es defendible con los datos reales |
| A2 | `12_analisis_reconfiguracion_xml.md` | Cambios XML exactos validados para SQX 144 |
| A3 | `13_especificacion_generador_ideal.md` | **Contrato** de "cómo debe comportarse el generador" |
| A4 | `14_analisis_antioverfit.md` | Capa anti-overfit (gates, MC, SPP, promoción) |

---

## 1. Realidad verificada (no supuestos)

**Datos en el Data Manager de SQX hoy:**
- **BTCUSDT H1**: 3.840 barras (26-feb → 4-ago 2026, ~5.2 meses). Es el símbolo del proyecto.
- **SPY D1**: 8.572 barras (1993 → 2026, 33 años). No usado por el proyecto.
- **NO hay M1/M5/ticks de BTC** en disco.
- La conexión Binance USDT-M está cargada (puede traer desde 2017 en futuro, si se autoriza).

**Config actual del generador (`Build-Task1.xml`, verificado):**
1. `Ranking type="NetProfit"` — premia curvas frágiles. ❌
2. `EvoInSamplePeriod ratio="100"` — evoluciona 100% IS, ciega al OOS. ❌
3. `<CrossChecks use="false">` — todos los cross-checks apagados (WFO, MC, SPP). ❌
4. `<Chart spread="0">`, `slippage="1"` — costes irreales para BTC. ❌
5. Sin filtros de sesión/régimen (`Session="No Session"`, sin London/NY). ❌

**Consecuencia real ya registrada en BD:** `Strategy 1.1.43` PF_IS 1.56 / PF_OOS 0.80 — el caso más claro de curve-fit.

---

## 2. Decisión clave: validación con los datos actuales (5.2 meses BTC H1)

**Hallazgo A1 (matemático):** Con 3.840 barras H1 **no se puede** hacer un WFO de 6-10 folds con significancia. Un fold de 6.4 días da 3-4 trades = ruido. El objetivo de 150+ trades OOS del Perfil A es **imposible** en 5 meses sin sobreajustar a ruido de alta frecuencia que muere en real por costes (0.08-0.15% round-trip).

**Configuración de validación DEFENDIBLE hoy:**
- **Split IS/OOS 75/25** (IS: 26-feb→22-jun; OOS: 22-jun→4-ago) — modo principal.
- Alternativa: WFO 2 folds / 25% OOS.
- **Trades OOS ≥ 20** (no 150), **Trades totales ≥ 60**.
- PF_OOS ≥ 1.20, Expectancy > 0.15%/trade.

> **Nota de reconciliación:** los umbrales estrictos de A3/A4 (trades OOS≥50, PF_OOS≥1.40, Ret/DD≥3) se aplican en los **gates de la API/BD** y se activarán **al completo** cuando exista histórico ampliado (fase futura). El generador HOY no se ahoga en un umbral inalcanzable, pero la validación final sigue siendo estricta.

---

## 3. La plantilla objetivo: cambios XML exactos a `Build-Task1.xml`

Reemplazos verificados textualmente (todos existen en el XML real, uno a uno ✅). Entran dentro de `project.cfx` (ZIP) → `Build-Task1.xml`:

| # | Fragmento actual | Fragmento nuevo | Por qué |
|---|---|---|---|
| 1 | `Rankings type="never"` + `Ranking type="NetProfit"` | `Rankings type="always"` + `Ranking type="ReturnDDRatio"` + condiciones `#trades>=100`, `MaxDD%<=35` | Premia retorno/riesgo, filtra en generación. Clase nativa SQX. |
| 2 | `EvoInSamplePeriod ratio="100"` | `ratio="70"` | Reserva 30% OOS dentro de la evolución → evita memorizar ruido. |
| 3 | `<CrossChecks use="false">` | `use="true"` | Activa la matriz anti-overfit. |
| 4 | `<WalkForwardOptimization use="false"> period="10" optimization="15"` | `use="true"` + `period="5"` `optimization="20"` + accept `WFPctOfProfitableRuns>=70` | WFO viable en 5 meses; exige ≥70% runs rentables. |
| 5 | `<MonteCarloRetest use="false">` | `use="true"`, `NumberOfSimulations=20`, randomized slippage/spread/params | Robustez frente a variaciones de ejecución. |
| 6 | `<OptProfileSysParamPermutation use="false">` | `use="true"`, `MaxTests=100` | Verifica meseta de parámetros (anti picos frágiles). |
| 7 | `<Chart spread="0">` | `spread="30"` | Coste realista BTC Binance (30 pips ≈ $0.3-3). |
| 8 | `slippage="1"` | `slippage="3"` | Slippage realista. |
| 9 | `LimitTimeRange false` + `Session="No Session"` | `LimitTimeRange true`, From 25200 (07:00), To 75600 (21:00), `Session="LondonNY"` | Evita baja liquidez; filtra a mejores horas. |
| 10 | `PopulationSize=80 MaxGen=40` | `PopulationSize=100 MaxGen=60` | Más exploración (recomendado perfil A). |

**Corrección de orquestador al A2 (importante):**
- A2 proponía `testPrecision="2"` (M1 bar magnifier) y activar a fondo `RetestWithHigherPrecision`. **NO se aplica** en esta fase: no hay datos M1 de BTC en disco, y el usuario dijo no descargar. SQX con precisión M1 sin datos M1 fallaría o degradaría. Se mantiene `testPrecision="1"` y el `RetestWithHigherPrecision` se deja como está apagado hasta que existan datos M1. (Coherente con A1 y con la restricción del usuario.)
- El `RetestWithHigherPrecision` ya estaba `use=true` pero apagado por el master; al activar el master, se **dejará deliberadamente `use=false`** su sub-bloque para no pedir M1 inexistente.

---

## 4. Orden de ejecución (fases planificadas, cada una con verificación)

### Fase 0 — Backups y preparación (YA HECHO ✅)
- Backup de `project.cfx`, `ultrarentable.sqlite3` y databank en `/home/ubuntu/backups/ultrarentable/` (verificado, 81KB). ✅
- Confirmado: el databank `Results_20260809_032803` tiene candidatos; se renombrará para salida limpia.

### Fase 1 — Aplicar plantilla robusta (momentánea, con verificaciones)
1. Desempaquetar `project.cfx` → aplicar los 10 reemplazos a `Build-Task1.xml`.
2. Empaquetar de nuevo (ZIP válido).
3. **Redirigir databank de salida** a uno nuevo (`Results_robust_20260809`) para no re-ingestar lo viejo (patrón skill sqx-automation).
4. Verificar: `zip -T`, tamaño, y que los 10 cambios están textualmente en el ZIP nuevo.

### Fase 2 — Reiniciar servicio SQX (recargar CFX)
- `systemctl --user restart strategyquantx` → confirmar `is-active ACTIVE` y `/sqx/status` ONLINE.
- Regla: el `.cfx` editado solo se recarga en memoria tras reiniciar el servicio.

### Fase 3 — Ejecutar el generador
- `POST /api/v1/sqx/projects/Ultra_Auto_Pilot/run` (o MCP `run_project`).
- Esperar y muestrear `list_strategies` / `get_strategy_stats`.

### Fase 4 — Gate de calidad (lo que separa balas de ruido)
- Aplicar gates A4 en la ingesta (devuelve pocos o ninguno → NORMAL, la regla del pulgar):
  - `PF_IS >= 1.30`, `PF_OOS >= 1.20`, `Ratio PF_OOS/PF_IS >= 0.70`
  - `Trades_OOS >= 20` (ajustado a datos actuales), `Trades_Total >= 60`
  - `MaxDD% <= 20`, `Ret/DD >= 2.0`, DD convertido de USD a %.
- Esperar rechazo masivo (1-2% pass rate). Si la lista sale grande → el gate está mal.

### Fase 5 — Promoción y 2º motor (fuera de esta sesión de configuración)
- Los que pasen → `SQX_CANDIDATE` → revalidación NautilusTrader → `CANONICAL`.
- No se ejecuta aquí; se documenta como siguiente hito.

---

## 5. Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|---|
| Activar WFO/MC/SPP ralentiza el run | Aceptable; la calidad > velocidad. Squad de generación paramétrica. |
| `ReturnDDRatio` no reconocido | Verificado como clase nativa SQX 144 (`com.strategyquant.databank.columns.ReturnDDRatio`). |
| Sin M1 → Bar Magnifier falla | Decisión: NO activar precisión M1 (corrección arriba). |
| Databank lleno → run hace nada | Redirección a databank nuevo + `passedStrategies=200` ya en CFX + restart. |
| Costes optimistas | `spread=30`, `slippage=3`, comisión 0.05% taker — realistas Binance. |

---

## 6. Criterio de éxito (verificable)

El generador produce candidatos que **sí pasan los gates** (PF_OOS≥1.20, ratio OOS/IS≥0.70, trades OOS≥20, DD%)
que la **config actual (fitness NetProfit + cross-checks OFF) no producía** — o bien produce 0-2 balas, que según la doctrina es el resultado correcto y esperable (las balas son raras).

---

*Plan consolidado y verificado por el orquestador. Los cambios XML son aplicables de forma limpia según validación sintáctica y textual contra el fichero real.*
