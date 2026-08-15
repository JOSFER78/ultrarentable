# PLAN MAESTRO DE EXPLOTACIÓN MÁXIMA AL 100% DE STRATEGYQUANT X (SQX) EN ULTRARENTABLE

**Proyecto:** 01 Ultrarentable  
**Ubicación:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/Estado/auditoria/17C_PLAN_100_PORCIENTO_SQX.md`  
**Fecha:** 2026-08-11  
**Doctrina:** REAL-ONLY, automatización integral sin intervenciones manuales ni degradación de rigor, alineado con el plan 15 (`15_PLAN_MAESTRO_ESTABLE_GENERADOR.md`) y la auditoría de verificación 17 (`17_verificacion_xml.md`).

---

## 1. ESTADO REAL Y EVIDENCIA EMPÍRICA VERIFICADA

### 1.1 Entorno de Ejecución e Infraestructura SQX
- **Instalación:** `/home/ubuntu/StrategyQuantX` en VPS Linux (Kernel 6.17-oracle).
- **Servicio Systemd:** `strategyquantx.service` (User service en modo headless con `DISPLAY=:99` vía Xvfb).
- **Interfaz Web UI:** `http://127.0.0.1:5050` (HTTP 200, CORS `*`).
- **Servidor MCP HTTP JSON-RPC:** `http://127.0.0.1:8080/mcp` (6 herramientas expuestas: `list_projects`, `list_databanks`, `list_strategies`, `get_strategy_stats`, `run_project`, `stop_project`).
- **Resguardo Crítico Verificado:** `/home/ubuntu/backups/ultrarentable/pre_reconfig_20260809_105641/project.cfx` (archivo ZIP original intacto de 26.3 KB).

### 1.2 Proyectos y Databanks Verificados (Inspección MCP Real)
El servidor MCP respondió estado **ONLINE** con `session_id: fac113e4-151c-4648-a66f-d5c99ce22224`.
Proyectos detectados en el sistema: `['PortfolioMaster', 'PortfolioComposer', 'Optimizer', 'Builder', 'Ultra_Auto_Pilot', 'Ultra_Improve_Pilot', 'Retester']`.

- **`Ultra_Auto_Pilot`**:
  - Estructura ZIP: `config.xml` (734 bytes) + `Build-Task1.xml` (1,225,608 bytes).
  - Databanks detectados: `Results_robust_20260809` (0 estrategias), `Last generation` (0), `Initial population` (0), `Strategies to improve` (0), `Results` (0), `Existing portfolio` (0).
- **`Ultra_Improve_Pilot`**:
  - Estructura ZIP: `config.xml` (653 bytes) + `Build-Task1.xml` (1,225,736 bytes).
  - Databanks detectados: `Results` (0 estrategias), `Last generation` (0), `Initial population` (0), `Strategies to improve` (0), `Existing portfolio` (0).

### 1.3 Parámetros Extraídos Real-Time de los CFX Activos (`zipfile`)
- **`Ultra_Auto_Pilot/project.cfx`**:
  - `StrategyType`: `<StrategyType type="simple" additionalCharts="0" templateFile="SQ3StrategyTemplateExample.sq4" architecture="sq4" />`
  - `BuildMode`: `generationType="genetic-evolution"`, `PopulationSize=80`, `MaxGenerations=40`.
  - `WalkForwardOptimization`: `use="false"`, `period=10`, `optimization=15`.
  - `MonteCarloRetest`: `use="true"`, `RandomizeHistoryData`.
  - `OptProfileSysParamPermutation`: `use="true"`, `MaxTests=1000`.
  - `Rankings`: `type="never"`, `MaxStrategies=24`, `Ranking type="NetProfit"`.
- **`Ultra_Improve_Pilot/project.cfx`**:
  - `StrategyType`: `<StrategyType type="improve" additionalCharts="0" templateFile="" improveType="databank" strategyFile="" improveDatabank="Strategies to improve" />`
  - `BuildMode`: `generationType="genetic-evolution"`, `PopulationSize=60`, `MaxGenerations=25`.
  - `WalkForwardOptimization`: `use="false"`.
  - `MonteCarloRetest`: `use="false"`.
  - `OptProfileSysParamPermutation`: `use="false"`.
  - `Rankings`: `type="never"`, `MaxStrategies=12`, `Ranking type="NetProfit"`.

---

## 2. MATRIZ MAESTRA DE CAPACIDADES SQX VS VÍAS DE AUTOMATIZACIÓN

### 2.1 Matriz de Integración (Capacidades x Vías)

| Módulo / Capacidad SQX | Vía MCP (8080/mcp) | Vía Mutación CFX (ZIP) | Vía GUI / CDP (Xvfb :99) | Vía Ingest / BD | Prioridad |
|---|---|---|---|---|---|
| **Builder Genético (Simple / Custom)** | Trigger `run_project` / `stop_project` | Reemplazo XML de `BuildMode`, `BuildingBlocks`, Sesiones, Spreads, Rankings | Configuración visual de bloques exóticos y sintaxis de reglas en X-Builder | Lectura vía `list_strategies` e ingesta en `ultrarentable.sqlite3` | **P0** |
| **Improve Generator (Optimizador de Databank)** | Ejecución vía MCP | Mutación de `improveDatabank` y parámetros de mutación local | Inserción manual/CDP de estrategias a mejorar en databank `Strategies to improve` | Ingesta de candidatos perfeccionados | **P1** |
| **Walk-Forward Optimization (WFO)** | Polling de estado durante run | Activación en XML: `<WalkForwardOptimization use="true">` | Inspección visual de la matriz 3D de WFO | Almacenamiento de % WFPctOfProfitableRuns en BD | **P0** |
| **Monte Carlo (MC) & System Parameter Permutation (SPP)** | Transparente tras la generación | Activación XML (`MonteCarloRetest`, `OptProfileSysParamPermutation` MaxTests=100) | Análisis de distribución de retornos | Ingesta de métricas de resiliencia | **P0** |
| **Portfolio Composer & Master** | No expuesto directamente en MCP | Mutación de `AutomaticPortfolioBuilder-Task1.xml` | Creación y filtrado de portafolios descorrelacionados | Ingesta de portafolios agrupados como metas-estrategias | **P1** |
| **Custom Indicators & Code Editor** | N/A | Inyección de archivos `.java` / `.class` en `/home/ubuntu/StrategyQuantX/user/code/` | Compilación y depuración de código Java custom | Persistencia de indicadores en DSL JSON | **P2** |
| **Retester (Multi-Mercado / Cross-Check)** | Trigger `run_project("Retester")` | Mutación de `Retest-Task1.xml` (símbolos secundarios, timeframes) | Visualización de equity curves multi-asset | Ingesta de matriz cross-market | **P1** |

---

## 3. IDENTIFICACIÓN DE RIESGOS Y ESTRATEGIAS DE MITIGACIÓN

| Riesgo Detectado | Causa Raíz (Empíricamente Demostrada) | Severidad | Estrategia de Mitigación Concreta |
|---|---|---|---|
| **Databank-Full Lockup ("Do Nothing")** | `StopCondition databank-full` (e.g. `passedStrategies=24`). SQX finaliza en 300ms sin explorar si el databank ya tiene 24 estrategias. | **CRÍTICA (P0)** | 1. Redireccionar databank en `config.xml` a `Results_<timestamp>` (`templates/cfx_manipulator.py`).<br>2. Elevar `MaxStrategies` a 200.<br>3. Reiniciar servicio systemd (`systemctl --user restart strategyquantx`) tras mutar el CFX. |
| **EvoStagnation / Convergencia Prematura** | Población pequeña (80/40), `EvoInSamplePeriod ratio=100`, alta presión selectiva. | **ALTA (P1)** | Setear `EvoInSamplePeriod ratio=70`, `PopulationSize=100`, `MaxGenerations=60`, deshabilitar `EvoStagnationRestartGenerations`. |
| **Incompatibilidad de Forma CFX (Instant Abort)** | Mutar un proyecto `improve` con XML de `simple` o viceversa provoca `Estrategias generadas: 0` de inmediato. | **ALTA (P0)** | Preservar strictly las etiquetas de modo (`StrategyType.type`, `BuildMode.generationType`, `improveType`) según el tipo de proyecto. |
| **Explosión Combinatoria por Cómputo (Timeout)** | `MaxTests=1000` en SPP + WFO + MC simultáneos multiplica x10,000 los backtests por candidato. | **ALTA (P1)** | Ajustar `MaxTests=100` en SPP y `NumberOfSimulations=20` en MC. |
| **Corrupción / Error en Base de Datos SQLite** | Bloqueo o desalineación de esquemas en SQLite. | **MEDIA (P1)** | Mantenimiento de backups limpios (`backup_20260809_103910.tar.gz`) y manejo defensivo con `sqlite3` retries. |
| **Overfitting a 5.2 Meses de BTCUSDT** | Intentar WFO de 10 folds con 3,840 barras H1 genera 3-4 trades por fold. | **ALTA (P0)** | WFO 5 folds / 20% OOS, Split IS/OOS 70/30, exigencia de trades totales ≥60 y OOS ≥20. |
| **Unidades de Drawdown Incorrectas (USD vs %)** | SQX entrega Drawdown en USD absolutos en las columnas de databank. | **MEDIA (P0)** | Conversión obligatoria en ingesta (`ingest_sqx_results.py`): `dd_pct = dd_usd / peak_equity * 100`. |

---

## 4. FLUJO OPERATIVO PROPUESTO (CICLO INTEGRAL DE AUTOMATIZACIÓN)

El flujo operativo propuesto es un ciclo cerrado de 7 fases automatizadas sin intervención humana:

```
[1. Mutación CFX en Disco] ──> [2. Reinicio Servicio SQX] ──> [3. Ejecución MCP]
 (cfx_manipulator.py)           (systemctl restart)          (SQXMCPClient.run_project)
                                                                       │
                                                                       ▼
[6. Validación Multi-Motor] <── [5. Ingesta a SQLite] <── [4. Polling & Infección]
 (NautilusTrader Gate)           (ingest_sqx_results.py)     (SQXMCPClient.list_strategies)
         │
         ├──> [Pasa Gates] ──> ESTADO: CANONICAL (Aprobado)
         └──> [No Pasa]   ──> ESTADO: REJECTED (Descartado)
```

### Detalle de Comandos y Scripts Concretos por Fase:

#### Fase 1: Backup y Mutación de CFX
Usa `templates/cfx_manipulator.py` para aplicar las mutaciones en `Build-Task1.xml` y redirigir el databank en `config.xml`:
```python
import sys
sys.path.append('/home/ubuntu/.hermes/skills/trading/sqx-automation/templates')
from cfx_manipulator import backup_cfx, redirect_databank_output
from pathlib import Path

sqx_dir = Path('/home/ubuntu/StrategyQuantX/user/projects')
backup_cfx('Ultra_Auto_Pilot', sqx_dir)
new_db = redirect_databank_output('Ultra_Auto_Pilot', sqx_dir)
print(f'Nuevo Databank asignado: {new_db}')
```

#### Fase 2: Reinicio de Servicio Systemd
Es **OBLIGATORIO** para que SQX recargue la nueva configuración XML desde el ZIP en memoria:
```bash
systemctl --user restart strategyquantx
sleep 5
python3 -c "
import sys
sys.path.append('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/services/sqx_bridge')
from sqx_client import SQXMCPClient
client = SQXMCPClient()
print('Status SQX:', client.check_connection())
"
```

#### Fase 3: Disparo de Generación vía MCP
```python
import sys
sys.path.append('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/services/sqx_bridge')
from sqx_client import SQXMCPClient

client = SQXMCPClient()
res = client.run_project('Ultra_Auto_Pilot')
print('Ejecución iniciada vía MCP:', res)
```

#### Fase 4: Polling y Monitoreo de Estrategias
Muestreo periódico vía MCP sin sobrecargar la CPU:
```python
import sys
sys.path.append('/home/ubuntu/workspace/pro/trading/01 Ultrarentable/services/sqx_bridge')
from sqx_client import SQXMCPClient

client = SQXMCPClient()
strats = client.list_strategies('Ultra_Auto_Pilot', 'Results')
print(f'Estrategias en Results: {len(strats)}')
```

#### Fase 5: Ingesta Automática a BD
Ejecución del script existente `services/sqx_bridge/ingest_sqx_results.py`:
```bash
python3 /home/ubuntu/workspace/pro/trading/01\ Ultrarentable/services/sqx_bridge/ingest_sqx_results.py
```

#### Fase 6: Validación Multi-Motor (NautilusTrader)
Las estrategias marcadas en `validation_status="SQX_CANDIDATE"` son enviadas al motor NautilusTrader para re-evaluación independiente.

#### Fase 7: Promoción o Descarte
Promoción a `CANONICAL` o marcado en `REJECTED` según los gates de calidad (PF_OOS ≥ 1.20, Trades_OOS ≥ 20, MaxDD% ≤ 20%).

---

## 5. PLAN DE ACCIÓN Y ROADMAP POR PRIORIDADES (P0 / P1 / P2)

### P0 (Inmediato - Requisito para Cualquier Operación)
1. **Aplicar los 10 cambios XML verificados** en `17_verificacion_xml.md` sobre `Build-Task1.xml` de `Ultra_Auto_Pilot` (Rankings ReturnDDRatio, IS/OOS 70/30, CrossChecks ON, WFO 5/20, MC 20 sim, SPP MaxTests 100, Spreads/Slippage Binance, Sesión LondonNY, Población 100/60).
2. **Consolidar el script de runner integral** que coordine la secuencia `cfx_manipulator` -> `systemctl restart` -> `SQXMCPClient` -> `ingest_sqx_results`.
3. **Garantizar la corrección de unidades DD** (convertir USD a % sobre capital acumulado/equity) en todos los endpoints de ingesta.

### P1 (Medio Plazo - Optimización y Robustez Multi-Mercado)
1. **Activar el proyecto `Ultra_Improve_Pilot`** con mutaciones localizadas sobre databank `Strategies to improve` para refinar candidatos que hayan superado la fase P0.
2. **Automatizar ejecuciones del proyecto `Retester`** sobre símbolos secundarios (ETHUSDT, SOLUSDT, BNBUSDT) para construir la matriz cross-market.
3. **Integración con `PortfolioComposer`** para ensamblar portafolios multiescenario con correlación < 0.30 entre curvas de equity.

### P2 (Avanzado - Capacidades Custom)
1. **Desarrollo de Custom Indicators en Java** en `/home/ubuntu/StrategyQuantX/user/code/` para incorporar bloques de análisis de liquidez y microestructura.
2. **Exportación directa de código fuente (MQL5 / Python)** para consumo nativo en NautilusTrader sin traducción intermedia.

---

*Plan Maestro 17C redactado y validado en base a datos e infraestructura REALES del VPS. Queda registrado como referencia canónica para la explotación automatizada de StrategyQuant X.*
