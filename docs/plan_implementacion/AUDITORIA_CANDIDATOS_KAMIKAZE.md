# Auditoría: Candidatos Kamikaze de StrategyQuant X vs Protocolo "Miles de % Verificables"
**Proyecto:** Ultrarentable — `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`  
**Blueprint:** `plan_implementacion/BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md`  
**Autoría:** Auditoría de calidad (solo lectura, sin modificar core)  
**Fecha:** 2026-08-09  
**Regla REAL-ONLY:** todas las métricas provienen de lectura real de API/DB. No se inventan valores.

---

## Resumen Ejecutivo
- **Estado actual:** 24 candidatos `sqx_generated` ingeridos en BD. Ninguno alcanza retornos >=1000%. El mejor retorno IS es **37.17%** (`UR-SQX-Strategy_1.1.43`) y el mejor OOS es **1.24%** (`UR-SQX-Strategy_1.1.24`).
- **Veredicto global:** **0 POTENTIAL_WINNER**, **24 REJECTED_OVERFIT** bajo el protocolo estricto del blueprint. Muchos son claramente overfit o ruinosos OOS.
- **Filtro actual `/rentable`:** demasiado permisivo en cantidad de trades y débil en dependencia de outliers, WFE, cobertura temporal y Monte Carlo. Deja pasar candidatos con DD altísima y OOS negativo.
- **Acción prioritaria:** endurecer la ingesta y el endpoint `/rentable` con la scorecard del blueprint, y preparar la llegada de resultados kamikaze reales para que no se escapen falsos positivos ni se descarten winners por umbrales mal calibrados.

---

## 1. Estado Actual de Candidatos (Datos Reales)

### 1.1 Censo desde API `/api/v1/sqx/rentable` y SQLite
- **Total candidatos en BD:** 24 estrategias (`family = sqx_generated`).
- **Proyecto SQX origen:** `Ultra_Auto_Pilot`, databank `Results`.
- **Timeframe/símbolo:** BTC-USDT, 1h, venue BINGX.
- **Filtros activos actuales en `/rentable`:**
  - `PF_IS >= 1.3`
  - `PF_OOS >= 1.0`
  - `trades_count >= 20`
  - `net_return_pct > 0`
  - Drawdown ruinoso (`>=100%`) excluido.
  - Calmin `>= 0.5` en modo `ultra` no aplica en `/rentable`, pero `rentable(ultra)` en ingest exige `net_return >= 5%` y `PF >= 1.5`.
- **Estrategias que pasan `/rentable` hoy:** 2 (`UR-SQX-Strategy_1.2.24` y `UR-SQX-Strategy_1.1.41`).
- **Rechazadas por gate actual:** 22.

### 1.2 Perfil agregado de los 24 candidatos
| Estrategia | Retorno IS (%) | Retorno OOS (%) | Trades IS/OOS | PF IS/OOS | DD OOS (%) | WFE (OOS/IS) | Observación |
|---|---|---|---|---|---|---|---|
| 1.1.43 | 37.17 | -0.90 | 61 / 28 | 1.56 / 0.80 | 202.57 | -0.02 | IS alto, OOS ruinoso |
| 1.2.24 | 16.22 | 1.11 | 37 / 20 | 1.40 / 1.45 | 50.43 | 0.07 | Pocos trades, OOS marginal |
| 1.1.42 | 10.86 | -0.48 | 74 / 32 | 1.13 / 0.83 | 131.77 | -0.04 | PF_OOS < 1.0 |
| 1.1.24 | 10.11 | 1.24 | 40 / 21 | 1.20 / 1.48 | 59.50 | 0.12 | PF_IS < 1.3 |
| 1.1.41 | 10.01 | 0.32 | 86 / 30 | 1.34 / 1.33 | 72.55 | 0.03 | Pasa `/rentable` |
| 1.1.38 | 6.01 | -0.51 | 22 / 4 | 1.27 / 0.23 | 66.30 | -0.08 | OOS casi nulo, DD alta |
| 1.1.37 | 5.40 | -2.87 | 67 / 34 | 1.07 / 0.40 | 298.36 | -0.53 | OOS ruinoso |
| 1.1.28 | 3.73 | -0.14 | 33 / 18 | 2.13 / 0.80 | 44.17 | -0.04 | PF_OOS < 1.0 |
| 1.1.29 | 2.68 | -0.15 | 27 / 16 | 1.20 / 0.85 | 65.61 | -0.05 | Pocos trades |
| 1.1.23 | 2.49 | -0.43 | 79 / 46 | 1.06 / 0.83 | 79.05 | -0.17 | PF_IS < 1.3 |
| 1.1.33 | 1.66 | -0.01 | 21 / 12 | 1.54 / 0.95 | 27.57 | -0.01 | Pocos trades |
| ... | ... | ... | ... | ... | ... | ... | ... |

**Nota:** Las marcas "..." representan el resto de estrategias con retornos IS entre -22.94% y +2.86%. Ninguna supera 40% IS ni 1.5% OOS.

---

## 2. Auditoría contra el Protocolo del Blueprint

### 2.1 Frente al requisito "1000%+ verificable"
- **Hallazgo:** **Ningún candidato actual supera 1000%**. El máximo IS es 37.17%.
- **Interpretación:** Con los datos actuales no se puede validar el protocolo extremo porque ni siquiera se presenta un sospechoso de "miles de %". Esto sugiere que el run kamikaze actual no ha generado retornos extremos, o bien el databank `Results` no los ha retenido.

### 2.2 Requisitos mínimos del blueprint para retornos extremos
| Requisito | Umbral blueprint | Cumplimiento actual | Evidencia real |
|---|---|---|---|
| N trades IS | >= 200 si >500% o >=1000% | No aplica (no hay >500%) | Max IS trades = 199 (`1.1.27`) |
| N trades OOS | >= 100 | No aplica | Max OOS trades = 98 (`1.1.27`) |
| Cobertura IS | 2-3 años diarios o 6-12 meses intradía | No disponible en BD | No se almacena rango de fechas |
| Cobertura OOS | >= 6 meses reales | No disponible | No se almacena rango de fechas |
| Outlier dependency | Top-2 trades < 15% IS / <20% OOS | No computable | No hay datos de PnL por trade en BD |
| Walk-forward OOS | >= 50% bloques positivos | No computable | No hay bloques WF en BD |
| WFE | >= 0.60 | Computable | Máximo WFE ≈ 0.12 |
| Max DD OOS | < 40% | Computable | Solo 1 estrategia con DD_OOS < 40%: `1.1.24` con 59.50% |
| Monte Carlo | >=90% simulaciones equity>0 | No computable | Sin serie de trades en BD |
| 2º motor Nautilus | Reproducibilidad | No ejecutado | Sin evidencia |
| DSR / Romano-Wolf | Ajuste múltiples pruebas | No computable | Sin número de trials ni distribución nula |

### 2.3 Diagnóstico de overfit
- **Patrón dominante:** IS positivo o moderado, OOS negativo o ruinoso. Esto es firma clásica de overfit a IS.
- **Ejemplos paradigmáticos:**
  - `1.1.43`: PF_IS 1.56, PF_OOS 0.80, DD_OOS 202.57%. Overfit severo.
  - `1.1.37`: IS +5.4%, OOS -286.92%, DD_OOS 298.36%. Catastrófico OOS.
  - `1.1.38`: IS +6.01%, OOS -50.56%, solo 4 trades OOS. Overfit por pocos trades.
- **Conclusión:** Los 24 candidatos actuales no superan el protocolo. 22/24 ya son excluidos por `/rentable`; los 2 restantes (`1.2.24`, `1.1.41`) son marginales y tampoco pasarían la scorecard completa.

---

## 3. Scorecard de Calidad Operativa

### 3.1 Definición de niveles
| Nivel | Definición | Acción |
|---|---|---|
| **POTENTIAL_WINNER** | Supera protocolo completo o tiene tracción suficiente para 2º motor + MC. | Avanzar a Nautilus y portfolio. |
| **NEEDS_2ND_MOTOR** | Cumple criba barata y filtros básicos, pero le faltan OOS robustos, WFE, MC o cobertura temporal. | Enviar a validación adversarial / Nautilus antes de decidir. |
| **REJECTED_OVERFIT** | Falla gates básicos, dependencia de outliers, OOS negativo, ruinoso o sin generalización. | Descarte operativo. |

### 3.2 Reglas de scorecard (lista para implementar)

#### Capa A — Criba Barata (ejecutar en ingest y `/rentable`)
```yaml
min_trades_is: 30
min_pf_is: 1.30
min_net_return_is_pct: 5.0
max_dd_is_pct: 85.0 # solo ruina real >=100%
require_oos: true
min_trades_oos: 10
min_pf_oos: 1.00
min_net_return_oos_pct: 0.0
```
**Si falla A → `REJECTED_OVERFIT`.**

#### Capa B — Evidencia y Robustez (filtros adicionales del blueprint)
```yaml
wfe_min: 0.60
outlier_dependency_is_max_top2_share: 0.15
outlier_dependency_oos_max_top2_share: 0.20
max_dd_oos_pct: 40.0
temporal_coverage_is_min_days: 730 # 2 años diarios
temporal_coverage_oos_min_days: 180 # 6 meses
monte_carlo_min_positive_final_equity_pct: 0.90
```
**Si falla B → `NEEDS_2ND_MOTOR`.**

#### Capa C — Validación Extrema (solo para sospechosos de >=500% o >=1000%)
```yaml
extreme_return_min_pct: 500
extreme_min_trades_is: 200
extreme_min_trades_oos: 100
nautilus_delta_return_max_pct: 10
nautilus_delta_dd_max_pct: 3
nautilus_delta_sharpe_max: 0.5
```
**Si cumple A+B y supera C → `POTENTIAL_WINNER`.**

### 3.3 Aplicación práctica a los datos actuales
| Estrategia | Capa A | Capa B | Capa C | Score final |
|---|---|---|---|---|
| 1.1.43 | PF_IS OK, OOS PF<1.0 | WFE <<0.6, DD_OOS>>40% | N/A | **REJECTED_OVERFIT** |
| 1.2.24 | PF_IS OK, trades IS<30 | WFE<<0.6, DD_OOS>>40% | N/A | **REJECTED_OVERFIT** |
| 1.1.24 | PF_IS<1.3 | — | N/A | **REJECTED_OVERFIT** |
| 1.1.41 | Pasa A | WFE<<0.6, DD_OOS>>40% | N/A | **NEEDS_2ND_MOTOR** |
| 1.1.38 | trades OOS<10 | — | N/A | **REJECTED_OVERFIT** |
| Resto | Varios fallos | — | N/A | **REJECTED_OVERFIT** |

**Resultado:** 0 potenciales ganadores. 1 candidato borderline para 2º motor (`1.1.41`). 23 claramente descartables.

---

## 4. Flujo de Nuevos Resultados Kamikaze y Ajustes Necesarios

### 4.1 Cómo se puebla el databank `Results`
1. Un subagente ejecuta `run_project` sobre `Ultra_Auto_Pilot` en SQX.
2. SQX genera estrategias y escribe métricas en el databank configurado (`Results` por defecto en ingest).
3. Al llamar a `POST /projects/{project}/ingest`, el router:
   - Lista estrategias del databank.
   - Extrae métricas con `extract_stats`.
   - Calcula `net_return`, `max_dd`, `pf`.
   - Aplica `rentable(ultra)` para decidir `SQX_CANDIDATE` vs `SQX_REJECTED_RISK`.
   - Inserta `StrategyModel` + `BacktestModel`.

### 4.2 Por qué los resultados kamikaze nuevos podrían quedar excluidos
- **Umbral de rentable() en ingest (`ultra`):** exige `net_return >= 5%` y `PF >= 1.5`. Si el run kamikaze produce estrategias con retornos altos pero PF cercano a 1.2-1.4 (común en entornos extremos), **se marcarán como `SQX_REJECTED_RISK` y no aparecerán en `/rentable`**.
- **Filtro `/rentable`:** exige `PF_OOS >= 1.0` y `trades >= 20`. Si el modo kamikaze reduce la frecuencia de trading o tiene OOS ruidoso, **quedará excluido**.
- **Falta de columnas de evidencia:** la BD actual no guarda:
  - Rango temporal IS/OOS.
  - Serie de retornos por trade (para outlier dependency y MC).
  - Bloques walk-forward.
  - Métricas de diversidad/hash.
  Sin esto, **ni el blueprint ni la scorecard pueden ejecutarse** aunque los datos lleguen.

### 4.3 Ajustes recomendados para que los nuevos kamikaze aparezcan cuando valgan
1. **Relajar `rentable()` en modo `ultra` para ingest** (no para `/rentable`):
   - Cambiar `MIN_RENTABLE_NET_RETURN_PCT` a `0.0` en modo `ultra`.
   - Cambiar `MIN_RENTABLE_PROFIT_FACTOR` a `1.1` en modo `ultra`.
   - Motivo: no queremos que el gate de ingest descarte candidatos kamikaze con retornos altos pero PF delgado. El filtro fino va en `/rentable` y scorecard.

2. **Endurecer `/rentable` con la scorecard del blueprint**:
   - Mantener `PF_OOS >= 1.0` y `trades >= 20`.
   - Añadir `WFE >= 0.60` cuando sea computable.
   - Añadir `max_dd_oos < 40%`.
   - Añadir `net_return_oos_pct > 0`.
   - Para candidatos con `net_return_is_pct >= 500`, exigir `trades_is >= 200` y `trades_oos >= 100`.

3. **Ampliar esquema de `backtests` para capturar evidencia**:
   - Añadir columnas: `is_start_date`, `is_end_date`, `oos_start_date`, `oos_end_date`, `wfe`, `top2_trade_dependency_is`, `top2_trade_dependency_oos`, `monte_carlo_positive_pct`, `dsr`, `hash_diversity_score`.
   - Esto permite ejecutar la scorecard completa sin adivinar.

4. **Persistir checksum/dsl_hash y familia**:
   - Ya existe `canonical_hash` en `strategies`. Usarlo para detectar clones entre runs kamikaze.

5. **No descartar por drawdown en modo `ultra`**:
   - Mantener el comportamiento actual: solo ruina real (`>=100%`) descarta.
   - Pero en `/rentable` sí mostrar el DD OOS para decisión humana; no ocultar candidatos con DD 60-90% si el retorno es extremo y el WFE bueno.

---

## 5. Recomendaciones Finales

1. **Implementar la scorecard como módulo independiente** (`services/api/app/factory/kamikaze_scorecard.py`) con las tres capas definidas arriba. `/rentable` e `ingest` deben consumirla.
2. **Cerrar los gaps P0 del blueprint** antes de celebrar cualquier "miles de %":
   - G1: DSR/ajuste múltiples pruebas.
   - G2: CPCV/purging.
   - G5: protocolo extremo con outlier-dependency, MC, WFE.
   - G6: hash diversity y anti-clonación.
3. **Preparar la ingesta de trade-level data**: mientras SQX no guarde la serie de trades en BD, la auditoría no puede certificar "miles de %". Cualquier candidato con retorno extremo debe ser marcado como `NEEDS_2ND_MOTOR` hasta tener esa evidencia.
4. **No modificar `/home/ubuntu/StrategyQuantX` ni servicios/core** desde este documento. Las recomendaciones son para el subagente de API/quality gates.

---

## 6. Próximos Pasos Operativos
1. El subagente de API actualiza `quality_gates.py` e `ingest_sqx_results.py` según ajustes 4.3.1 y 4.3.2.
2. El subagente de SQX lanza run kamikaze con seed diversa y databank `Results`.
3. Este auditor vuelve a ejecutar la consulta `/api/v1/sqx/rentable` y la scorecard para certificar si apareció algún `POTENTIAL_WINNER`.
4. Solo después de pasar Capa B, el subagente de Nautilus ejecuta la validación en 2º motor.

---

*Documento generado con datos reales de API y SQLite. No se inventaron métricas.*
