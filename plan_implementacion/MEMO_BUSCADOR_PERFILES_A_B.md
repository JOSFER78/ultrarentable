# Memo — Diseño de mejora del buscador de estrategias (capturado 2026-08-09)
> Origen: sesión de Hermes `20260809_085051_13c434` (claude-opus-5, desktop, perfil default).
> Esta sesión no tenía acceso al workspace, por lo que dio este diseño basándose en los
> síntomas del usuario (el buscador no consigue estrategias de miles de % y no cubre bien
> fondeo con control de DD diario). Es un diseño valioso y complementario — se captura aquí
> para que los multiagentes lo implementen, integrado con lo que ya existe en el proyecto.

---

## El problema de fondo (tal como lo diagnostica ese diseño)
- Buscar "miles de %" por retorno bruto del backtest es **la causa del problema**, no la solución.
  Un retorno de 4 dígitos casi nunca viene de una señal mejor: viene de:
  1. **Compounding** sobre muchos años.
  2. **Sizing** (fracción de riesgo por operación) agresiva, que normalmente no está en el espacio de búsqueda.
  3. **Sobreajuste**, cuando el optimizador ordena por retorno → prefiere la curva más frágil.
- Fallos que explican los síntomas:
  - Fitness única para dos objetivos opuestos (ultra vs fondeo).
  - DD medido sobre cierres, no intrabar → subestima el DD intradía.
  - Sizing fijo fuera del espacio de búsqueda → techo de retorno fijo.
  - Búsqueda por grid (desperdicia presupuesto).
  - Sin walk-forward ni gate out-of-sample (no distingue edge de ruido).
  - Espacio de búsqueda estrecho (1 instrumento, 1 timeframe, sin filtros de sesión/régimen).
  - Costes optimistas (sin spread/slippage realistas → dominan sistemas hft que mueren en real).

---

## SOLUCIÓN: dos perfiles, un motor

### Perfil A — Growth (ULTRA-rentable)
```
fitness_A = CAGR_oos × estabilidad
estabilidad = (1 - dispersión_de_CAGR_entre_folds) × ratio_folds_positivos

restricciones duras (descarte, NO penalización):
  trades_oos  >= 150
  folds_oos_positivos >= 70%
  max_DD_intradía  <= 35%
  peor_mes  >= -20%
  tiempo_en_recuperación_max <= 12 meses
```
Los "miles de %" salen del SIZING, no de la señal: meter la fracción de riesgo en el espacio de
búsqueda con **Kelly fraccional acotado** (`f ∈ [0.005, 0.05]`) y dejar que el optimizador lo
resuelva bajo la restricción de DD.

### Perfil B — Funding (FONDEO con DD diario)
```
fitness_B = P(pasar_challenge) × P(sobrevivir_90d | pasado)

restricciones duras:
  max_DD_diario_intradía <= 0.6 × límite_diario_de_la_fondeadora
  max_DD_total_intradía  <= 0.5 × límite_total
  P(violar_DD_diario)    <= 2%
  días_hasta_target      <= límite del programa
```
CRÍTICO: el DD diario debe medirse **intrabar** (no sobre cierres). Requiere resample a M1 (o tick)
para reconstruir el peor punto de cada día. La fondeadora aprueba estrategias que revientan la
regla diaria si mides con equity al cierre.

---

## Motor de búsqueda (sustituir grid por):
```
1. Sampleo latino hipercubo       → 500 candidatos, solo train
2. Filtro barato                  → descarta por restricciones duras (rápido, sin OOS)
3. Optimización bayesiana (TPE)   → 2000 evaluaciones sobre supervivientes
4. Walk-forward anclado           → 6 folds, gap de 1 semana entre train y test
5. Gate de robustez               → las 4 pruebas de abajo
6. Monte Carlo de trades          → 10k reordenamientos; reporta p5 CAGR y p95 DD
```

### Gate de robustez (edge vs suerte): un candidato pasa solo si sobrevive las 4
- **Sensibilidad de parámetros**: perturbar ±15%; fitness no cae más del 30%.
- **Vecindad**: candidatos adyacentes también rentables (óptimo aislado = ruido).
- **Coste estresado**: revalidar con spread ×2 y slippage ×2.
- **Cross-instrumento**: degrada con gracia en instrumento correlacionado sin reoptimizar.

---

## Dónde está el retorno que no se encuentra (ampliar espacio por impacto)
1. **Filtro de sesión** (Londres / NY / solape) — la mayor ganancia por complejidad.
2. **Filtro de régimen** (ADX / volatilidad realizada / percentil de ATR) para apagar donde no hay edge.
3. **Multi-timeframe**: señal en el bajo, sesgo en el alto.
4. **Cartera de 3-5 variantes descorrelacionadas** en vez de una única (baja DD agregado,
   permite subir la fracción de riesgo → retorno compuesto se multiplica de verdad).

---

## Reparto para los multiagentes (cada bloque independiente y testeable)

| Agente | Entregable | Criterio de aceptación |
|---|---|---|
| A1 Datos | Loader M1 + reconstrucción intrabar de equity | DD intradía verificado contra caso conocido |
| A2 Costes | Spread variable por sesión, comisión, slippage | Backtest de referencia degrada de forma coherente |
| A3 Métricas | CAGR, DD intradía, DD diario, Sharpe, tiempo en recuperación, peor mes | Suite de tests con curvas sintéticas |
| A4 Fitness | fitness_A y fitness_B; restricciones duras separadas del score | Restricciones descartan, no penalizan |
| A5 Motor | TPE + walk-forward anclado con gap | Reproducible con semilla fija |
| A6 Gate | Las 4 pruebas de robustez | Un candidato sobreajustado conocido debe ser rechazado |
| A7 Monte Carlo | Simulador de challenge + reordenamiento de trades | P(pasar) calibrada contra reglas reales de la fondeadora |
| A8 Reporte | Ficha por estrategia con métricas train/OOS/estresado | Ninguna estrategia se publica sin OOS |

Dependencias: A1 → A2 → A3 → A4 → A5 → A6 → A7 → A8 (A1/A2/A3 paralelizables tras acordar interfaces).

**Regla de gobernanza:** ninguna estrategia se reporta ni se rankea por métricas de TRAIN.
Train solo selecciona; OOS decide.

---

## Integración con lo que ya existe (estado actual del proyecto)
- Ya hay `BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md` (protocolo de miles de % + WFE/OOS/MC).
- Ya hay `AUDITORIA_CANDIDATOS_KAMIKAZE.md` (scorecard de 3 capas; hoy 0 winners, mejor ~2.24% IS).
- Ya hay `GUIA_EXPERTO_USAR_SQUANT.md` y el motor SQX desbloqueado (genera candidatos 4.1.x reales).
- Este memo añade: **separación de fitness por perfil (A/B), sizing con Kelly en el espacio de
  búsqueda, DD intrabar (resample M1), filtros de sesión/régimen, cartera descorrelacionada,
  y el reparto A1-A8 accionable**.
- SIGUIENTE PASO CONCRETO: integrar este diseño en el plan de orquestación
  (`ORQUESTACION_MOTOR_BUSQUEDA_20260809.md`) y despachar a los multiagentes A1-A8 en el orden
  de dependencias, arrancando por A1 (datos M1 + DD intrabar) y A4 (fitness A/B).
