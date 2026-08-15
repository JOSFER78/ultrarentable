# CFX FONDEO APLICADO — Registro de Cambios XML en StrategyQuant X

> **Proyecto:** Ultrarentable · **Fecha:** 2026-08-15  
> **Fichero Modificado:** `/home/ubuntu/StrategyQuantX/user/projects/Ultra_Auto_Pilot/project.cfx`  
> **Backup Crítico:** `/home/ubuntu/backups/ultrarentable/pre_reconfig_20260809_105641/project.cfx` y `project.cfx.pre_fase2_20260815_1633`  
> **Doctrina:** REAL-ONLY · **Validación:** Sintaxis XML 100% válida, ZIP testzip verificado.

---

## 1. Tabla de los 10 Cambios Aplicados (Antes vs Después)

| # | Parámetro / Módulo | Valor Anterior (Kamikaze Overfit) | Valor Aplicado (Fondeo Anti-Overfit) | Razón Técnica |
|---|---|---|---|---|
| 1 | **Rankings & Fitness** | `type="never"`, `Ranking type="NetProfit"`, sin condiciones | `type="always"`, `Ranking type="ReturnDDRatio"`, `#trades>=50`, `MaxDD%<=35` | Premia consistencia y ratio retorno/riesgo; descarta de inmediato estrategias ruinosas. |
| 2 | **EvoInSamplePeriod** | `ratio="100"` (100% In-Sample) | `ratio="70"` (70% IS / 30% OOS) | Reserva un 30% OOS dentro de la evolución genética para evitar memorización de ruido. |
| 3 | **CrossChecks Master** | `use="false"` | `use="true" evaluateAll="false"` | Activa la matriz de verificación cruzada multietapa. |
| 4 | **Walk-Forward (WFO)** | `use="false"`, `period="10"`, `optimization="15"` | `use="true"`, `period="5"`, `optimization="20"`, `WFPct>=70%` | WFO viable con 5,2 meses de H1 (5 folds); exige ≥70% de ejecuciones rentables. |
| 5 | **Monte Carlo Retest** | `use="false"` (luego 10 sims) | `use="true"`, `NumberOfSimulations="20"` | Evalúa 20 trayectorias aleatorias de slippage y spread antes de aceptar. |
| 6 | **Permutación SPP** | `MaxTests="1000"` | `use="true"`, `MaxTests="100"` | Análisis de meseta de parámetros para evitar picos frágiles aislados. |
| 7 | **Spread BTC** | `spread="0"` (irreal) | `spread="30"` (30 pips ≈ $0.3–$3.0) | Coste de transacción real en Binance/BingX perps. |
| 8 | **Slippage BTC** | `slippage="1"` | `slippage="3"` (3 pips) | Deslizamiento realista en órdenes de mercado. |
| 9 | **Filtro de Sesión** | `LimitTimeRange="false"`, `Session="No Session"` | `LimitTimeRange="true"`, From `25200` (07:00 UTC), To `75600` (21:00 UTC), `Session="LondonNY"` | Concentra la operativa en las sesiones de mayor volumen y liquidez (Londres + NY). |
| 10 | **Población Genética** | `PopulationSize="80"`, `MaxGenerations="40"` | `PopulationSize="100"`, `MaxGenerations="60"` | Mayor capacidad de exploración genética controlada sin sobreajuste. |

---

## 2. Verificación de Integridad en Disco

- **Archivo `project.cfx`:**
  - Tamaño final: **26.444 bytes**
  - Entradas ZIP: `config.xml` (734 bytes) y `Build-Task1.xml` (1.226.790 bytes)
  - Validación sintáctica: Árbol XML parseado exitosamente sin errores de schema o etiquetas no cerradas.
- **Backups preservados:**
  - `/home/ubuntu/backups/ultrarentable/pre_reconfig_20260809_105641/project.cfx` (26.380 bytes)
  - `/home/ubuntu/backups/ultrarentable/project.cfx.pre_fase2_20260815_1633` (26.347 bytes)
