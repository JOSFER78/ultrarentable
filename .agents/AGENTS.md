# DIRECTIVA MAESTRA UNIVERSAL PARA AGENTES DE IA

> **REGLA DE DESCUBRIMIENTO AUTOMÁTICO:** Cualquier agente de IA que inicie sesión en este workspace debe acatar esta directiva de forma obligatoria, transparente y continua sin necesidad de recordatorios previos.

---

## 1. GUARDARRAÍLES SUPREMOS E INQUEBRANTABLES

### 1.1 DOCTRINA ZERO-MOCKS & REAL-ONLY (CERO SIMULACIONES FALSAS)
- **PROHIBICIÓN TOTAL DE INVENTAR**: Queda terminantemente prohibido inventar datos, registros, velas, trades, métricas de rendimiento, curvas de equidad, balances, Profit Factor, Sharpe/Sortino o logs de eventos.
- **PROHIBICIÓN DE GENERADORES SINTÉTICOS**: Prohibido el uso de funciones aleatorias o generadoras sintéticas (`random`, `randint`, `uniform`, `seed`) en motores de cálculo, validación, APIs o bases de datos operacionales.
- **CERO FALLBACKS COMPLACIENTES**: Nunca insertar mocks, placeholders o resultados falsos para que una interfaz o reporte "se vea lleno o bonito".
- **GESTIÓN DETERMINISTA DE ESTADOS**:
  - Falta de información o evidencia $\longrightarrow$ `BLOCKED / NO EVIDENCE`.
  - Fallo de un motor o servicio externo $\longrightarrow$ `ENGINE_ERROR / BLOCKED`.
  - Estrategia o cálculo sin datos fuera de muestra $\longrightarrow$ `NO EVIDENCE / REJECTED`.
- **EVIDENCIA FÍSICA OBLIGATORIA**: Toda métrica y veredicto debe ser producto exclusivo de datos reales verificados en disco o respuestas contrastadas de APIs reales.

### 1.2 PRINCIPIO DE PACIENCIA Y CALIDAD FORENSE (NO HAY PRISA)
- **EL USUARIO NO TIENE PRISA**: Prohibido tomar atajos apresurados, soluciones superficiales o intentar resolver problemas complejos en un solo turno descuidado.
- **LOOPS DE REINTENTO Y AUTOCORRECCIÓN ILIMITADOS**: Ante cualquier fallo de test, discrepancia numérica o error de ejecución, itera sistemáticamente:
  $$\text{1. Diagnóstico Forense de Causa Raíz} \longrightarrow \text{2. Corrección de Código} \longrightarrow \text{3. Re-ejecución de Tests Reales} \longrightarrow \text{4. Auditoría de Resultados}$$
- Repite este ciclo cuantas veces sea necesario hasta que la solución sea matemáticamente exacta y empíricamente verificada.
- Es preferible realizar múltiples ciclos de depuración rigurosa y certificar una solución blindada, que entregar código rápido a medias.

### 1.3 PROHIBICIÓN ABSOLUTA DE INVENTAR PÁGINAS, RUTAS O COMPONENTES
- Las rutas del frontend y endpoints del backend deben ceñirse estrictamente a la arquitectura y contratos oficiales del proyecto.
- **PROHIBIDO crear subpáginas temporales, borradores o enlaces rotos** que desvíen o saturen la aplicación.

### 1.4 MANTENIMIENTO Y LIMPIEZA DEL WORKSPACE
- No dejar archivos temporales sueltos en la raíz (`.zip`, `.bat`, `.tmp`, scripts huérfanos).
- Mantener la separación limpia y desacoplada entre capas: contratos inmutables, motores de exploración, motores de validación, servicios y vistas.

### 1.5 SOBERANÍA Y CONTROL TOTAL DE GIT EN MANOS DEL USUARIO
- **PROHIBIDO hacer `git commit` o `git push` de forma automática o desatendida**.
- Todos los cambios de código, directivas y documentación deben permanecer en el *working tree* (sin commitear) para que el usuario pueda inspeccionar los diffs en el panel de **Source Control** y hacer commit/push manualmente cuando lo decida.

---

## 2. ARQUITECTURA DINÁMICA DE EJECUCIÓN (UNIVERSAL PARA CUALQUIER PROYECTO)

- **DETECCIÓN DINÁMICA DEL ENTORNO**:
  - Descubre dinámicamente puertos, procesos, servicios y variables de entorno en lugar de asumir configuraciones estáticas predefinidas.
- **SEPARACIÓN COGNITIVA ESTRICTA**:
  - **Capa Discovery / Exploración**: Abierta a generar, optimizar y explorar hipótesis algorítmicas o soluciones técnicas.
  - **Capa Validación / Juez**: Evaluador independiente, ciego e inmutable. Evalúa las hipótesis desde cero sobre datos reales sin alterar los parámetros.
  - **Capa Certificación**: Emisión de veredictos verificables basados en evidencia matemática.

---

## 3. ESPECIFICACIÓN MAESTRA CANÓNICA: RUTA ULTRA VS RUTA FONDEO

> **Cualquier agente de IA que opere en este workspace debe acatar estas definiciones exactas sin alterarlas ni omitirlas.**

### 3.1 RUTA ULTRA (ASIMETRÍA HIPER-RENTABLE & SUB-CUENTAS BALA)
- **Filosofía**: Convexidad agresiva extrema mediante subcuentas independientes ("balas kamikaze") de **$\$1.000\text{ USD}$**.
- **Sizing de Riesgo**: **$10.0\% - 25.0\%$ de riesgo base por trade** calculado sobre la **equidad disponible**.
- **Apalancamiento Máximo**: **Hasta $500\text{x}$** (Hyper-Leverage extremo en BingX, Perpetuos y Forex).
- **Interés Compuesto**: **Compounding Dinámico Activo y Geométrico**. A medida que la subcuenta crece, el dimensionamiento escala geométricamente.
- **Piramidación**: **Habilitada (1 a 3 tramos agresivos)** reinvirtiendo del $50\%$ al $75\%$ del margen flotante exclusivamente en beneficio $\ge +1.5R$ moviendo el Stop Loss a Break-Even ($0R$).
- **Drawdown Permitido**: **Hasta $80.0\% - 85.0\%$** en la subcuenta bala. La bala solo se considera muerta si alcanza el $85.0\% - 100.0\%$ (liquidación).
- **Cosecha a Bóveda (Ratchet Vault)**: Al alcanzar $+200\%$ de ganancia, el $50\%$ se transfiere automáticamente e irrevocablemente a la Bóveda de Cosecha protegida.
- **Universo de Activos**: **ABSOLUTAMENTE TODOS LOS MERCADOS Y ACTIVOS GLOBALES** (100% Cripto Perpetuos, 100% Forex Majors y Cruces, 100% Futuros CME e Índices, 100% Commodities en todas las temporalidades `1m`, `5m`, `15m`, `1h`, `4h`, `1d`):
  - *Forex Majors & Cruces*: `EURUSD`, `GBPUSD`, `USDJPY`, `AUDUSD`, `USDCAD`, `USDCHF`, `NZDUSD`, `EURJPY`, `GBPJPY`, `EURGBP`, `CADJPY`, etc.
  - *Cripto Perpetuos*: `BTC`, `ETH`, `SOL`, `SUI`, `DOGE`, `AVAX`, `BNB`, `LINK`, `XRP`, `ADA`, `DOT`, `NEAR`, `APT`, `MATIC/POL`, `PEPE`, `SHIB`, `ARB`, `OP`, `TIA`, etc.
  - *Futuros CME & Materias Primas*: `NQ`, `ES`, `YM`, `RTY`, `GC`, `SI`, `CL`, `NG`, `FDAX`, `FTSE`, `NK225`.

### 3.2 RUTA FONDEO (EXÁMENES PROP FIRMS & CUENTAS INSTITUCIONALES)
- **Filosofía**: Superación rápida y sistemática de evaluaciones de Prop Firms (Apex, Topstep, FTMO) en sprint de **$\le 3 - 5$ días hábiles** preservando el Drawdown institucional.
- **Capital Base**: **$\$50.000\text{ USD}$** (Objetivo de pase: $+6.0\% = +\$3.000\text{ USD}$).
- **Sizing de Riesgo**: **$0.7\% - 1.0\%$ por trade** ($\$350 - \$500\text{ USD}$) con **Dynamic Drawdown Cushion Sizing**.
- **Horizonte de Sprint**: Diseñado para alcanzar el Profit Target en $\le 5$ días de trading concentrando 2 a 4 operaciones de alta asimetría ($R \ge 2.5$) por sesión RTH.
- **Interés Compuesto**: **DESHABILITADO**. Lotes fijos / contratos fijos CME (1 o 2 contratos).
- **Piramidación**: **PROHIBIDA**. Exposición lineal estricta.
- **Drawdown Máximo**: **$4.0\%$ estricto** (Límite de Apex/Topstep de $\$2.000\text{ USD}$). Cualquier DD $> 4.0\%$ es motivo de descarte fatal.
- **Límite de Pérdida Diaria**: **$\le 2.0\%$ diario** ($\le \$1.000\text{ USD}$ al día) con auto-flatten al $1.5\%$.
- **Filtro de Sesión**: Operar exclusivamente en horario regular de alta liquidez (**RTH Nueva York: 13:30 a 20:00 UTC**).
- **Universo de Activos**: Solo instrumentos regulados autorizados por firmas de fondeo (`NQ`, `ES`, `YM`, `RTY`, `GC`, `SI`, `CL`, `6E`, `EURUSD`, `GBPUSD`, `USDJPY`).

---

## 4. DOCTRINA DE PUREZA DIMENSIONAL (% Y MÚLTIPLOS R)

- **Capa Cuantitativa y de Juicio (11 Gates, Señales, Optimización)**:
  - **100% en $\%$ y múltiplos $R$**. Prohibido evaluar calidad algorítmica sumando o restando dólares nominales brutos ($\$$).
  - Retorno por trade: $r_t = \frac{\Delta \text{Equity}_t}{\text{Equity}_{t-1}}$.
  - Drawdown: $\text{DD}_t = \frac{\text{Peak}_t - \text{Equity}_t}{\text{Peak}_t} \times 100\%$.
  - Monte Carlo: Remuestreo multiplicativo geométrico $\text{Equity}_t = \text{Equity}_0 \times \prod (1 + r_k)$.
- **Capa de Liquidación Contable**:
  - Los **$\$$ USD** se emplean exclusivamente para balances finales, depósitos iniciales y transferencias a Bóveda.

