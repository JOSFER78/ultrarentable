# BLUEPRINT: Controlador de Estrategias de Nivel Mundial
## Selección de estrategias ganadoras (miles de %) entre miles de candidatos de StrategyQuant X SIN overfit

**Tipo:** Diseño / Investigación  
**Estado:** Borrador de blueprint  
**Alcance:** No toca código de la app ni `/home/ubuntu/StrategyQuantX`; define el diseño para un controlador de selección de élite.

---

## 1. MEJORES PRÁCTICAS GLOBALES DE SELECCIÓN (QUÉ HACEN LOS PROFESIONALES)

Los quants de élite y firmas como **WorldQuant**, **Two Sigma**, **Renaissance**, **TopStep**, **Fundur**, **PTJ**, **Alphacet** y shops de prop trading con screening masivo no se fían del retorno puntual de una muestra. Sus pilares comunes son:

### 1.1 Pruebas múltiples ajustadas (Multiple Testing Adjustment)
- **Sharpe deflacionado** (Bailey & López de Prado): ajusta el Sharpe observado por el número de configuraciones probadas y la longitud de la muestra. Sin esto, un Sharpe de 3 entre 10.000 trials puede ser casualidad.
- **Criterios de family-wise error rate (FWER) y FDR**: Romano-Wolf, White’s Reality Check, **SDA** (Stepwise Data-Auditing), **BHY** (Benjamini-Hochberg-Yekutieli). Evitan que los falsos positivos se cuelen solo por volumen.
- **Combinación de pruebas**: no confiar en un único test (t-test de retornos, bootstrap, walk-forward), sino requerir que la estrategia sobreviva a **varias pruebas ortogonales**.

### 1.2 Walk-forward con WFE alto y estructura IS/OOS real
- **Walk-forward “anidado”**: IS para selección de parámetros, OOS para validación de cada reentreno.
- **WFE (Walk-Forward Efficiency)**: ratio de retorno OOS / IS. WorldQuant exige WFE alto (> 0.60–0.80 en entornos ruidosos). Si WFE es muy bajo, la estrategia está memorizando IS.
- **CPCV** (Combinatorially Symmetric Cross-Validation with purge/embargo): usa todas las particiones posibles sin fuga de información y con bloqueos entre train/test. Es el gold standard moderno frente al K-fold ingenuo.
- **Purging y embargo**: eliminar del entrenamiento cualquier muestra que se solape temporalmente con el test (embargo) y limpiar la primera ventana después de eventos (purging).

### 1.3 Mínimos de robustez y penalización por complejidad
- **Mínimo de trades independientes**: decenas o cientos, no 5 trades milagrosos. WorldQuant a menudo exige > 100–300 trades OOS dependientes del instrumento/timeframe.
- **Penalización por parámetros**: AIC/BIC o penalización directa por número de parámetros optimizados. Cuantos más parámetros, más improbable que la estrategia sea real. López de Prado propone **Deflated Sharpe Ratio (DSR)** como métrica unificada.
- **Estabilidad de la curva de equity**: no vale un pico; se requiere monotonía o drawdowns controlados a lo largo del OOS.

### 1.4 Juez ciego, portafolios y sesgo de supervivencia
- **Juez ciego / selection-blind ranking**: separar la generación de candidatos de su evaluación para evitar sesgo de confirmación.
- **Portafolio de muchas estrategias mediocres vs pocas extraordinarias**: en entornos de alta competencia, muchas estrategias con Sharpe modesto pero consistentes superan a una “estrella” overfit.
- **Sesgo de supervivencia**: descartar estrategias que solo funcionan porque el instrumento/era no murió. Requiere validación en activos secundarios, universos paralelos o periodos de crisis.

---

## 2. FILTRO DE “MILES DE %” VERIFICABLE: PROTOCOLO CONCRETO

Un candidato que en IS muestre 1000%+ de retorno debe demostrar que **ese resultado es insesgado y reproducible**. El protocolo mínimo es:

### 2.1 Requisitos de entrada al protocolo “1000%+”
1. **IS no es el mundo real**: el retorno de IS se descuenta como métrica prioritaria; se convierte en un “sospechoso” hasta superar OOS.
2. **Mínimo de trades independientes**:
   - Para retornos extremos (>500% o >1000%), exigir **N ≥ 200 trades independientes** en IS.
   - En OOS, **N ≥ 100 trades independientes**.
3. **Cobertura temporal**:
   - IS cubre **al menos 2–3 años** de datos diarios o **6–12 meses** en intradía.
   - OOS cubre **al menos 6 meses** reales (no sintéticos), preferiblemente con eventos de estrés (COVID, flash crash, cambios de Fed).
4. **No outlier-dependent**:
   - El retorno total no puede depender de **1 o 2 trades**.
   - Métrica: **Top-2 trades / total profit < 15%** en IS y < 20% en OOS.
   - Si un solo trade explica >10% del retorno, descartar o marcar “no robusto”.

### 2.2 Supervivencia a walk-forward / OOS real
1. **Walk-forward OOS positivo**: al menos el **50% de los bloques OOS** deben ser positivos (mejor ≥ 60%).
2. **WFE >= 0.60**: retorno OOS / retorno IS >= 0.60. Si WFE < 0.60, la estrategia probablemente está sobreoptimizada.
3. **Drawdown OOS controlado**: **Max DD OOS < 40%** (preferiblemente < 25%).
4. **No ruido**:
   - P-value de la prueba de aleatoriedad de retornos > 0.05 (no se rechaza que sea ruido).
   - O test de rachas o autocorrelación de retornos: sin evidencia de clustering patológico.

### 2.3 Sesgo de supervivencia y Monte Carlo
1. **Sesgo de supervivencia**:
   - Si la estrategia opera sobre activos que podrían dejar de existir/volverse ilíquidos, simular **censura** o probar en un universo “muerto” de activos.
   - Evitar periodos donde solo sobrevivieron los ganadores.
2. **Monte Carlo**:
   - Simular **10.000–50.000 escenarios** de reordenamiento de trades o bootstrap de retornos.
   - Métrica clave: **% de veces que equity final > 0** (o > umbral mínimo) en MC.
   - Para retornos extremos, exigir **≥ 90% de simulaciones con equity final positivo** en OOS y **≥ 95%** en IS.
   - Además, **p10 / p90 del equity final**: el p10 no puede ser pérdida catastrófica.

### 2.4 Validación en 2º motor (Nautilus)
- La estrategia debe **reproducirse en un motor independiente** (Nautilus u otro backtester).
- Si en Nautilus el retorno cae > 30% o el drawdown sube > 20%, descartar.
- Diferencias aceptables: ±5% en Sharpe, ±10% en retorno total, ±3% en Max DD.
- Esto detecta **bugs, slippage mal modelada, lookahead bias, overfitting al motor**.

---

## 3. ARQUITECTURA RECOMENDADA DEL CONTROLADOR

### 3.1 Pipeline macro: desde SQX hasta Champion

```
[StrategyQuant X] --> [Captura Masiva] --> [Criba Barata] --> [Filtros de Evidencia]
                                                               |
                                                               v
                                                    [Ranking por Valor Esperado + Multiplicador]
                                                               |
                                                               v
                                                    [Validación Adversarial]
                                                               |
                                                               v
                                                    [2º Motor / Nautilus]
                                                               |
                                                               v
                                                          [Champion]
```

### 3.2 Etapas detalladas

#### Etapa 1: StrategyQuant X → Captura Masiva
- **Entrada**: runs del proyecto `kamikaze` con configuraciones aleatorizadas (seed, lógicas, timeframes, mercados).
- **Salida**: catálogo de candidatos crudos con métricas IS completas (retorno, Sharpe, Max DD, trades, parámetros).
- **Objetivo**: generar **10.000–100.000 candidatos** por campaña.
- **Control**: cada run debe usar una semilla y configuración distintas para evitar sesgo.

#### Etapa 2: Criba Barata (vectorbt / fast)
- **Entrada**: catálogo crudo.
- **Procesamiento**:
  - Filtros rápidos sin datos de alta precisión: `trades >= 30`, `Sharpe > 0.5`, `Max DD < 60%`, `profit_factor > 1.2`, ` días activos > 30%`.
  - Eliminar duplicados por hash de estrategia (lógica + parámetros clave).
  - Eliminar clones: estrategias idénticas con distinto seed.
- **Umbrales recomendados**:
  - `trades >= 50`
  - `profit_factor >= 1.3`
  - `expectancy > 0`
  - `Max DD < 50%`
- **Salida**: candidatos “verdes” (5.000–20.000).
- **Objetivo**: reducir coste computacional para etapas pesadas.

#### Etapa 3: Filtros de Evidencia (bootstrap / IS-OOS / walk-forward)
- **Entrada**: candidatos verdes.
- **Procesamiento**:
  1. **Bootstrap de retornos** (strategy_evidence.py existente): exigir `p_bootstrap < 0.05` para retorno > 0.
  2. **IS-OOS split**: dividir en IS/OOS con purging. Exigir retorno OOS > 0.
  3. **Walk-forward efficiency**: WFE >= 0.60.
  4. **Deflated Sharpe Ratio**: DSR > 2.0 (equivale a ~95% confianza ajustada).
  5. **Temporal coverage**: IS >= 2 años, OOS >= 6 meses.
  6. **Outlier-dependence check**: Top-2 trades < 15% del beneficio total.
- **Umbrales recomendados**:
  - `DSR >= 2.0`
  - `WFE >= 0.60`
  - `OOS return > 0`
  - `bootstrap p-value < 0.05`
- **Salida**: estrategias “robustas” (cientos a pocos miles).
- **Objetivo**: eliminar falsos positivos por suerte o overfit.

#### Etapa 4: Ranking por Valor Esperado + Multiplicador
- **Entrada**: estrategias robustas.
- **Métrica compuesta**:
  - **Valor esperado (EV)**: `expectancy * frecuencia anualizada`.
  - **Multiplicador**: `retorno total OOS / Max DD OOS` (o `Calmar OOS`).
  - **Score final**: combinación ponderada de EV, multiplicador y estabilidad (baja volatilidad de retornos OOS).
- **Umbrales recomendados**:
  - `Calmar OOS >= 1.5`
  - `EV anualizado > umbral mínimo de la cuenta`
  - `estabilidad (std dev de retornos mensuales OOS) < 30%`
- **Salida**: top 50–200 candidatos preseleccionados.
- **Objetivo**: priorizar estrategias que no solo ganan, sino que lo hacen de forma predecible.

#### Etapa 5: Validación Adversarial (adversarial_validation.py existente)
- **Entrada**: top candidatos.
- **Procesamiento**:
  1. **Cost-stress**: comisiones, slippage y spread al doble/triple. La estrategia debe seguir siendo rentable.
  2. **Lockbox OOS**: usar datos de OOS que nunca vieron los parámetros (lockbox estricto).
  3. **Random windows**: probar en ventanas aleatorias de OOS, no solo secuenciales.
  4. **Regime change**: simular mercados laterales, bajistas, de alta volatilidad.
- **Umbrales recomendados**:
  - Rentable bajo cost-stress 2x/3x.
  - Pasa ≥ 70% de random windows OOS.
- **Salida**: estrategias “adversarialmente validadas” (10–50).
- **Objetivo**: detectar overfit a costes/slippage/periodos favorables.

#### Etapa 6: Validación en 2º Motor (Nautilus)
- **Entrada**: estrategias validadas adversarialmente.
- **Procesamiento**:
  - Traducir la lógica a Nautilus (motor independiente).
  - Ejecutar en los mismos datos IS/OOS.
  - Comparar métricas clave: retorno, Sharpe, Max DD, trades.
- **Umbrales recomendados**:
  - Desviación relativa de retorno < 10%.
  - Desviación de Max DD < 3 puntos porcentuales.
  - Sharpe no cae más de 0.5 puntos.
- **Salida**: “Champions” (1–10 estrategias).
- **Objetivo**: eliminar artefactos de implementación, lookahead bias o dependencia del motor.

### 3.3 Tabla resumen de etapas

| Etapa | Entrada | Salida | Métrica clave | Umbral |
|-------|---------|--------|---------------|--------|
| 1 Captura | Runs SQX | Candidatos crudos | # candidatos | 10k–100k |
| 2 Criba | Crudos | Verdes | Trades, PF, DD | Trades≥50, PF≥1.3 |
| 3 Evidencia | Verdes | Robustos | DSR, WFE, OOS | DSR≥2.0, WFE≥0.60 |
| 4 Ranking | Robustos | Preseleccionados | EV + Multiplicador | Calmar≥1.5 |
| 5 Adversarial | Preseleccionados | Adversariales | Cost-stress, lockbox | Rentable 2x costes |
| 6 2º Motor | Adversariales | Champions | Reproducibilidad Nautilus | Δ retorno < 10% |

---

## 4. CONTROL: EVITAR QUE “SIEMPRE DÉ LO MISMO” Y MEDIR EXPLORACIÓN

### 4.1 Variación de seed y configuración entre runs
- **Problema**: si SQX corre con la misma semilla/config, el espacio de búsqueda no se explora y se repiten clones.
- **Solución**:
  - Rotación obligatoria de **semillas aleatorias** y **listas de activos** por campaña.
  - Variar el ** orden de generación de reglas** y **rangos de parámetros** entre batches.
  - Si el proyecto usa `run_project kamikaze`, inyectar un “nonce” de campaña en la configuración de búsqueda.
- **Métrica**: **hash diversity** = número de hashes únicos de estrategia por campaña / total generados. Objetivo: > 95% únicos.

### 4.2 Medir que la búsqueda está explorando
- **Diversidad de hashes**:
  - Cada estrategia se hashea por su árbol de reglas + parámetros clave.
  - Si en una campaña la diversidad < 80%, la búsqueda está estancada.
- **Candidatos únicos por run**:
  - Medir cuántos candidatos únicos aparecen por cada 1.000 generados.
  - Objetivo: > 90% únicos.
- **Cobertura del espacio**:
  - Tracking de familias de estrategias (tendencia, reversión, breakout, etc.).
  - Si una familia domina > 60% del top 100, forzar diversificación en la siguiente campaña.
- **Repetición de clones**:
  - Sistema de “seen hashes” persistente (SQLite/Redis). Si un hash ya fue visto en campañas anteriores, marcar como “ya evaluado” y no re-evaluar a menos que cambien los datos.

### 4.3 Evitar sobreoptimización de la semilla
- No premiar estrategias que solo funcionan con una semilla específica.
- Requerir que la estrategia sobreviva a **al menos 3 seeds distintas** en IS (no solo la semilla ganadora).
- En OOS, repetir la validación con **2 seeds distintas**.

---

## 5. QUÉ FALTA EN EL CÓDIGO ACTUAL (GAPS vs BLUEPRINT)

### 5.1 Módulos existentes y su estado actual

| Módulo | Funcionalidad actual | Rol en el blueprint | Estado |
|--------|----------------------|---------------------|--------|
| `strategy_evidence.py` | Bootstrap de retornos, temporal coverage, best_trade_dependency, alternatives_tried, expected_holding_bars. | Etapa 3 (Filtros de Evidencia) parcial. | **Parcial** |
| `adversarial_validation.py` | Walk-forward windows, cost-stress, lockbox OOS, random windows. | Etapa 5 (Validación Adversarial). | **Bueno**, pero le falta regime change y cost-stress 2x/3x estricto. |
| `quality_gates.py` | `is_ruinous(dd>=100)`, `calmar_ratio`, `rentable()`. | Etapa 2 (Criba Barata) y etapa 4 (Ranking). | **Básico**, pero insuficiente para DSR, WFE, etc. |
| Motor de búsqueda SQX | Generación masiva en `/home/ubuntu/StrategyQuantX` (controlado por otro subagente). | Etapa 1 (Captura). | **Externo**, no tocar. |

### 5.2 Gaps concretos para llegar al controlador mundial

| # | Gap | Impacto | Solución propuesta |
|---|-----|---------|--------------------|
| G1 | **No hay Deflated Sharpe Ratio (DSR) ni Sharpe ajustado por múltiples pruebas.** | Criba de falsos positivos muy débil con miles de candidatos. | Implementar DSR (Bailey & López de Prado) y, como mínimo, Romano-Wolf o White’s Reality Check en `strategy_evidence.py`. |
| G2 | **No hay CPCV ni purging/embargo estricto.** | Fuga de información entre IS y OOS, sobrestimación de robustez. | Implementar CPCV con purge/embargo como split estándar en `strategy_evidence.py` o nuevo módulo `validation_splits.py`. |
| G3 | **No hay penalización por parámetros ni complejidad (AIC/BIC).** | Se cuelan estrategias con 10+ parámetros sobreoptimizados. | Añadir `complexity_penalty()` y `num_params` en `quality_gates.py`; combinarlo con DSR. |
| G4 | **No hay validación en 2º motor (Nautilus).** | No se detectan artefactos de implementación ni lookahead bias específicos de SQX. | Crear módulo `nautilus_validator.py` que reciba la lógica y ejecute en Nautilus, comparando métricas clave. |
| G5 | **No hay protocolo “1000%+ verificable”.** | El controlador no sabe priorizar ni filtrar los retornos extremos. | Crear `protocol_extreme_returns.py` con los requisitos de este blueprint (outlier-dependence, MC, OOS mínimo). |
| G6 | **No hay control de diversidad ni anti-clonación.** | La búsqueda se estanca, repite estrategias y sobreoptimiza la semilla. | Añadir sistema de hashes persistentes y métricas de diversidad (`hash_diversity`, `unique_candidates_per_run`). |
| G7 | **No hay integración de portafolio.** | El controlador selecciona estrategias individuales, no un conjunto equilibrado. | Diseñar módulo `portfolio_assembler.py` que combine estrategias robustas minimizando correlación y drawdown agregado. |
| G8 | **No hay Monte Carlo avanzado en el pipeline.** | No se mide la robustez probabilística del equity final. | Extender `strategy_evidence.py` con MC de trades/bootstrap con percentiles p10/p90. |
| G9 | **Falta “juez ciego” y protocolo de selección ciega.** | Sesgo de confirmación humano o del sistema. | Diseñar flujo de evaluación ciega donde el ranking no conozca IS/OOS hasta el final de la fase. |

### 5.3 Mapa de priorización sugerida

1. **Prioridad Alta (P0)**: G1, G2, G5, G6. Sin esto, el controlador sigue filtrando mal y repitiendo clones.
2. **Prioridad Media (P1)**: G3, G4, G8. Mejoran la robustez pero dependen de P0.
3. **Prioridad Baja (P2)**: G7, G9. Complementan la calidad pero no bloquean la operación básica.

---

## 6. RESUMEN EJECUTIVO

Este blueprint define un **controlador de élite** para StrategyQuant X con las siguientes garantías:

1. **Selección profesional**: aplica DSR, CPCV, walk-forward con WFE, múltiples pruebas ortogonales y penalización por complejidad, igual que WorldQuant y quants de primer nivel.
2. **Filtro verificable para retornos extremos**: exige cobertura temporal, mínimo de trades independientes, OOS positivo, no outlier-dependencia, Monte Carlo y validación en 2º motor.
3. **Arquitectura por etapas**: desde captura masiva hasta champion, con criba barata, filtros de evidencia, ranking compuesto, validación adversarial y motor independiente.
4. **Control de exploración**: rotación de seeds, hash diversity, seen-hashes y anti-clonación para que la búsqueda no se estanque.
5. **Gap analysis**: identifica 9 gaps concretos en el código actual (`strategy_evidence.py`, `adversarial_validation.py`, `quality_gates.py`) y prioriza su cierre para alcanzar el nivel mundial.

**Próximo paso recomendado**: cerrar los gaps P0 en orden (G1 → G2 → G5 → G6) y después montar el pipeline unificado.
