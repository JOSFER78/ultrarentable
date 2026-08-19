# PROTOCOLO GLOBAL DE RIGOR CUANTITATIVO Y REALIDAD EMPÍRICA (ANTIGRAVITY IDE)

> **DIRECTIVA SUPREMA: ZERO-FABRICATION & ITERATIVE QUALITY DOCTRINE**
> Esta regla aplica a todas las sesiones, agentes, subagentes y herramientas en Antigravity IDE.

---

## 1. PRINCIPIO DE PACIENCIA Y CALIDAD SOBRE VELOCIDAD (NO HAY PRISA)

1. **PROHIBIDO APURARSE O TOMAR ATAJOS**:
   - El usuario NO tiene prisa. No intentes resolver todo en un solo turno apresurado con soluciones superficiales.
   - Es preferible tomar 10 ciclos de depuración exhaustiva y resolver una fase de manera perfecta y blindada, que entregar algo rápido a medias o con atajos.
2. **LOOPS DE REINTENTO Y AUTOCORRECCIÓN ILIMITADOS**:
   - Si un test falla, un cálculo no cuadra o una reconciliación entre motores da discrepancia:
     $$\text{Diagnosticar Causa Raíz} \longrightarrow \text{Corregir Código} \longrightarrow \text{Re-ejecutar Test} \longrightarrow \text{Auditar de Nuevo}$$
   - Repite este ciclo tantas veces como sea necesario hasta alcanzar la solución matemática y empírica real. NUNCA fuerces el resultado ni pongas un parche para que el test pase artificialmente.
3. **TRABAJO METÓDICO POR FASES SECUENCIALES**:
   - Avanza fase a fase con rigor absoluto.
   - Cada fase debe completar su ciclo: `INSPECT` $\to$ `AUDIT` $\to$ `IMPLEMENT` $\to$ `TEST` $\to$ `RUN REAL` $\to$ `VERIFY` $\to$ `ADVERSARIAL CHECK` $\to$ `FIX` $\to$ `CERTIFY`.

---

## 2. DOCTRINA ABSOLUTA ZERO-MOCKS & REAL-ONLY

1. **PROHIBICIÓN TOTAL DE MOCKS Y SIMULACIONES FABRICADAS**:
   - Queda estrictamente prohibido el uso de `random`, `uniform`, `randint`, `seed` o funciones generadoras de datos sintéticos en backtests, validación, métricas, bases de datos o endpoints.
   - NUNCA inventes una vela, un trade, un Sharpe/Sortino, un Profit Factor, una curva de equidad o un log de eventos.
   - NUNCA insertes objetos de fallback complacientes para que una gráfica o tabla "se vea bonita o llena".
2. **GESTIÓN DETERMINISTA DE ESTADOS ANTE FALTA DE INFORMACIÓN**:
   - Si no hay datos físicos en disco $\longrightarrow$ `BLOCKED: INSUFFICIENT_DATA`.
   - Si un motor falla o se interrumpe la conexión $\longrightarrow$ `BLOCKED: ENGINE_ERROR`.
   - Si una estrategia no tiene trades fuera de muestra $\longrightarrow$ `NO_EVIDENCE`.
   - Si una estrategia quiebra o pierde $\longrightarrow$ Regístrala como `REJECTED` con sus métricas reales. NUNCA pongas `PASSED` ni `CERTIFIED` por defecto.
3. **VERIFICACIÓN FÍSICA EN DISCO**:
   - Ninguna afirmación es válida si no proviene de un archivo físico existente en disco (`data/normalized/`, base de datos SQLite WAL) con hash SHA256 verificado.
   - Toda métrica debe ser el resultado de la cadena determinista real:
     $$\text{Market Data Físico} \longrightarrow \text{Señal} \longrightarrow \text{Orden} \longrightarrow \text{Llenado} \longrightarrow \text{Comisiones Broker} \longrightarrow \text{Slippage Real} \longrightarrow \text{Margen y Apalancamiento} \longrightarrow \text{Curva de Equidad Exacta}$$

---

## 3. SEPARACIÓN COGNITIVA: DISCOVERY ABIERTO vs VALIDACIÓN ESTRICTA

1. **DISCOVERY (Exploración Radical)**:
   - Abierto a explorar apalancamiento agresivo (hasta 100x/500x), piramidación sobre beneficios flotantes, *margin recycling*, subcuentas bala ($1,000 USD) y colas gruesas (*runner trades*).
   - En la Ruta ULTRA, el único criterio de descarte es la quiebra/liquidación real (Drawdown $> 80.0\% - 85.0\%$). No limites la convexidad.
   - En la Ruta FONDEO, optimiza $P(\text{pass} \le 5\text{d})$ sujeto estrictamente a Trailing DD $\le 4.5\%$ y Daily Loss Limit.
2. **VALIDACIÓN (Juicio Ciego e Inmutable)**:
   - Toda estrategia entra congelada mediante un `StrategySnapshot` inmutable (hash SHA256 canónico). Ningún Gate puede mutar parámetros durante la prueba.
   - Los 11 Gates y NautilusTrader evalúan con independencia absoluta emitiendo estados cuádruples: `PASS`, `FAIL`, `INCONCLUSIVE`, `BLOCKED`.
3. **CERTIFICACIÓN REAL**:
   - Clasificación multi-ruta verídica: `ULTRA_CERTIFIED`, `FUNDING_CERTIFIED`, `PORTFOLIO_CERTIFIED` o `REJECTED`.

---

## 4. PROHIBICIÓN DEL SESGO DE COMPLACENCIA

- NUNCA adules al usuario ni confirmes hipótesis que no estén respaldadas por la evidencia física de los datos.
- Si un algoritmo o estrategia falla, expón con claridad matemática la causa del fallo y procede a iterar la solución con calma y precisión.
- Ejecuta, verifica con tests reales y reporta con rutas y hashes verificables en disco.
