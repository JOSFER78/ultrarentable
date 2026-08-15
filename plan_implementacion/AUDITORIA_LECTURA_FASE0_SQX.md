# AUDITORIA LECTURA FASE 0 — SQX, CFX, Datos y Databanks (Agente C)

> **Proyecto:** Ultrarentable (Trading Cuantitativo Multi-Motor)  
> **Fecha de auditoría:** 2026-08-15  
> **Doctrina:** REAL-ONLY (verificado contra el filesystem y binarios del VPS)  
> **Auditor:** Agente C (SQX / CFX / Datos / Databank)

---

## 1. Verificación del Backup Crítico del CFX

| Archivo de Backup | Ubicación en Disco | Tamaño | Integridad |
|---|---|---|---|
| `project.cfx` (Pre-reconfig) | `/home/ubuntu/backups/ultrarentable/pre_reconfig_20260809_105641/project.cfx` | 26.380 bytes | ✅ Verificado (ZIP válido con `config.xml` y `Build-Task1.xml`) |
| Tarball completo | `/home/ubuntu/backups/ultrarentable/backup_20260809_103910.tar.gz` | 81.645 bytes | ✅ Verificado (incluye CFX y BD SQLite de 434 KB) |

---

## 2. Diagnóstico Exacto del XML en `Build-Task1.xml` (10 Cambios)

Inspección realizada extrayendo `Build-Task1.xml` (1.225.608 caracteres) del CFX actual en `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx`:

| # | Parámetro | Estado en XML Actual | Estado Requerido (Fondeo) | Diagnóstico |
|---|---|---|---|---|
| 1 | **EvoInSamplePeriod** | `<EvoInSamplePeriod ratio="70" />` | `ratio="70"` | ✅ **APLICADO** |
| 2 | **CrossChecks Master** | `<CrossChecks use="true">` | `use="true"` | ✅ **APLICADO** |
| 3 | **MonteCarloRetest** | `<MonteCarloRetest use="true">` | `use="true"` (20 simulaciones) | ✅ **APLICADO** |
| 4 | **OptProfileSysParamPermutation** | `<OptProfileSysParamPermutation use="true">` | `use="true"` | ✅ **APLICADO** |
| 5 | **Chart Spread** | `spread="30"` | `spread="30"` (0.3–3 USD real Binance) | ✅ **APLICADO** |
| 6 | **Chart Slippage** | `slippage="3"` | `slippage="3"` (3 pips real) | ✅ **APLICADO** |
| 7 | **WalkForwardOptimization** | `<WalkForwardOptimization use="false">` | `use="true"` + `period="5"` `optimization="20"` | ❌ **PENDIENTE** |
| 8 | **Ranking / Fitness** | `Rankings type="never"` / `Ranking type="NetProfit"` | `Rankings type="always"` + `ReturnDDRatio` + gates | ❌ **PENDIENTE** |
| 9 | **Filtro de Sesión** | `<Param key="Session">No Session</Param>` | Sincronizado (`LondonNY` o justificado 24/7) | ❌ **PENDIENTE** |
| 10 | **PopulationSize** | `<PopulationSize>80</PopulationSize>` | Tamaño controlado según objetivo | ❌ **PENDIENTE** |

**Balance:** Exactamente **6 cambios aplicados** y **4 cambios pendientes** (los 4 bloqueados previamente por indentación en el formateo de clases Java SQX).

---

## 3. Series de Datos Históricos en SQX (`user/data/History/`)

Inspección directa de `/home/ubuntu/StrategyQuantX/user/data/History/`:
- **BTCUSDT_AUTO:**
  - Archivo: `BTCUSDT_AUTO/BTCUSDT_AUTO_H1.dat` (153.479 bytes).
  - Número de barras: **3.840 barras H1**.
  - Rango de fechas: `2026.02.26` a `2026.08.04` (~5,2 meses).
  - **NO existen datos M1, M5 ni ticks de BTC** en disco.
  - Precisión de backtest en CFX: `testPrecision="1"` (OHLC de barra H1; bar magnifier M1 correctamente desactivado).
- **SPY D1:**
  - Archivo de referencia predeterminado en `sq_equity` (8.572 barras, 1993–2026), no utilizado por la búsqueda de crypto.

---

## 4. Estado de Conectividad SQX MCP / Databanks

- **Estado del Servidor SQX:** 🔴 **OFFLINE**
  - El puerto 8080 del host no responde a la API SQX MCP porque está ocupado por un servicio Python ajeno (`MoneyPrinterTurbo`, PID 84200).
  - El servicio systemd `strategyquantx.service` está estático/deshabilitado tras limpieza previa.
- **Databanks en Disco (`user/projects/Ultra_Auto_Pilot/databanks/`):**
  - Existen los directorios: `Results`, `Results_20260809_032803`, `Results_robust_20260809`, `Existing portfolio`, `Initial population`, `Last generation`.
  - Conteo actual de archivos `.str` en disco: **0 archivos** (databanks limpios listos para recibir salida de nueva búsqueda).
  - El backup `ultrarentable.sqlite3` del 2026-08-09 10:39 preserva los registros de las 30 estrategias y 29 backtests históricos analizados.
