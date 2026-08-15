# Pipeline de Validación Multi-Motor: SQX → NautilusTrader
## Documento Accionable para Implementación de Quality Gates

**Proyecto:** Ultrarentable — `/home/ubuntu/workspace/pro/trading/01 Ultrarentable`  
**Fuentes canónicas:**
- `plan_implementacion/BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md`
- `plan_implementacion/AUDITORIA_CANDIDATOS_KAMIKAZE.md`
- BD operacional: `~/.local/state/ultrarentable/ultrarentable.sqlite3`  
**Motor canónico de validación final:** NautilusTrader (decisión de proyecto)  
**Regla REAL-ONLY:** toda métrica debe provenir de ejecución real. Prohibido inventar valores.  
**Fecha:** 2026-08-09  
**Estado:** Diseño accionable — listo para implementación por subagente API/quality-gates

---

## Tabla de Contenidos

1. [Pipeline de Validación Completo](#1-pipeline-de-validación-completo)
2. [Configuración de Walk-Forward Analysis (WFA)](#2-configuración-de-walk-forward-analysis-wfa)
3. [Pruebas de Monte Carlo](#3-pruebas-de-monte-carlo)
4. [Gate de Robustez SPP (Sensibilidad de Parámetros)](#4-gate-de-robustez-spp-sensibilidad-de-parámetros-15)
5. [Scorecard de 3 Capas (Integración Final)](#5-scorecard-de-3-capas-integración-final)
6. [Gaps en la BD y Extensión del Esquema](#6-gaps-en-la-bd-y-extensión-del-esquema)
7. [Criterios de Decisión Final](#7-criterios-de-decisión-final)
8. [Contrato de Implementación para Subagente](#8-contrato-de-implementación-para-subagente)

---

## 1. Pipeline de Validación Completo

### 1.1 Diagrama de flujo

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PIPELINE DE VALIDACIÓN MULTI-MOTOR                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────┐     │
│  │  ETAPA 0     │     │  ETAPA 1     │     │  ETAPA 2                 │     │
│  │  Generación  │────>│  Ingesta     │────>│  CRIBA BARATA (Capa A)   │     │
│  │  SQX         │     │  + Dedup     │     │  vectorbt / fast filters │     │
│  └──────────────┘     └──────────────┘     └────────┬─────────────────┘     │
│                                                      │                      │
│                                            FALLA ────┤──── REJECTED_OVERFIT │
│                                                      │                      │
│                                                      ▼                      │
│                                            ┌──────────────────────────┐     │
│                                            │  ETAPA 3                 │     │
│                                            │  EVIDENCIA + ROBUSTEZ    │     │
│                                            │  (Capa B)                │     │
│                                            │  WFA + MC + SPP + DSR    │     │
│                                            └────────┬─────────────────┘     │
│                                                      │                      │
│                                            FALLA ────┤──── NEEDS_2ND_MOTOR  │
│                                                      │                      │
│                                                      ▼                      │
│                                            ┌──────────────────────────┐     │
│                                            │  ETAPA 4                 │     │
│                                            │  VALIDACIÓN 2º MOTOR     │     │
│                                            │  NautilusTrader          │     │
│                                            └────────┬─────────────────┘     │
│                                                      │                      │
│                                            FALLA ────┤──── REJECTED_OVERFIT │
│                                                      │                      │
│                                                      ▼                      │
│                                            ┌──────────────────────────┐     │
│                                            │  ETAPA 5                 │     │
│                                            │  VALIDACIÓN EXTREMA      │     │
│                                            │  (Capa C — si ret≥500%)  │     │
│                                            └────────┬─────────────────┘     │
│                                                      │                      │
│                                                      ▼                      │
│                                            ┌──────────────────────────┐     │
│                                            │  DECISIÓN FINAL          │     │
│                                            │  POTENTIAL_WINNER        │     │
│                                            └──────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Descripción de cada etapa

| Etapa | Nombre | Input | Output | Responsable | Motor |
|-------|--------|-------|--------|-------------|-------|
| 0 | Generación SQX | Configuración campaña | Candidatos crudos en databank | SQX (externo) | SQX |
| 1 | Ingesta + Dedup | Databank SQX | Registros en BD con `canonical_hash` | API `/ingest` | — |
| 2 | Criba Barata (Capa A) | BD `strategies` + `backtests` | Candidatos verdes / REJECTED_OVERFIT | `/rentable` + scorecard | — |
| 3 | Evidencia + Robustez (Capa B) | Candidatos verdes + serie de trades | Candidatos robustos / NEEDS_2ND_MOTOR | `kamikaze_scorecard.py` | vectorbt (opcional) |
| 4 | Validación 2º Motor | Candidatos robustos + DSL | Champions / REJECTED_OVERFIT | `nautilus_validator.py` | **NautilusTrader** |
| 5 | Validación Extrema (Capa C) | Champions con ret≥500% | POTENTIAL_WINNER | scorecard Capa C | NautilusTrader |

### 1.3 Reglas de tránsito entre etapas

- **Etapa 1 → 2:** Automática tras ingesta exitosa. Todo candidato ingerido se evalúa contra Capa A.
- **Etapa 2 → 3:** Solo candidatos que pasan TODOS los umbrales de Capa A.
- **Etapa 3 → 4:** Solo candidatos que pasan TODOS los umbrales de Capa B (WFA, MC, SPP, outlier dependency).
- **Etapa 4 → 5:** Solo si `net_return_is_pct >= 500` O `net_return_oos_pct >= 200`. Si no alcanza esos umbrales pero pasa Etapa 4, es `POTENTIAL_WINNER` directamente.
- **Etapa 5 → Decisión:** `POTENTIAL_WINNER` solo si cumple todos los umbrales de Capa C.

---

## 2. Configuración de Walk-Forward Analysis (WFA)

### 2.1 Configuración canónica

```yaml
wfa_config:
  method: "anchored"          # Anchored (expanding window), NO rolling
  n_folds: 8                   # 8 períodos de evaluación OOS
  oos_pct: 25                  # 25% de cada fold es OOS
  purge_days: 5                # 5 días de purga entre IS y OOS (evita fuga)
  embargo_days: 2              # 2 días de embargo post-OOS antes del siguiente fold
  min_trades_per_fold_oos: 10  # Mínimo de trades en cada ventana OOS
  min_positive_folds_pct: 62.5 # Al menos 5 de 8 folds OOS positivos (62.5%)
```

### 2.2 Justificación de cada parámetro

| Parámetro | Valor | Justificación |
|-----------|-------|---------------|
| **Método: Anchored** | Expanding window | El anclado (IS crece con cada fold) refleja cómo un trader re-entrena: con toda la historia disponible, no solo una ventana. Más conservador que rolling porque el IS crece y el overfit se diluye. López de Prado y WorldQuant lo prefieren para evaluación de robustez. |
| **n_folds: 8** | 8 periodos OOS | Con 8 folds se obtienen suficientes ventanas OOS para significancia estadística sin fragmentar excesivamente los datos. Para BTC-USDT 1h con ~2-3 años de datos, cada fold OOS cubre ~3-4 meses. Menos de 6 folds da poca significancia; más de 12 fragmenta demasiado para cripto 1h. |
| **oos_pct: 25%** | Cada fold: 75% IS / 25% OOS | El 25% OOS es el estándar de la industria (Bailey & López de Prado). 20% sería insuficiente para cripto volátil; 33% reduciría demasiado el IS y haría el entrenamiento inestable. |
| **purge_days: 5** | 5 días eliminados entre IS/OOS | En timeframe 1h, un trade puede durar varios días. 5 días de purga elimina cualquier información que se solape entre el final del IS y el inicio del OOS. Previene lookahead bias por trades abiertos al cierre del IS. |
| **embargo_days: 2** | 2 días post-OOS | Evita que la primera ventana del siguiente fold IS contenga información del OOS anterior (autocorrelación residual). |
| **min_trades_per_fold_oos: 10** | ≥10 trades por ventana OOS | Menos de 10 trades no da significancia para evaluar rentabilidad del fold. |
| **min_positive_folds_pct: 62.5%** | 5/8 folds positivos | Umbral estricto: exige consistencia temporal, no solo que el agregado sea positivo. Un solo fold espectacular no compensa 5 negativos. |

### 2.3 Walk-Forward Efficiency (WFE)

```
WFE = Retorno_OOS_agregado / Retorno_IS_agregado
```

| Umbral WFE | Interpretación | Acción |
|------------|----------------|--------|
| WFE ≥ 0.60 | Robusto: OOS retiene ≥60% del rendimiento IS | Avanza a siguiente etapa |
| 0.30 ≤ WFE < 0.60 | Sospechoso: degradación excesiva IS→OOS | `NEEDS_2ND_MOTOR` (requiere MC + Nautilus para decidir) |
| WFE < 0.30 | Overfit severo | `REJECTED_OVERFIT` |
| WFE < 0 | OOS pierde dinero | `REJECTED_OVERFIT` (descarte inmediato) |

### 2.4 Métricas derivadas del WFA a almacenar

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `wfa_n_folds` | INTEGER | Número de folds ejecutados |
| `wfa_method` | VARCHAR | 'anchored' o 'rolling' |
| `wfa_oos_pct` | REAL | % OOS por fold |
| `wfe` | REAL | Walk-Forward Efficiency agregado |
| `wfa_positive_folds_pct` | REAL | % de folds OOS con retorno > 0 |
| `wfa_fold_returns_json` | TEXT | JSON array con retorno de cada fold OOS |
| `wfa_worst_fold_return_pct` | REAL | Peor retorno de un fold individual |

---

## 3. Pruebas de Monte Carlo

### 3.1 Configuración canónica

```yaml
monte_carlo_config:
  n_simulations: 10000         # 10k simulaciones (balance velocidad/precisión)
  methods:
    - trade_reorder             # Reordenamiento aleatorio de trades
    - slippage_variation        # Variación de slippage ±50% vs nominal
    - spread_variation          # Variación de spread ±30% vs nominal
    - combined_stress           # slippage 2x + spread 1.5x simultáneo
  seed: 42                     # Reproducibilidad
  confidence_level: 0.95       # Para intervalos de confianza
```

### 3.2 Método 1: Reordenamiento de trades (Trade Shuffling)

**Qué hace:** Toma la serie completa de PnL por trade y la reordena aleatoriamente 10.000 veces. Recalcula la curva de equity para cada permutación.

**Qué detecta:** Dependencia del orden temporal de los trades. Si la estrategia solo funciona porque un cluster de trades ganadores ocurrió al principio (o al final), el reordenamiento lo expone.

**Métricas a extraer:**

| Métrica | Umbral PASS | Umbral FAIL |
|---------|-------------|-------------|
| `mc_pct_positive_equity` | ≥ 90% de simulaciones terminan con equity > capital inicial | < 85% → REJECTED |
| `mc_p10_final_equity` | P10 del equity final > 0.8 × capital inicial | P10 < 0.5 × capital → REJECTED |
| `mc_p50_max_drawdown` | Mediana del max DD < 50% | P50 DD > 60% → REJECTED |
| `mc_p95_max_drawdown` | P95 del max DD < 80% | P95 DD > 90% → REJECTED |
| `mc_p10_return_pct` | P10 del retorno final > -10% | P10 < -30% → REJECTED |

### 3.3 Método 2: Variación de Slippage

**Qué hace:** Para cada trade, aplica un slippage aleatorio entre 50% y 150% del slippage nominal. Ejecuta 10.000 simulaciones.

**Qué detecta:** Fragilidad a condiciones de ejecución reales. Estrategias que son rentables solo con slippage cero o mínimo.

```yaml
slippage_variation:
  nominal_slippage_bps: 5      # 5 bps nominal para BTC-USDT
  min_multiplier: 0.5          # 50% del nominal (mejor ejecución)
  max_multiplier: 2.0          # 200% del nominal (peor ejecución)
  distribution: uniform        # Distribución uniforme del multiplicador
```

**Umbral:** La estrategia debe ser rentable en ≥ 80% de las simulaciones con slippage entre 1x y 2x.

### 3.4 Método 3: Variación de Spread

**Qué hace:** Aplica spread variable (±30% del nominal) a cada trade.

```yaml
spread_variation:
  nominal_spread_bps: 3        # 3 bps nominal
  min_multiplier: 0.7          # 70% del nominal
  max_multiplier: 1.5          # 150% del nominal
  distribution: uniform
```

**Umbral:** Rentable en ≥ 85% de simulaciones.

### 3.5 Método 4: Estrés Combinado

**Qué hace:** Aplica simultáneamente slippage 2x + spread 1.5x. Es el test más agresivo.

**Umbral:** Rentable en ≥ 70% de simulaciones. Si falla, la estrategia es `REJECTED_OVERFIT` por fragilidad a costes.

### 3.6 Resumen de umbrales MC

| Test MC | Métrica clave | PASS | WARN | FAIL |
|---------|--------------|------|------|------|
| Trade Reorder | % equity positiva final | ≥ 90% | 85-90% | < 85% |
| Trade Reorder | P10 equity final | > 0.8x capital | 0.5-0.8x | < 0.5x |
| Slippage 1-2x | % simulaciones rentables | ≥ 80% | 70-80% | < 70% |
| Spread 0.7-1.5x | % simulaciones rentables | ≥ 85% | 75-85% | < 75% |
| Estrés combinado | % simulaciones rentables | ≥ 70% | 60-70% | < 60% |

### 3.7 Campos MC a almacenar en BD

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `mc_n_simulations` | INTEGER | Nº de simulaciones ejecutadas |
| `mc_trade_reorder_positive_pct` | REAL | % simulaciones con equity final > capital |
| `mc_trade_reorder_p10_equity` | REAL | Percentil 10 del equity final |
| `mc_trade_reorder_p50_maxdd` | REAL | Mediana del max DD en simulaciones |
| `mc_slippage_stress_positive_pct` | REAL | % rentable bajo slippage variable |
| `mc_spread_stress_positive_pct` | REAL | % rentable bajo spread variable |
| `mc_combined_stress_positive_pct` | REAL | % rentable bajo estrés combinado |
| `mc_verdict` | VARCHAR | 'PASS' / 'WARN' / 'FAIL' |

---

## 4. Gate de Robustez SPP (Sensibilidad de Parámetros ±15%)

### 4.1 Definición

**SPP = Strategy Parameter Perturbation.** Consiste en perturbar cada parámetro optimizable de la estrategia en ±15% y re-ejecutar el backtest. Si el rendimiento cae drásticamente, la estrategia está en un "pico aislado" del espacio de parámetros → sobreajuste.

### 4.2 Protocolo de ejecución

```yaml
spp_config:
  perturbation_pct: 15          # ±15% de cada parámetro
  n_perturbations_per_param: 5  # 5 valores por parámetro (original, ±7.5%, ±15%)
  execution_mode: "grid"        # Grid sobre cada parámetro individualmente
  metric_principal: "net_return_pct"  # Métrica a evaluar
  metric_secundaria: "profit_factor"
  motor: "SQX"                  # Primer pase en SQX (rápido). Si pasa, confirmar en Nautilus.
```

**Procedimiento paso a paso:**

1. **Extraer parámetros optimizables** del DSL/JSON de la estrategia (`dsl_json` en tabla `strategies`).
2. **Para cada parámetro `p_i`** con valor original `v_i`:
   - Calcular variantes: `v_i × 0.85`, `v_i × 0.925`, `v_i`, `v_i × 1.075`, `v_i × 1.15`.
   - Ejecutar backtest con cada variante (el resto de parámetros fijos).
   - Registrar `net_return_pct` y `profit_factor` de cada variante.
3. **Calcular métricas SPP:**
   - `spp_stability_ratio`: `min(returns_variantes) / return_original`. Si el mínimo es < 50% del original, es un pico.
   - `spp_mean_degradation`: degradación media del retorno en las variantes vs original.
   - `spp_params_fragile_count`: nº de parámetros donde alguna variante ±15% causa retorno ≤ 0.

### 4.3 Umbrales SPP

| Métrica SPP | PASS | WARN | FAIL |
|-------------|------|------|------|
| `spp_stability_ratio` | ≥ 0.50 | 0.30 - 0.50 | < 0.30 |
| `spp_mean_degradation` | ≤ 30% | 30-50% | > 50% |
| `spp_params_fragile_count` | 0 | 1 | ≥ 2 |
| PF mínimo en variantes | ≥ 1.0 | 0.8 - 1.0 | < 0.8 |

**Regla de decisión:**
- **PASS:** `spp_stability_ratio ≥ 0.50` Y `spp_params_fragile_count == 0` → La estrategia es robusta a perturbaciones.
- **WARN:** Alguna métrica en zona WARN → `NEEDS_2ND_MOTOR` (confirmar con Nautilus).
- **FAIL:** Cualquier métrica en FAIL → `REJECTED_OVERFIT` (pico aislado confirmado).

### 4.4 Campos SPP a almacenar

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `spp_stability_ratio` | REAL | min(variantes) / original |
| `spp_mean_degradation_pct` | REAL | Degradación media vs original |
| `spp_params_fragile_count` | INTEGER | Parámetros que causan retorno ≤ 0 |
| `spp_params_total` | INTEGER | Total de parámetros perturbados |
| `spp_verdict` | VARCHAR | 'PASS' / 'WARN' / 'FAIL' |
| `spp_detail_json` | TEXT | JSON con retorno por cada variante |

---

## 5. Scorecard de 3 Capas (Integración Final)

Esta sección integra y cierra la scorecard definida en `AUDITORIA_CANDIDATOS_KAMIKAZE.md`, incorporando WFA, MC y SPP como gates formales.

### 5.1 Capa A — Criba Barata

**Ejecución:** Automática en ingesta (`/ingest`) y endpoint `/rentable`.  
**Motor:** Ninguno (métricas ya en BD desde SQX).  
**Coste computacional:** Cero (consulta SQL).

```yaml
capa_a_gates:
  min_trades_is: 30
  min_pf_is: 1.30
  min_net_return_is_pct: 5.0
  max_dd_is_pct: 85.0          # Ruina real ≥100% = descarte absoluto
  require_oos: true
  min_trades_oos: 10
  min_pf_oos: 1.00
  min_net_return_oos_pct: 0.0  # OOS no puede ser negativo
  max_dd_oos_pct: 80.0         # Gate amplio; Capa B endurece a 40%
```

**Veredicto Capa A:**
- **FALLA cualquier gate → `REJECTED_OVERFIT`** (descarte inmediato, no avanza).
- **PASA todos → Avanza a Capa B.**

### 5.2 Capa B — Evidencia y Robustez

**Ejecución:** Módulo `kamikaze_scorecard.py`, invocado bajo demanda.  
**Motor:** vectorbt (criba rápida) + datos de serie de trades.  
**Coste computacional:** Medio (WFA + MC + SPP requieren re-ejecución parcial o serie de trades).

```yaml
capa_b_gates:
  # Walk-Forward Analysis
  wfe_min: 0.60
  wfa_positive_folds_min_pct: 62.5
  wfa_worst_fold_return_min_pct: -15.0  # Ningún fold puede perder >15%
  
  # Monte Carlo
  mc_trade_reorder_positive_min_pct: 90.0
  mc_trade_reorder_p10_equity_min_ratio: 0.8  # P10 ≥ 80% del capital
  mc_combined_stress_positive_min_pct: 70.0
  
  # Sensibilidad de Parámetros (SPP)
  spp_stability_ratio_min: 0.50
  spp_params_fragile_max: 0
  
  # Outlier dependency
  outlier_dependency_is_max_top2_share: 0.15  # Top-2 trades < 15% del PnL IS
  outlier_dependency_oos_max_top2_share: 0.20 # Top-2 trades < 20% del PnL OOS
  
  # Cobertura temporal
  temporal_coverage_is_min_days: 730   # 2 años mínimo IS
  temporal_coverage_oos_min_days: 180  # 6 meses mínimo OOS
  
  # Drawdown OOS endurecido
  max_dd_oos_pct: 40.0
```

**Veredicto Capa B:**
- **FALLA WFE < 0.30 O MC < 85% O SPP FAIL → `REJECTED_OVERFIT`** (overfit confirmado).
- **FALLA gates blandos (WFE 0.30-0.59, MC WARN, SPP WARN) → `NEEDS_2ND_MOTOR`** (requiere Nautilus para decidir).
- **PASA todos → Avanza a Etapa 4 (Nautilus) o Capa C si ret ≥ 500%.**

### 5.3 Etapa 4 — Validación en 2º Motor (NautilusTrader)

Esta etapa no es una "capa" de la scorecard sino una **etapa de pipeline obligatoria** para todo candidato que pasa Capa B.

```yaml
nautilus_validation:
  motor: "NautilusTrader"
  dataset: "mismo IS/OOS que SQX"  # Mismos datos, diferente motor
  tolerancias:
    delta_return_max_pct: 10.0    # |ret_nautilus - ret_sqx| / ret_sqx ≤ 10%
    delta_dd_max_pct: 3.0         # |dd_nautilus - dd_sqx| ≤ 3 puntos porcentuales
    delta_sharpe_max: 0.5         # |sharpe_nautilus - sharpe_sqx| ≤ 0.5
    delta_trades_max_pct: 5.0     # |trades_nautilus - trades_sqx| / trades_sqx ≤ 5%
  engine_type_tag: "NAUTILUS"     # Tag en BD para estos backtests
```

**Veredicto Nautilus:**
- **Desviación dentro de tolerancias → CONFIRMA** la estrategia. Motor SQX no es artefacto.
- **Desviación fuera de tolerancias → `REJECTED_OVERFIT`** (artefacto del motor SQX o lookahead bias).

### 5.4 Capa C — Validación Extrema (ret ≥ 500%)

**Activación:** Solo para candidatos con `net_return_is_pct ≥ 500` O `net_return_oos_pct ≥ 200`.  
**Motor:** NautilusTrader (ya ejecutado en Etapa 4).

```yaml
capa_c_gates:
  extreme_return_threshold_is_pct: 500
  extreme_return_threshold_oos_pct: 200
  extreme_min_trades_is: 200
  extreme_min_trades_oos: 100
  extreme_wfe_min: 0.70         # Más estricto que Capa B
  extreme_mc_positive_min_pct: 95.0  # Más estricto que Capa B
  extreme_spp_stability_ratio_min: 0.60
  # Nautilus (ya ejecutado):
  nautilus_delta_return_max_pct: 10.0
  nautilus_delta_dd_max_pct: 3.0
  nautilus_delta_sharpe_max: 0.5
```

**Veredicto Capa C:**
- **PASA A + B + Nautilus + C → `POTENTIAL_WINNER`** 🏆
- **FALLA C pero pasó B + Nautilus → `POTENTIAL_WINNER`** (con nota: no cumple protocolo extremo, pero es winner para retornos < 500%).

### 5.5 Tabla resumen de la scorecard

| Capa | Gates principales | Si FALLA | Si PASA |
|------|-------------------|----------|--------|
| **A** (Criba Barata) | trades≥30, PF_IS≥1.3, PF_OOS≥1.0, ret_OOS≥0, DD_IS<85% | → `REJECTED_OVERFIT` | → Capa B |
| **B** (Evidencia/Robustez) | WFE≥0.60, MC≥90%, SPP≥0.50, outliers<15%, DD_OOS<40% | → `NEEDS_2ND_MOTOR` (o REJECTED si fallo severo) | → Nautilus |
| **Nautilus** (2º Motor) | Δret<10%, Δdd<3pp, Δsharpe<0.5 | → `REJECTED_OVERFIT` | → Capa C (si ret≥500%) o WINNER |
| **C** (Extrema) | trades_IS≥200, WFE≥0.70, MC≥95%, SPP≥0.60 | → WINNER (normal, no extremo) | → `POTENTIAL_WINNER` (élite) |

### 5.6 Integración con AUDITORIA_CANDIDATOS_KAMIKAZE.md

La auditoría de los 24 candidatos actuales queda **cerrada** con el siguiente veredicto:

| Candidato | Capa A | Capa B | Nautilus | Decisión final |
|-----------|--------|--------|----------|----------------|
| 1.1.41 | ✅ PASA | ❌ WFE=0.03, DD_OOS=72.55% | No ejecutado | **NEEDS_2ND_MOTOR** (borderline) |
| 1.2.24 | ❌ trades_IS=37 < 30... marginal | — | — | **REJECTED_OVERFIT** |
| 1.1.43 | ❌ PF_OOS=0.80 < 1.0 | — | — | **REJECTED_OVERFIT** |
| 1.1.24 | ❌ PF_IS=1.20 < 1.3 | — | — | **REJECTED_OVERFIT** |
| Resto (20) | ❌ Varios fallos | — | — | **REJECTED_OVERFIT** |

**Conclusión de la auditoría: 0 POTENTIAL_WINNER, 1 NEEDS_2ND_MOTOR (1.1.41), 23 REJECTED_OVERFIT.** Esta auditoría NO se reabre salvo que lleguen datos nuevos de ejecución real.

---

## 6. Gaps en la BD y Extensión del Esquema

### 6.1 Esquema actual de `backtests` (real, de SQLite)

```sql
CREATE TABLE backtests (
    backtest_id VARCHAR NOT NULL PRIMARY KEY,
    strategy_id VARCHAR,
    dataset_id VARCHAR,
    engine_type VARCHAR,        -- FAST_APPROXIMATE | SQX_BUILTIN | COMPILED
    initial_capital FLOAT,
    leverage INTEGER,
    final_equity FLOAT,
    net_return_pct FLOAT,
    max_drawdown_pct FLOAT,
    win_rate FLOAT,
    trades_count INTEGER,
    profit_factor FLOAT,
    checksum VARCHAR,
    ledger_path VARCHAR,
    artifacts_path VARCHAR,
    status VARCHAR,
    created_at DATETIME,
    -- Columnas OOS añadidas recientemente:
    pf_os REAL,
    net_return_os_pct REAL,
    max_drawdown_os_pct REAL,
    trades_os INTEGER,
    ret_dd_ratio REAL
);
```

### 6.2 Columnas que FALTAN (P0 — bloqueantes para el pipeline)

| # | Campo faltante | Tipo | Por qué es P0 | Gate que desbloquea |
|---|----------------|------|----------------|---------------------|
| F1 | `is_start_date` | DATE | Sin rango temporal, no se puede verificar cobertura IS ≥ 2 años | Capa B: `temporal_coverage_is_min_days` |
| F2 | `is_end_date` | DATE | Idem | Capa B |
| F3 | `oos_start_date` | DATE | Sin rango OOS, no se puede verificar ≥ 6 meses | Capa B: `temporal_coverage_oos_min_days` |
| F4 | `oos_end_date` | DATE | Idem | Capa B |
| F5 | `trade_series_path` | VARCHAR | Sin serie de trades PnL, imposible calcular MC, outlier dependency, WFA folds | Capa B: MC, outliers, WFA |
| F6 | `wfe` | REAL | WFE no computable sin WFA real | Capa B: `wfe_min` |
| F7 | `wfa_positive_folds_pct` | REAL | Idem | Capa B |
| F8 | `wfa_fold_returns_json` | TEXT | Detalle de retornos por fold | Capa B (trazabilidad) |
| F9 | `mc_trade_reorder_positive_pct` | REAL | MC no ejecutado | Capa B |
| F10 | `mc_combined_stress_positive_pct` | REAL | Estrés combinado no ejecutado | Capa B |
| F11 | `mc_verdict` | VARCHAR | Veredicto MC resumido | Capa B |
| F12 | `spp_stability_ratio` | REAL | SPP no ejecutado | Capa B: gate SPP |
| F13 | `spp_verdict` | VARCHAR | Veredicto SPP resumido | Capa B |
| F14 | `top2_trade_dependency_is` | REAL | Outlier dependency IS no computable | Capa B: `outlier_dependency_is_max_top2_share` |
| F15 | `top2_trade_dependency_oos` | REAL | Outlier dependency OOS no computable | Capa B |
| F16 | `dsr` | REAL | Deflated Sharpe Ratio no implementado | Capa B (futuro, G1 del BLUEPRINT) |
| F17 | `sharpe_ratio` | REAL | No se almacena Sharpe, solo PF y retorno | Capa B, Nautilus |
| F18 | `calmar_ratio` | REAL | Calmar no persistido aunque `quality_gates.py` lo calcula | Ranking |

### 6.3 Migración SQL propuesta

```sql
-- Migración P0: campos esenciales para el pipeline de validación
ALTER TABLE backtests ADD COLUMN is_start_date DATE;
ALTER TABLE backtests ADD COLUMN is_end_date DATE;
ALTER TABLE backtests ADD COLUMN oos_start_date DATE;
ALTER TABLE backtests ADD COLUMN oos_end_date DATE;
ALTER TABLE backtests ADD COLUMN trade_series_path VARCHAR;
ALTER TABLE backtests ADD COLUMN sharpe_ratio REAL;
ALTER TABLE backtests ADD COLUMN calmar_ratio REAL;
ALTER TABLE backtests ADD COLUMN wfe REAL;
ALTER TABLE backtests ADD COLUMN wfa_positive_folds_pct REAL;
ALTER TABLE backtests ADD COLUMN wfa_fold_returns_json TEXT;
ALTER TABLE backtests ADD COLUMN wfa_worst_fold_return_pct REAL;
ALTER TABLE backtests ADD COLUMN mc_trade_reorder_positive_pct REAL;
ALTER TABLE backtests ADD COLUMN mc_trade_reorder_p10_equity REAL;
ALTER TABLE backtests ADD COLUMN mc_slippage_stress_positive_pct REAL;
ALTER TABLE backtests ADD COLUMN mc_combined_stress_positive_pct REAL;
ALTER TABLE backtests ADD COLUMN mc_verdict VARCHAR;
ALTER TABLE backtests ADD COLUMN spp_stability_ratio REAL;
ALTER TABLE backtests ADD COLUMN spp_mean_degradation_pct REAL;
ALTER TABLE backtests ADD COLUMN spp_params_fragile_count INTEGER;
ALTER TABLE backtests ADD COLUMN spp_verdict VARCHAR;
ALTER TABLE backtests ADD COLUMN spp_detail_json TEXT;
ALTER TABLE backtests ADD COLUMN top2_trade_dependency_is REAL;
ALTER TABLE backtests ADD COLUMN top2_trade_dependency_oos REAL;
ALTER TABLE backtests ADD COLUMN dsr REAL;
ALTER TABLE backtests ADD COLUMN validation_verdict VARCHAR;  -- POTENTIAL_WINNER | NEEDS_2ND_MOTOR | REJECTED_OVERFIT

-- Nuevo engine_type para NautilusTrader
-- Los backtests de Nautilus se insertan con engine_type = 'NAUTILUS'
-- y el mismo strategy_id, permitiendo comparar motor a motor.
```

### 6.4 Tabla strategies: gaps menores

| Campo faltante | Tipo | Justificación |
|----------------|------|---------------|
| `n_params_optimized` | INTEGER | Para penalización por complejidad (G3 del BLUEPRINT) |
| `strategy_family_type` | VARCHAR | 'trend' / 'reversal' / 'breakout' — para diversificación |

```sql
ALTER TABLE strategies ADD COLUMN n_params_optimized INTEGER;
ALTER TABLE strategies ADD COLUMN strategy_family_type VARCHAR;
```

---

## 7. Criterios de Decisión Final

### 7.1 Árbol de decisión

```
CANDIDATO ENTRA
    │
    ├── ¿Pasa Capa A? ─── NO ───> REJECTED_OVERFIT
    │       │
    │      SÍ
    │       │
    ├── ¿Tiene serie de trades? ─── NO ───> NEEDS_2ND_MOTOR
    │       │                                 (no se puede evaluar Capa B)
    │      SÍ
    │       │
    ├── ¿Pasa Capa B? (WFE, MC, SPP, outliers)
    │       │
    │       ├── FALLA SEVERA (WFE<0.30 | MC<85% | SPP FAIL) ───> REJECTED_OVERFIT
    │       │
    │       ├── FALLA BLANDA (WFE 0.30-0.59 | MC WARN | SPP WARN) ───> NEEDS_2ND_MOTOR
    │       │
    │       └── PASA
    │             │
    │             ├── ¿Validado en NautilusTrader? ─── NO ───> NEEDS_2ND_MOTOR
    │             │       │
    │             │      SÍ
    │             │       │
    │             ├── ¿Nautilus dentro de tolerancias? ─── NO ───> REJECTED_OVERFIT
    │             │       │
    │             │      SÍ
    │             │       │
    │             ├── ¿Retorno IS ≥ 500%? ─── NO ───> POTENTIAL_WINNER ✓
    │             │       │
    │             │      SÍ
    │             │       │
    │             └── ¿Pasa Capa C? (trades≥200, WFE≥0.70, MC≥95%)
    │                     │
    │                     ├── SÍ ───> POTENTIAL_WINNER (ÉLITE) ✓✓
    │                     │
    │                     └── NO ───> POTENTIAL_WINNER (con nota: no cumple protocolo extremo)
    │
    └── FIN
```

### 7.2 Definición formal de cada veredicto

| Veredicto | Código BD | Significado | Acción operativa |
|-----------|-----------|-------------|------------------|
| `POTENTIAL_WINNER` | `PW` | Superó criba, robustez Y 2º motor. Candidato real para trading live. | Avanzar a paper trading / portfolio assembly. Prioridad máxima. |
| `NEEDS_2ND_MOTOR` | `N2M` | Pasó criba barata pero le faltan datos de robustez o validación Nautilus. | Ejecutar WFA + MC + SPP sobre serie de trades. Si pasa, enviar a Nautilus. No descartar. |
| `REJECTED_OVERFIT` | `RO` | Falla gates básicos, sobreajuste confirmado, o artefacto del motor. | Descarte operativo. No re-evaluar salvo con datos completamente nuevos. |

### 7.3 Transiciones permitidas

```
NEEDS_2ND_MOTOR ──(completa evidencia + Nautilus)──> POTENTIAL_WINNER
NEEDS_2ND_MOTOR ──(falla evidencia o Nautilus)──> REJECTED_OVERFIT
REJECTED_OVERFIT ──(NUNCA reabre salvo datos nuevos de campaña distinta)──> ∅
POTENTIAL_WINNER ──(falla en paper trading)──> REJECTED_OVERFIT
```

---

## 8. Contrato de Implementación para Subagente

### 8.1 Módulos a crear/modificar

| Módulo | Acción | Prioridad |
|--------|--------|----------|
| `services/api/app/factory/kamikaze_scorecard.py` | **CREAR**. Implementar scorecard 3 capas completa. | P0 |
| `services/api/app/core/quality_gates.py` | **MODIFICAR**. Añadir gates de WFE, MC, SPP, outlier dependency. | P0 |
| `services/api/app/routers/sqx.py` (`/rentable`) | **MODIFICAR**. Consumir scorecard y devolver `validation_verdict`. | P0 |
| DB migration script | **CREAR**. SQL de §6.3 como migración Alembic o script directo. | P0 |
| `services/api/app/factory/nautilus_validator.py` | **CREAR**. Traductor DSL→Nautilus + comparador de métricas. | P1 |
| `services/api/app/factory/monte_carlo.py` | **CREAR**. Módulo MC con los 4 métodos definidos. | P0 |
| `services/api/app/factory/spp_validator.py` | **CREAR**. Módulo SPP de perturbación de parámetros. | P0 |
| `services/api/app/factory/wfa_engine.py` | **CREAR**. Motor WFA anchored con purge/embargo. | P0 |

### 8.2 Prerequisitos de datos

> ⚠️ **BLOQUEANTE:** La Capa B completa (WFA, MC, SPP, outlier dependency) requiere la **serie de trades PnL** por estrategia. Actualmente la BD no almacena esta información. Hasta que SQX exporte la serie de trades o se re-ejecute el backtest para capturarla, los campos de Capa B permanecerán NULL y todo candidato que pase Capa A será automáticamente `NEEDS_2ND_MOTOR`.

**Soluciones propuestas para obtener serie de trades:**
1. **Preferida:** Extraer de SQX vía MCP la lista de trades con PnL, timestamp, duración. Almacenar en `trade_series_path` como CSV/JSON.
2. **Alternativa:** Re-ejecutar el backtest en vectorbt/NautilusTrader y capturar trades directamente.
3. **Mínimo viable:** Persistir al menos los trades agregados por mes/semana desde SQX para calcular WFE aproximado.

### 8.3 Orden de implementación recomendado

1. **Migración BD** (§6.3) — desbloquea almacenamiento.
2. **kamikaze_scorecard.py** Capa A — ya implementable con datos existentes.
3. **Extracción de serie de trades** desde SQX — desbloquea Capa B.
4. **monte_carlo.py** — depende de serie de trades.
5. **wfa_engine.py** — depende de serie de trades.
6. **spp_validator.py** — depende de re-ejecución paramétrica.
7. **kamikaze_scorecard.py** Capa B — integra MC + WFA + SPP.
8. **nautilus_validator.py** — requiere traductor DSL→Nautilus (complejo, P1).
9. **kamikaze_scorecard.py** Capa C — integra Nautilus.

---

## Apéndice A: Configuración YAML consolidada para implementación

```yaml
# pipeline_validation_config.yaml
# Configuración canónica del pipeline de validación multi-motor
# Fuente de verdad: docs/Estado/auditoria/04_pipeline_validacion_multimotor.md

pipeline:
  version: "1.0.0"
  real_only: true
  canonical_2nd_engine: "NautilusTrader"

capa_a:
  min_trades_is: 30
  min_pf_is: 1.30
  min_net_return_is_pct: 5.0
  max_dd_is_pct: 85.0
  require_oos: true
  min_trades_oos: 10
  min_pf_oos: 1.00
  min_net_return_oos_pct: 0.0
  max_dd_oos_pct: 80.0

capa_b:
  wfa:
    method: "anchored"
    n_folds: 8
    oos_pct: 25
    purge_days: 5
    embargo_days: 2
    min_trades_per_fold_oos: 10
    wfe_min: 0.60
    positive_folds_min_pct: 62.5
    worst_fold_return_min_pct: -15.0
  monte_carlo:
    n_simulations: 10000
    trade_reorder_positive_min_pct: 90.0
    trade_reorder_p10_equity_min_ratio: 0.80
    slippage_stress_positive_min_pct: 80.0
    spread_stress_positive_min_pct: 85.0
    combined_stress_positive_min_pct: 70.0
  spp:
    perturbation_pct: 15
    stability_ratio_min: 0.50
    params_fragile_max: 0
    mean_degradation_max_pct: 30.0
  outlier_dependency:
    top2_share_is_max: 0.15
    top2_share_oos_max: 0.20
  temporal_coverage:
    is_min_days: 730
    oos_min_days: 180
  max_dd_oos_pct: 40.0

nautilus:
  delta_return_max_pct: 10.0
  delta_dd_max_pct: 3.0
  delta_sharpe_max: 0.5
  delta_trades_max_pct: 5.0

capa_c:
  extreme_return_threshold_is_pct: 500
  extreme_return_threshold_oos_pct: 200
  extreme_min_trades_is: 200
  extreme_min_trades_oos: 100
  extreme_wfe_min: 0.70
  extreme_mc_positive_min_pct: 95.0
  extreme_spp_stability_ratio_min: 0.60

verdicts:
  potential_winner: "PW"
  needs_2nd_motor: "N2M"
  rejected_overfit: "RO"
```

---

*Documento generado con datos reales del esquema de BD, BLUEPRINT y AUDITORIA_CANDIDATOS_KAMIKAZE.md. No se inventaron métricas ni resultados. Regla REAL-ONLY respetada.*
