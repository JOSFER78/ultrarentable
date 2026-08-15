# 13 — Especificación Operativa del Generador Ideal de StrategyQuant (Caza de Balas Ultrarentables)

> **Documento Canónico de Especificación y Contrato de Validación**  
> **Fecha**: 2026-08-09 | **Proyecto**: Ultrarentable (BingX Ultra Strategy Lab)  
> **Motor de Inferencia**: StrategyQuant X (SQX) | **Doctrina**: REAL-ONLY & Anti-Overfit  
> **Ubicación Canónica**: `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/docs/Estado/auditoria/13_especificacion_generador_ideal.md`

---

## 1. Introducción y Propósito del Contrato

El propósito de este documento es definir la **especificación clara, cuantitativa y no ambigua** de cómo debe comportarse el generador de estrategias de StrategyQuant X (SQX) para descubrir e identificar estrategias **ultrarentables** (definidas operativamente como **"BALAS"**).

Este documento sirve como el **contrato de validación definitivo**: cualquier plan de generación, script de automatización (`computer_use` / MCP) o pipeline de ingesta propuesto dentro del proyecto *Ultrarentable* **debe ser auditado y validado contra las reglas y umbrales aquí establecidos**.

### Principios Doctrinarios Fundamentales
1. **Una estrategia ultrarentable es una BALA**: Una oportunidad rara caracterizada por una **asimetría extrema** (retorno potencial muy elevado frente a un riesgo/drawdown acotado). No es simplemente "cualquier estrategia con Profit Factor > 1.0 en muestra".
2. **El Out-of-Sample (OOS) es el juez ciego e innegociable**: El In-Sample (IS) solo mide el ajuste a datos pasados. Si una estrategia destaca en IS pero decae o pierde dinero en OOS ($\text{PF}_{\text{OOS}} < 1.0$), es **ruido sobreajustado (curve-fit)** y debe ser descartada de inmediato.
3. **El generador no es su propio validador**: SQX genera e identifica `SQX_CANDIDATE`. La promoción final a `CANONICAL` exige revalidación independiente en un 2º motor (NautilusTrader).
4. **Doctrina REAL-ONLY**: Todos los datos y métricas deben provenir de ejecuciones reales sobre datos existentes en la GUI/motor de SQX, sin invención de resultados ni estimaciones teóricas no verificadas.

---

## 2. Definición Operativa de "Bala" (Métricas Exactas y Umbrales)

Para que una estrategia generada por SQX sea clasificada como una **Bala Ultrarentable**, debe cumplir simultáneamente con los siguientes umbrales métricos estrictos:

| Métrica | Umbral Mínimo / Requerimiento | Justificación Teórica y Operativa |
| :--- | :--- | :--- |
| **Profit Factor In-Sample ($\text{PF}_{\text{IS}}$)** | $\ge 1.30$ | Garantiza la existencia de una ventaja estadística (*edge*) real en la fase de construcción. |
| **Profit Factor Out-of-Sample ($\text{PF}_{\text{OOS}}$)** | $\ge 1.00$ (Estricto) / Deseable $\ge 1.25$ | **Filtro innegociable anti-overfit**. Demuestra generalización en datos no vistos. $\text{PF}_{\text{OOS}} < 1.0$ representa sobreajuste directo. |
| **Ratio Retorno / Drawdown ($\text{Ret/DD}_{\text{OOS}}$)** | $\ge 2.00$ (Perfil A) / $\ge 1.50$ (Perfil B) | Exige asimetría pura. La recompensa debe ser sustancialmente mayor que la peor racha de pérdidas. |
| **Trades Mínimos In-Sample ($\text{Trades}_{\text{IS}}$)** | $\ge 20$ (Filtro base) / $\ge 150$ (Perfil A) / $\ge 100$ (Perfil B) | Evita la ilusión de significancia estadística provocada por muestras pequeñas de 3–10 trades. |
| **Trades Mínimos Out-of-Sample ($\text{Trades}_{\text{OOS}}$)** | $\ge 15$ (Filtro base) / $\ge 50$ (Perfil A) / $\ge 30$ (Perfil B) | Asegura que el rendimiento OOS no sea fruto de 1 o 2 trades afortunados en la cola derecha. |
| **Drawdown Máximo % ($\text{MaxDD}_{\%}$)** | Perfil A: $\le 35.0\%$ intradía<br>Perfil B: $\le 3.0\%$ diario / $\le 5.0\%$ total | **CRÍTICO**: Debe calcularse obligatoriamente en % sobre Equity real ($\frac{\text{DD}_{\text{USD}}}{\text{Equity}_{\text{Pico}}} \times 100$), NUNCA en USD absolutos. |
| **Consistencia Folds Walk-Forward** | $\ge 70\%$ de folds positivos | En evaluación de 6 folds anclados, al menos 5 folds OOS deben cerrar en beneficio neto positivo. |
| **Tiempo de Estancamiento Máximo** | $\le 365$ días (Perfil A) / $\le 90$ días (Perfil B) | Evita estrategias que pasan años en drawdown lateral congelando capital. |

---

## 3. Función de Fitness Deseada y Justificación

### El Error Histórico a Evitar
Maximizar únicamente el *Net Profit* o el *Profit Factor IS* provoca que el algoritmo genético de SQX seleccione curvas ultra-sobreajustadas, llenas de parámetros frágiles que explotan en cuanto cambian las condiciones de mercado.

### 3.1 Perfil A — Growth / Ultra (Miles de %)
**Fórmula de Fitness**:
$$\text{Fitness}_A = \text{CAGR}_{\text{OOS}} \times \text{Estabilidad}_{\text{WF}}$$

Donde:
$$\text{Estabilidad}_{\text{WF}} = \left( 1 - \frac{\sigma_{\text{CAGR\_fold}}}{\mu_{\text{CAGR\_fold}}} \right) \times \left( \frac{\text{Folds OOS Positivos}}{\text{Total Folds}} \right)$$

* **Justificación**: El objetivo de Perfil A es el crecimiento compuesto acelerado. Al multiplicar el CAGR OOS por la estabilidad entre folds, se penalizan severamente las estrategias que obtienen sus retornos de un único periodo afortunado y se premian los sistemas con crecimiento uniforme a través de múltiples regímenes de mercado.

### 3.2 Perfil B — Fondeo / Prop Firm (Challenge & 90 Días)
**Fórmula de Fitness**:
$$\text{Fitness}_B = \frac{\text{NetReturn}_{\text{OOS}}}{\text{MaxDD}_{\text{OOS\_intrabar}}} \times \text{Consistency\_Score}$$

* **Justificación**: En cuentas de fondeo, el riesgo de ruina o violación del Drawdown Diario Intrabar mata la cuenta instantáneamente. La prioridad no es el retorno bruto, sino maximizar la rentabilidad ajustada al riesgo intrabar estricto, maximizando la probabilidad de superar el reto y sobrevivir los 90 días posteriores.

---

## 4. Gates de Aceptación (Condiciones Duras / Hard Filters)

El generador de SQX debe aplicar **filtros duros de descarte inmediato** (*Hard Filters* en `Rankings & Filtering -> Conditions`). Cualquier candidato que incumpla un solo gate es descartado en tiempo de generación antes de pasar a etapas avanzadas.

```
   [ Candidato Generado ]
             │
             ▼
   ¿PF_IS ≥ 1.30? ──(No)──► [ DESCARTE ]
             │ (Sí)
             ▼
   ¿PF_OOS ≥ 1.00? ──(No)──► [ DESCARTE ]
             │ (Sí)
             ▼
   ¿Trades IS ≥ 20 & OOS ≥ 15? ──(No)──► [ DESCARTE ]
             │ (Sí)
             ▼
   ¿MaxDD% ≤ Límite Perfil? ──(No)──► [ DESCARTE ]
             │ (Sí)
             ▼
   ¿Folds Positive OOS ≥ 70%? ──(No)──► [ DESCARTE ]
             │ (Sí)
             ▼
   [ ACEPTADO: Candidato Promocionable ]
```

### Tabla Resumen de Gates Duros
1. **Gate 1 (Borde Mínimo)**: $\text{PF}_{\text{IS}} < 1.30 \implies \text{RECHAZO}$.
2. **Gate 2 (Generalización OOS)**: $\text{PF}_{\text{OOS}} < 1.00 \implies \text{RECHAZO IMMEDIATO}$.
3. **Gate 3 (Significancia Estadística)**: $\text{Trades}_{\text{IS}} < 20$ ó $\text{Trades}_{\text{OOS}} < 15 \implies \text{RECHAZO}$.
4. **Gate 4 (Riesgo Intradía/Intrabar)**: $\text{MaxDD}_{\%} > \text{Límite} \implies \text{RECHAZO}$.
5. **Gate 5 (Estancamiento)**: $\text{MaxStagnationDays} > 365 \implies \text{RECHAZO}$.
6. **Gate 6 (Peor Mes)**: $\text{WorstMonthReturn} < -20\% \text{ (Perfil A)} / < -3\% \text{ (Perfil B)} \implies \text{RECHAZO}$.

---

## 5. Matriz de Cross-Checks (Pruebas Anti-Overfit)

Para garantizar que la bala encontrada sea robusta y no un artefacto estadístico, SQX debe aplicar una matriz de pruebas cruzadas dividida entre imprescindibles y opcionales.

### 5.1 Cross-Checks Imprescindibles (Obligatorios en SQX)

1. **Walk-Forward Anclado (6 Folds, Gap de 1 Semana)**:
   * *Configuración*: 6 ventanas en expansión (IS mínimo 2 años), con 3-6 meses OOS por fold y un *gap* de 5 días (1 semana) entre IS y OOS para eliminar sesgo de solapamiento.
   * *Criterio de paso*: $\ge 70\%$ de los folds deben ser positivos en OOS.
2. **Parameter Sensitivity Test (Prueba de Sensibilidad)**:
   * *Configuración*: Perturbación aleatoria de los parámetros numéricos de los indicadores en $\pm 15\%$.
   * *Criterio de paso*: Retención del fitness de al menos $70\%$ (caída máxima de rendimiento $< 30\%$). Si la curva se cae ante pequeñas variaciones, la estrategia es frágil.
3. **Monte Carlo de Reordenamiento de Trades (10,000 Runs)**:
   * *Configuración*: 10,000 permutaciones del orden secuencial de los trades ejecutados.
   * *Criterio de paso*: El percentil 95 de Drawdown ($\text{p95\_DD}$) debe mantenerse dentro del límite permitido del perfil, y el percentil 5 de CAGR ($\text{p5\_CAGR}$) debe ser $> 0$.
4. **Retest en Precisión Superior (M1 Bar Magnifier)**:
   * *Configuración*: Re-evaluación con datos M1 para simular la ejecución intrabar exacta.
   * *Criterio de paso*: Indispensable para medir el Drawdown Diario Real Intrabar en Perfil B (Fondeo).

### 5.2 Cross-Checks Opcionales / Recomendados (Fase Secundaria)

1. **Monte Carlo de Parámetros y Costes (Slippage/Spread $\times 2$)**:
   * Simulación con doble de spread y slippage para evaluar resistencia al deterioro del broker real.
2. **Prueba Cross-Instrumento (Sin Re-optimización)**:
   * Ejecución de las reglas exactas en un activo correlacionado (ej. probar lógica EURUSD en GBPUSD sin cambiar parámetros). Si pierde $> 50\%$ de su fitness, la lógica responde a ruido del activo original.

---

## 6. Flujo Completo de Promoción: SQX Run $\rightarrow$ SQX_CANDIDATE $\rightarrow$ CANONICAL

El ciclo de vida de una estrategia sigue una tubería rigurosa donde la responsabilidad está estrictamente delimitada.

```
+-----------------------------------------------------------------------------------+
| 1. RUN SQX GENERATOR                                                              |
| Pipeline: Sampleo Latino Hipercubo -> Bayesiano TPE -> Walk-Forward 6 Folds       |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
| 2. FILTRADO DURO & INGESTA BD (`ingest_sqx_results.py`)                            |
| - Conversión DD USD -> DD % real sobre Equity                                      |
| - Evaluación de Gates Duros (PF_OOS >= 1.0, Trades >= 20/15, Ret/DD >= 2.0)       |
+-----------------------------------------------------------------------------------+
                                          │
                        ¿Cumple todos los Gates Duros?
                                ├─── NO ───► [ DESCARTE / ARCHIVO ]
                                │
                               ▼ SÍ
+-----------------------------------------------------------------------------------+
| 3. PROMOCIÓN A `SQX_CANDIDATE`                                                    |
| Registro en BD SQLite con metadata completa de IS/OOS y bandera SQX_CANDIDATE.    |
| (Regla: El generador NO es su propio validador)                                   |
+-----------------------------------------------------------------------------------+
                                          │
                                          ▼
+-----------------------------------------------------------------------------------+
| 4. REVALIDACIÓN CON 2º MOTOR INDEPENDIENTE (NautilusTrader)                       |
| - Traducir / exportar código de estrategia SQX a ejecutable Nautilus.             |
| - Ejecutar backtest con motor de eventos de Nautilus sobre datos normalizados.    |
| - Verificar discrepancia de ejecución (< 10% de variación en métricas clave).      |
+-----------------------------------------------------------------------------------+
                                          │
                        ¿Pasa la Revalidación Nautilus?
                                ├─── NO ───► [ RECHAZO / INCOMPATIBLE ]
                                │
                               ▼ SÍ
+-----------------------------------------------------------------------------------+
| 5. PROMOCIÓN A `CANONICAL` & CAPA DE PROTECCIÓN DINÁMICA                          |
| - Marca canónica en BD para despliegue / paper trading / real.                    |
| - Configuración del Ratchet de Equity / Trailing de Equity para gestión de bala.  |
+-----------------------------------------------------------------------------------+
```

---

## 7. Restricciones del Entorno y de Ejecución (Directivas del Usuario)

1. **No Descargar Datos Históricos Adicionales**:
   * Se debe operar 100% con los data feeds ya existentes e importados en la instalación de SQX (`data/normalized/` o almacenamiento interno de SQX). No realizar descargas masivas externas que rompan la coherencia de la base de datos.
2. **Operación en GUI Real de SQX**:
   * Las ejecuciones y configuraciones se realizan sobre la GUI real de StrategyQuant X (accesible en `http://127.0.0.1:5050` o Xvfb `:99`) y/o mediante la API MCP de SQX (puerto `8080`).
3. **Estricta Adherencia a la Doctrina REAL-ONLY**:
   * Queda estrictamente prohibido simular resultados mediante scripts que generen datos falsos de backtest. Toda estrategia registrada en el sistema debe provenir de un XML/archivo de estrategia real procesado por SQX.

---

## 8. Conclusión y Checklist de Auditoría para Planes Futuros

Cualquier plan de trabajo presentado para la optimización o automatización de SQX **debe ser verificado contra el siguiente checklist**:

- [x] ¿El plan exige $\text{PF}_{\text{OOS}} \ge 1.00$ de forma obligatoria?
- [x] ¿Se convierten los Drawdowns de USD absoluto a % sobre Equity real?
- [x] ¿Se imponen mínimos de trades ($\text{IS} \ge 20$, $\text{OOS} \ge 15$)?
- [x] ¿Se incluye el Walk-Forward Anclado con 6 folds y gap de 1 semana?
- [x] ¿Se diferencia claramente la etiqueta `SQX_CANDIDATE` de `CANONICAL` (requiriendo 2º motor NautilusTrader)?
- [x] ¿Se respeta la restricción de trabajar con datos existentes sin descargas adicionales ni simulación de datos falsos?
