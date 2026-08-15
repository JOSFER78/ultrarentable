# Análisis de Riesgos de Sobreajuste (Curve-Fit) y Diseño de la Capa Anti-Overfit

## 1. Diagnóstico y Evidencia de Sobreajuste en la Configuración Actual

### 1.1 Fallas en la Configuración Actual de StrategyQuant X (SQX)
La configuración de generación examinada presenta tres vulnerabilidades críticas que garantizan la producción masiva de estrategias sobreajustadas (curve-fitted):

1. **Función de Fitness orientada a NetProfit Absoluto:**
   - Optimizar exclusivamente por `NetProfit` sin penalizar el Drawdown ni requerir estabilidad o número mínimo de operaciones provoca que el generador seleccione sistemas que arriesgan capital de manera desproporcionada o que explotan unos pocos eventos atípicos (outliers) en la muestra.
2. **Evolución Ciega (`EvoInSamplePeriod = 100`):**
   - Al asignar el 100% de la muestra de datos al proceso evolutivo In-Sample (IS), la búsqueda genética memoriza las particularidades del ruido histórico. No existe ningún segmento de datos no visto durante el proceso de selección de bloques de construcción e hiperparámetros.
3. **Cross-Checks Desactivados (`OFF`):**
   - El pipeline omite las pruebas de estrés durante la generación. Estrategias frágiles que colapsan ante variaciones mínimas de parámetros, slippage, spread o permutación de operaciones pasan el filtro inicial sin ninguna resistencia.

### 1.2 Evidencia Empírica en la Base de Datos (`ultrarentable.sqlite3`)
El análisis de las 95 estrategias y 77 backtests almacenados en la base de datos local revela un patrón claro de sobreajuste:

- **Caso Emblemático: `Strategy 1.1.43`**
  - **$PF_{IS}$ (In-Sample):** $1.56$
  - **$PF_{OOS}$ (Out-of-Sample):** $0.80$
  - **Diagnóstico:** Excelente rendimiento aparente durante la fase de entrenamiento ($PF_{IS} = 1.56$), pero destructora de capital en datos no vistos ($PF_{OOS} = 0.80$). Esto representa una degradación del rendimiento superior al 48%, lo que confirma que el sistema memorizó el ruido del periodo IS.
- **Patrón Sistémico:** Múltiples candidatas aprobadas por el filtro laxo original presentan diferencias abismales entre $PF_{IS}$ y $PF_{OOS}$, demostrando que la ausencia de controles anti-overfit en la generación satura la BD con "falsos positivos".

---

## 2. Capa Anti-Overfit en StrategyQuant X: Filtros y Cross-Checks

Para mitigar el sobreajuste directamente en SQX, se debe configurar una secuencia de gates y cross-checks obligatorios:

```
[ Universo Genérico / Semilla ]
               │
               ▼
   [ IS / OOS Split (70/30) ] ──► Rechaza si PF_OOS < 1.20 o Degradación > 30%
               │
               ▼
 [ Walk-Forward Optimization ] ──► WFE >= 60%, Robusteza OOS >= 70%
               │
               ▼
  [ Simulación Monte Carlo ]  ──► 95% Confianza: PF_MC >= 1.15, MaxDD % <= 25%
               │
               ▼
 [ Permutación de Parámetros ] ──► Plateau Check: 80%+ de variaciones rentables
               │
               ▼
   [ Candidato Aprobado SQX ]
```

### 2.1 Walk-Forward Optimization (WFO) y Walk-Forward Matrix (WFM)
- **Propósito:** Validar que la lógica de la estrategia mantenga capacidad predictiva a lo largo de diferentes regímenes de mercado mediante re-optimización periódica en ventanas móviles.
- **Configuración Recomendada:**
  - **Runs:** 5 a 10 ventanas históricas (ej. 10 runs con 20% OOS por run).
  - **Walk-Forward Efficiency (WFE):** $\ge 60\%$ (calculado como $\frac{\text{Anualizado } PF_{OOS\_WFO}}{\text{Anualizado } PF_{IS\_WFO}}$).
  - **Robusteza OOS:** Al menos el $70\%$ de los periodos de prueba OOS individuales deben cerrar en beneficio.

### 2.2 Pruebas de Monte Carlo (MC)
- **Propósito:** Evaluar la sensibilidad a factores estocásticos y de ejecución (orden de trades, fallos de ejecución, variaciones de spread/slippage).
- **Sub-pruebas y Configuración:**
  1. **Randomize Trades Order (Permutación de Orden):**
     - *Configuración:* 200 a 500 iteraciones.
     - *Objetivo:* Determinar el peor Drawdown histórico posible bajo diferentes secuencias de ganancias/pérdidas.
  2. **Skip Trades (Pérdidas de Ejecución):**
     - *Configuración:* Omisión aleatoria del $5\%$ al $10\%$ de operaciones.
     - *Objetivo:* Asegurar que la rentabilidad no dependa de un par de operaciones extraordinarias ("lucky trades").
  3. **Randomize Spread & Slippage:**
     - *Configuración:* Aumento de spread entre $+20\%$ y $+50\%$; slippage aleatorio de 1 a 3 pips por orden.
- **Criterio de Paso Monte Carlo:**
  - En el **Percentil 95% de Confianza**: $PF_{MC\_95\%} \ge 1.15$ y $\text{MaxDD}_{MC\_95\%} \le 25\%$.

### 2.3 System Parameter Permutation (SPP) / Sensitivity Analysis
- **Propósito:** Verificar que los parámetros de los indicadores residan en una "meseta de estabilidad" (plateau) y no en un pico estrecho (spike).
- **Configuración:** Variación de parámetros de entrada en un rango de $\pm 10\%$ a $\pm 20\%$.
- **Criterio de Paso:** El $80\%+$ de las variaciones permutadas deben mantener $PF \ge 1.10$. Si pequeños cambios degrada bruscamente las métricas, la estrategia se descarta por fragilidad de hiperparámetros.

---

## 3. Integración y Rol del 2º Motor (NautilusTrader) como Validación Independiente

### 3.1 Justificación del Segundo Motor Independiente
Relying solely on SQX (o MetaTrader) introduce un riesgo de sesgo intrínseco del motor (engine-specific bias), derivado de cómo se simulan las ejecuciones de órdenes, el modelado de spreads y la simplificación del libro de órdenes.

NautilusTrader actúa como el **juez independiente de alta fidelidad**:
- **Simulación Event-Driven estricta:** Resolución a nivel de tick/L2 con simulación de latencia real y comisiones estructuradas.
- **Aislante de overfitting sintáctico:** Obliga a traducir la lógica a código ejecutable en Python puro, eliminando artefactos o comportamientos anómalos de las funciones internas de SQX.

### 3.2 Reglas para la Promoción a Estado `CANONICAL`

```
  Estrategia SQX (Filtros Aprobados)
               │
               ▼
  Exportación de Código / Reglas
               │
               ▼
 [ Backtest en NautilusTrader (Tick Data) ]
               │
               ├──► Desviación PF (SQX vs Nautilus) < 15%
               ├──► PF_Nautilus >= 1.15
               ├──► Max DD Relativo < 20%
               └──► Correlación de Equidad > 0.85
               │
               ▼
    [ Promoción a CANONICAL ]
```

Una estrategia solo alcanza el estatus **`CANONICAL`** cuando cumple los siguientes criterios de concordancia cruzada:
1. **Desviación de Profit Factor:** $|PF_{SQX} - PF_{Nautilus}| / PF_{SQX} \le 0.15$ (desviación máxima del 15%).
2. **Rentabilidad Mínima en Nautilus:** $PF_{Nautilus} \ge 1.15$ utilizando datos de tick independientes.
3. **Control de Drawdown:** Drawdown máximo relativo en Nautilus $\le 20\%$.
4. **Correlación de Curva de Equidad:** Correlación de Pearson entre las curvas de equidad acumulada de SQX y Nautilus $\ge 0.85$.

---

## 4. Métricas de Robustez Aceptables y Umbrales Anti-Overfit

Para garantizar la generalización fuera de muestra, se establecen los siguientes umbrales numéricos obligatorios en el pipeline de filtrado:

| Métrica | Umbral Mínimo Requerido | Umbral Objetivo ("Bala Ultrarentable") | Razón / Explicación |
| :--- | :--- | :--- | :--- |
| **$PF_{OOS}$** | $\ge 1.20$ | $\ge 1.40$ | El umbral actual del gate API ($PF_{OOS} \ge 1.0$) es insuficiente y permite breakevens frágiles. |
| **Eficiencia IS/OOS ($\frac{PF_{OOS}}{PF_{IS}}$)** | $\ge 0.70$ | $\ge 0.85$ | Garantiza que la degradación en datos no vistos no supere el 30%. |
| **Trades OOS ($N_{OOS}$)** | $\ge 30$ trades | $\ge 50$ trades | Asegura significancia estadística mínima en el periodo de prueba. |
| **Trades Totales ($N_{Total}$)** | $\ge 100$ trades | $\ge 200$ trades | Elimina sistemas con muestras insuficientes. |
| **Max Drawdown OOS (%)** | $\le 20\%$ | $\le 15\%$ | Convertido obligatoriamente de USD absoluto a porcentaje de capital. |
| **Retorno / Drawdown OOS** | $\ge 2.0$ | $\ge 3.0$ | Evalúa la eficiencia del retorno ajustado por riesgo en OOS. |
| **Monte Carlo $PF_{MC\_95\%}$** | $\ge 1.15$ | $\ge 1.30$ | Garantiza rentabilidad bajo permutaciones al 95% de confianza. |
| **WFE (Walk-Forward Eff.)** | $\ge 60\%$ | $\ge 75\%$ | Verifica consistencia en optimización continua. |

---

## 5. Regla del Pulgar: "Si la lista de candidatos es grande, el gate está mal"

### 5.1 Principio de Escasez del Alfa Real
En el trading cuantitativo, los sistemas que poseen una ventaja estadística genuina (edge) y resistente al mercado son extremadamente raros.
- Si un pipeline de generación o un filtro de base de datos (como el endpoint `GET /rentable` del router actual) devuelve decenas o cientos de candidatos aprobados por cada lote, **no significa que la generación sea excelente, sino que el gate es permeable y está aprobando ruido.**

### 5.2 Calibración Dinámica del Gate
- **Tasa de Aprobación Objetivo (Pass Rate):** $\le 1.0\%$ a $2.0\%$ del universo de estrategias generadas por SQX.
- **Acción Correctora Automática:** Si `/rentable` retorna más de 5 candidatos por cada 1,000 iteraciones de generación, el sistema debe endurecer automáticamente los parámetros del gate (subiendo el requisito de $PF_{OOS}$ a $1.30$ y el ratio de eficiencia a $0.75$).

---

## 6. Plan de Acción para la Implementación en el Pipeline Maestro

1. **Reconfiguración de Archivos `.cfx` / Proyectos de SQX:**
   - Activar división de datos estricta: 70% In-Sample, 30% Out-of-Sample.
   - Cambiar función de fitness a una métrica ponderada ajustada por riesgo (ej. $Ret/DD \times \sqrt{Trades} \times PF_{OOS}$).
   - Integrar bloques de filtrado automático WFO + Monte Carlo antes del almacenamiento de la estrategia.

2. **Actualización del Router API (`sqx_router.py` / `/rentable`):**
   - Modificar las consultas y filtros en el backend para aplicar las métricas de la Sección 4:
     - `PF_IS >= 1.30`
     - `PF_OOS >= 1.20`
     - `Ratio_OOS_IS (PF_OOS / PF_IS) >= 0.70`
     - `Trades_OOS >= 30` y `Trades_Total >= 100`
     - `MaxDD_OOS_Pct <= 20.0`

3. **Pipeline de Promoción Gradual en Base de Datos:**
   - Implementar el ciclo de vida de los estados de estrategia en SQLite:
     $$\text{DRAFT} \longrightarrow \text{SQX\_PASSED} \longrightarrow \text{NAUTILUS\_VERIFIED} \longrightarrow \text{CANONICAL}$$
