# Guía experta: cómo usar StrategyQuant X para buscar estrategias ultrarentables y para fondeo
## Proyecto Ultrarentable · VPS 24/7 · GUI real controlable por computer_use

**Ruta del documento:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md`  
**Entorno:** StrategyQuant X instalado en `/home/ubuntu/StrategyQuantX`, GUI sobre Xvfb `DISPLAY=:99`.  
**Servicio MCP:** `http://127.0.0.1:8080/mcp`  
**Fuentes:** [WEB] docs oficiales `strategyquant.com`, [WEB] guías especializadas (`nononsensetrader`, `smarttradingsoftware`, `quant-bot`, `joelsalgojournal`), [OBS] catálogo interno `06_CATALOGO_TECNICAS_STRATEGYQUANT.md` no accesible por ruta desconocida — se usa su doctrina conocida desde el contexto del proyecto.

---

## Índice
1. Cómo entrar y navegar en la GUI real
2. Variables y casos de uso del X-Builder / evolución genética
3. Paso a paso experto: búsqueda kamikaze de miles de %
4. Paso a paso experto: configuración orientada a fondeo
5. Errores de novato y detección de resultados falsos / overfit
6. Plan de control GUI para `computer_use`
7. Resumen de técnicas recomendadas

---

## 1. Cómo entrar y navegar en la GUI real de StrategyQuant X
### 1.1 Acceso a la GUI en la VPS
- SQX se ejecuta como servicio systemd `strategyquantx.service` en la VPS.
- La GUI usa Xvfb en `DISPLAY=:99`.
- El agente debe usar `computer_use` apuntando a la app `StrategyQuant` o a la ventana X11 del proceso de SQX. Si no se detecta por nombre, usar `DISPLAY=:99` y la ventana del proceso Java de SQX.
- En sesiones remotas, el teclado y ratón virtuales se entregan por `cua-driver`; no hace falta levantar la ventana al front a menos que un diálogo nativo lo requiera.

### 1.2 Módulos principales y layout
SQX se organiza en módulos principales con layout homogéneo. [WEB][DOC: Builder - StrategyQuant]

- **Builder** — núcleo de generación de estrategias.
- **Retester** — motor de retesting y robustness.
- **Optimizer** — optimización de parámetros.
- **Portfolio / Portfolio Master** — análisis de cartera y correlación.
- **AlgoWizard / AlgoLab** — edición visual de estrategias.
- **QuantAnalyzer** — análisis de resultados y estadísticas avanzadas.

Cada módulo comparte estructura de pestañas superiores:
- **Progress**
- **Full Settings**
- **Results**

### 1.3 Layout interno del Builder
[WEB][SMART TRADING SOFTWARE: Builder process guide]

En el módulo Builder se observan habitualmente:

1. **Barra superior de control del proceso**
   - Botones: Start, Pause, Stop.
   - Botones: Load settings, Save settings.
   - Botón: Fitness Evolution para abrir gráficas de evolución.
2. **Panel izquierdo / superior**
   - Data: motor de trading, símbolo, timeframe, rango histórico.
   - Build options: resumen breve de parámetros de generación.
   - Cross checks: toggle rápido para activar/desactivar pruebas de robustez.
   - Results mini-panel: métricas resumidas de la estrategia seleccionada en el databank.
3. **Zona central**
   - Log en vivo con estrategias generadas y su fitness.
   - Charts configurables en la parte inferior: estrategias por tiempo, tasa de rechazo, fitness, etc.
4. **Databank inferior**
   - Lista de estrategias generadas y aceptadas.
   - Ordenable por métricas.
   - Doble clic abre la pestaña **Results** detallada.
   - Botón **Portfolio** para combinar estrategias seleccionadas.

### 1.4 Pestañas del módulo
- **Progress**
  - Log de generación.
  - Gráficos de fitness, memoria, throughput.
  - Resumen de settings con edición rápida inline.
- **Full Settings**
  - Árbol de configuración completa: What to Build, Genetic Options, Data, Trading Options, Building Blocks, ATM, Money Management, Cross Checks, Rankings & Filtering, Notes.
- **Results**
  - Overview, List of trades, Equity chart, Trade analysis, Strategy config, Source code.

### 1.5 Retester
- Igual layout: Progress / Full Settings / Results.
- En **Full Settings** expone:
  - Data
  - Trading Options
  - ATM
  - Money Management
  - Cross Checks (Robustness)
  - Rankings & Filtering
  - Notes

### 1.6 Optimizer / Portfolio Master
- Optimizer: busca combinaciones de parámetros por fuerza bruta o genético para una estrategia.
- Portfolio Master: combina múltiples estrategias y busca asignaciones por fuerza bruta o search genético; útil para reducir correlación y drawdown agregado. [WEB][Quant-Bot / YouTube guide Portfolio Master]

---

## 2. Variables y casos de uso del X-Builder / evolución genética
### 2.1 What to Build
[WEB][SMART TRADING SOFTWARE / Builder guide]

| Variable | Valores típicos | Uso experto |
|---|---|---|
| Strategy type | Simple / Multi-TF-Multi-Symbol / From template / Improve existing | Simple para búsquedas rápidas. Multi-TF/Multi-Symbol para robustez y estrategias avanzadas. Template cuando quieres imponer una lógica concreta. |
| Trading directions | Long only / Short only / Both | Both maximiza el espacio de búsqueda. |
| Trading style | Simple / SQ X / SQ X Fuzzy | SQ X reduce señales ambiguas. Fuzzy para lógica probabilística avanzada. |
| Build mode | Genetic evolution / Random generation | Genetic para calidad. Random para diversificación infinita. |

### 2.2 Número de condiciones, periodos y shifts
- **Min/Max conditions**: rango de condiciones por regla.
  - Fuzzy: mínimo 3, preferible 4+.
  - Simple / SQ X: rango típico 1–3.
- **Global indicator period**: min-max de periodos de indicadores. No uses números excesivamente grandes; perderás relevancia de mercado.
- **Global lookback / Shift**: máximo lookback típico 1–5. No uses 0 porque puede usar la barra en formación y sesgar resultados.

### 2.3 Stop Loss y Profit Target
- SL: None / Fixed pips / ATR based. Define rangos min-max para generación aleatoria.
- TP: None / Same as SL / RRR range.
- Para búsqueda kamikaze puedes permitir rangos amplios; para fondeo, impone límites más realistas.

### 2.4 Genetic Options
[WEB][StrategyQuant official: Genetic options]

| Variable | Recomendación oficial | Uso experto |
|---|---|---|
| Max # of Generations | 5–100 | Más generaciones no siempre ayudan; mejor reiniciar si estancas. |
| Population size | 10–100+ | Poblaciones grandes mejoran refinamiento, pero ralentizan. |
| Crossover probability | Experimentar | Más alto = más intercambio de bloques entre padres. |
| Mutation probability | Experimentar | Más alto = más diversidad, riesgo de perder buenos padres. |
| Islands | 1–10 | 3–5 suele ser un punto dulce. |
| Migrate every Xth generation | ~10 | Evita migrar demasiado; pierdes diversidad insular. |
| Population migration rate | 1–5% | Depende del tamaño de población. |
| Generated decimation coefficient | 1–5+ | Genera X veces más iniciales y elige los mejores. Mejora calidad inicial, pero ralentiza mucho el arranque. |
| Initial population from databank | On/Off | Usa databank con buenas semillas para mejorar sobre ideas previas. |
| Filter generated initial population | Loose | Solo filtra “sin trades” inicialmente; deja que la genética mejore. |
| Detect same strategies / replace | On/Off | Ayuda a diversificar. |
| Replace X % weakest with fresh blood | Configurable | Renueva población si se estanca. |
| Show last generation databank | On/Off | Solo para isla 1; útil para depurar evolución. |
| Start again when finished | On/Off | Modo autónomo nocturno. |
| Restart if fitness stagnates | On/Off | Reinicia cuando la población no mejora. |

### 2.5 Data
- **Trading engine**: selecciona la plataforma objetivo, por ejemplo MT4/MT5 si el objetivo es部署 EA.
- **Backtest data settings**:
  - Símbolo, timeframe, periodo histórico.
  - Multi-TF / Multi-Symbol: define charts adicionales.
- **Test parameters / Precision**:
  - Selected timeframe only: rápido, 4 ticks por barra.
  - 1 Minute data: más preciso.
  - Real tick – custom spread: para spread controlado.
  - Real tick – real spread: más lento, solo para verificación final.
- **Comisión, Spread, Slippage, Min distance**.
- **Data range parts**:
  - IST: entrenamiento genético.
  - ISV: validación in-sample para reinicios.
  - OOS: fuera de muestra, evaluación realista.
  - No Trade: periodos sin operar.

### 2.6 Building Blocks
[WEB][StrategyQuant official: Building blocks]

Bloques principales:

#### Señales / Signals
- Condiciones predefinidas completas: ej. “ADX rising”, “CCI crossed above 0”.
- Puedes asignar peso para favorecer unas señales sobre otras.

#### Indicadores / Indicators
- Indicadores técnicos, rangos de precio, etc.
- Parámetros editables por bloque: Chart, Computed From, Period, Shift.
- Parameter sets: crea conjuntos fijos de parámetros en competencia con generación aleatoria.
- Indicator values: define rangos esperados para comparaciones numéricas.
- Indicator calibration: autocalibración o manual por mercado.

#### Stop/Limit entry blocks
- Bloques para definir niveles de entrada en órdenes pendientes.

#### Order types
- Market, Stop, Limit, Enter/Reverse.
- Define pesos y parámetros.

#### Exit types
- Reglas de salida: Profit Target, Trailing Stop, ExitRule, señal de salida, etc.

#### Custom data indicators
- Indicadores externos importados por timeframe.

#### Advanced: edición de parámetros
- Puedes fijar periodos, shifts, límites de generación.
- Parameter sets compiten con generación aleatoria según peso.

### 2.7 ATM
- Advanced Trade Management: múltiples salidas parciales.
- Desactiva Profit Target/Trailing Stop si lo usas.
- Cierres parciales según beneficio relativo al riesgo, porcentaje fijo o por barras.

### 2.8 Money Management
- Fixed size
- Fixed % of balance
- Fixed % of account
- Fixed amount
- Crypto size by price
- Stock size by price
- Simple Martingale MM

Para búsqueda de estrategias no uses MM agresiva en generación; guarda Martingale para pruebas específicas.

### 2.9 Cross Checks en Builder
- Úsalos de forma ligera en Builder.
- Tests pesados van en Retester.
- Objetivo: formar un “funnel” de aceptación rápido.

### 2.10 Rankings & Filtering
- **Max strategies in databank**: límite de guardado.
- **Fitness data source**: OOS, IS, portfolio completo, etc.
- **Ranking criteria**:
  - Default computations.
  - Custom rules.
- **Filters**:
  - Automatic filters: PF mínimo, trades mínimos, drawdown máximo, WR/DD, trades por mes, etc.
  - Custom filters: condiciones propias.

### 2.11 Strategy Templates
[WEB][StrategyQuant official: Strategy templates]

- Usa `RandomCondition` para que SQ genere condiciones automáticamente.
- Usa `NegatedCondition` para crear automáticamente la versión corta de una regla larga.
- Plantillas recomendadas para “miles de %”:
  - Breakouts con filtros de tiempo.
  - Pullbacks en tendencia.
  - Reversiones con ATR.
- Puedes partir de plantillas de comunidad y modificarlas.

---

## 3. Paso a paso experto: búsqueda kamikaze de miles de %
> Objetivo: maximizar retorno neto sin importar drawdown intermedio, con alta generación de ideas y filtrado posterior en Retester.

### Paso 1 — Selección de datos
1. Abre **Builder** → **Data**.
2. Elige símbolo y timeframe volátil y con spread bajo para “kamikaze”:
   - NAS100, US30, XAUUSD, pares exóticos o cripto CFD.
   - Timeframe intermedio: M15, M30, H1.
3. Si usas Multi-TF/Multi-Symbol, añade H4/D1 como contexto.
4. Carga datos tick/1min si está disponible.

### Paso 2 — Plantillas y bloques de señal
1. Ve a **What to Build** → elige **Strategy from template** si quieres imponer una lisis inicial.
2. Si prefieren búsqueda libre, elige **Simple strategy** o **SQ X style**.
3. Ve a **Building Blocks**:
   - Habilita **Signals**, **Indicators**, **Stop/Limit entry blocks**.
   - Para kamikaze puedes habilitar más bloques de volumen, volatilidad y patrones.
   - Asigna pesos altos a señales de momentum, breakout y filtros de tiempo.

### Paso 3 — Configuración de evolución agresiva
1. Abre **Genetic Options**:
   - Generations: 30–80.
   - Population size: 50–100 por isla.
   - Islands: 3–5.
   - Migrate every: 10 generaciones.
   - Migration rate: 2–5%.
   - Crossover: 0.6–0.8.
   - Mutation: 0.05–0.15.
   - Decimation coefficient: 2–4.
   - Fresh blood: activo.
   - Replace weakest: 10–20%.
   - Start again when finished: ON para overnight.
2. En **Data range parts**:
   - IST amplio.
   - ISV mediano.
   - OOS reducido o nulo si buscas puro backtest histórico extremo.
   - Nota: para “miles de %” es común usar IST muy largo y OOS corto; pero eso genera overfit. Luego filtrarás en Retester.

### Paso 4 — Stop Loss, TP, ATM y MM
1. SL: ATR-based con rango amplio.
2. TP: None o RRR amplio.
3. ATM: opcional, para splits parciales agresivos.
4. MM: Fixed size para no contaminar el ranking.

### Paso 5 — Cross Checks mínimos en Builder
- Activa solo **Basic** para no frenar la generación.
- Guarda pruebas pesadas para Retester.

### Paso 6 — Rankings y filtros iniciales
1. Ve a **Rankings & Filtering**.
2. Ranking personalizado:
   - Prioriza `Net profit`, `Profit factor`, `Win rate / DD`, `Return/Drawdown`.
3. Filtros automáticos recomendados para kamikaze:
   - Profit Factor > 1.2
   - Trades mínimos: 50–100
   - Max Drawdown %: relajado
   - Return %: muy alto
4. Máximo de estrategias en databank: 500–2000.

### Paso 7 — Lanzar y observar
1. En **Progress** pulsa **Start**.
2. Monitorea:
   - Fitness Evolution.
   - Log.
   - Tasa de rechazo.
3. Deja correr en modo autónomo overnight si activaste “Start again when finished”.

### Paso 8 — Revisión preliminar
1. Ve a **Results**.
2. Ordena por retorno y examina equity curves.
3. Selecciona candidatos prometedores y transfiérelos a **Retester**.

---

## 4. Paso a paso experto: configuración orientada a fondeo
> Objetivo: consistencia, drawdown controlado, generalización y bajo overfit.

### Paso 1 — Datos representativos
1. Elige mercados estables y representativos del reto:
   - Forex majors o índices líquidos: EURUSD, GBPUSD, NAS100, SPX500.
   - Usa H1 o H4 para reducir ruido.
2. Rango histórico amplio e IST/ISV/OOS claros.

### Paso 2 — Plantillas conservadoras
1. Usa plantillas probadas:
   - Trend following multi-TF.
   - Mean reversion con filtros de sesión.
2. Limita bloques exóticos en **Building Blocks**:
   - Mantén precio, operadores básicos, indicadores robustos.
   - Evita cientos de patrones raros.

### Paso 3 — Evolución moderada
1. **Genetic Options**:
   - Generations: 10–40.
   - Population size: 30–60.
   - Islands: 2–3.
   - Decimation: 2–3.
   - Mutation: 0.05–0.1.
   - Crossover: 0.5–0.7.
   - Fresh blood: moderado.
2. **Data range parts**:
   - IST / ISV / OOS bien diferenciados.
   - OOS ≥ 20–30% para evaluar generalización.

### Paso 4 — SL, TP, ATM, MM
1. SL fijo o ATR moderado.
2. TP realista.
3. ATM para control parcial de riesgo.
4. MM: Fixed size o Fixed amount para comparabilidad.

### Paso 5 — Filtros conservadores desde el inicio
1. **Rankings & Filtering**:
   - Profit Factor ≥ 1.4–1.7.
   - WR/DD ≥ 4–6.
   - Trades/mes ≥ 2–5.
   - Max Drawdown ≤ 15–25%.
   - Return % moderado, no obsesivo.
2. Máximo en databank: 200–500 estrategias.

### Paso 6 — Retester obligatorio
1. Transfiere estrategias a **Retester**.
2. Ejecuta funnel creciente:
   - Higher backtest precision.
   - What if simulations.
   - Monte Carlo manipulation.
   - Additional markets.
   - Monte Carlo retest methods.
   - Walk-Forward Optimization.
   - Walk-Forward Matrix.
3. Filtros finales:
   - WFE > 0.6, ideal > 0.8.
   - PF multi-mercado > 1.4.
   - Monte Carlo: drawdown estable.
4. Guarda solo estrategias con alto grado de robustez.

---

## 5. Errores de novato y detección de resultados falsos / overfit
### 5.1 Errores comunes
- Usar demasiados bloques y generar sobre-exploración ineficiente.
- Población muy pequeña o muy grande sin criterio.
- OOS nulo o insignificante.
- Filtros laxos en Builder y sin Retester posterior.
- Evaluar por beneficio absoluto en lugar de ratios.
- Ignorar costes reales: comisión, spread, slippage.
- No validar en mercados relacionados ni timeframes adyacentes. [WEB][Nononsensetrader]
- Permitir estrategias con pocos trades pero retorno altísimo.

### 5.2 Señales de overfit en la GUI
- Retorno altísimo con drawdown casi nulo en un solo mercado/timeframe.
- Curva de equity casi perfecta sin retrocesos.
- Muchos picos en Profit Factor pero trades < 100.
- Sensibilidad extrema a shift o parámetros pequeños.
- Resultados que colapsan al cambiar spread o slippage en 1–3 pips.
- Falla inmediata en Retester al cambiar mercado o timeframe. [WEB][SMART TRADING SOFTWARE: Retester guide]

### 5.3 Funnel de sanity checks recomendado
1. Builder → filtros iniciales moderados.
2. Retester → precision 1min o real tick.
3. Retester → What if con spread/slippage elevados.
4. Retester → Multi-market y multi-TF.
5. Retester → Monte Carlo manipulation.
6. Retester → Monte Carlo randomized params/spread/history.
7. Retester → Walk-Forward Optimization.
8. Retester → Walk-Forward Matrix.
9. Portfolio Master → correlación y drawdown agregado.

---

## 6. Plan de control GUI para `computer_use`
> Objetivo: secuencia operativa fiable para que un agente ejecute una búsqueda kamikaze real en la GUI de la VPS sin tocar código.

### 6.1 Precondiciones
- Servicio `strategyquantx` levantado.
- Sesión Xvfb `:99` activa.
- Datos históricos cargados en Data Manager.
- Ruta conocida: `/home/ubuntu/StrategyQuantX`.

### 6.2 Secuencia genérica de navegación en SQX
1. **Enfocar la app** `StrategyQuant`.
2. Si aparece diálogo de licencia/actualización, cerrarlo.
3. Localizar el módulo **Builder** en la barra lateral o menú principal.
4. Pulsar **Builder**.
5. En Builder:
   - Pulsar **Full Settings**.
   - Configurar **What to Build**.
   - Configurar **Genetic Options**.
   - Configurar **Data**.
   - Configurar **Building Blocks**.
   - Configurar **Rankings & Filtering**.
6. Volver a **Progress**.
7. Pulsar **Start**.
8. Esperar/observar logs.
9. Pulsar **Pause/Stop** si es necesario.
10. Abrir **Databank**, seleccionar estrategias.
11. Pulsar **Portfolio** si se requiere combinación.
12. Abrir **Retester**, transferir estrategias.
13. Configurar **Full Settings** en Retester.
14. Pulsar **Start** en Retester.
15. Revisar **Results** y exportar código si aplica.

### 6.3 Secuencia concreta para búsqueda kamikaze
Pasos numerados para ejecución real por `computer_use`:

1. `computer_use` → captura modo `som` de la ventana `StrategyQuant`.
2. Si no está en Builder, clic en **Builder** del menú lateral / módulos.
3. Clic en pestaña **Full Settings**.
4. En **What to Build**:
   - Elegir **Simple strategy** o **SQ X style**.
   - Direcciones: **Both**.
   - Estilo: **SQ X**.
   - Build mode: **Genetic evolution**.
5. En **# Of Conditions, Periods**:
   - Min conditions = 1, max = 3.
   - Global indicator period = rango moderado.
   - Shift = 1–5.
6. En **Genetic Options**:
   - Generations = 40–80.
   - Population size = 60–100.
   - Islands = 3–5.
   - Migration = cada 10 generaciones, 2–5%.
   - Crossover = 0.7.
   - Mutation = 0.1.
   - Decimation = 3.
   - Fresh blood activo, replace weakest 15%.
   - Start again when finished activo para overnight.
7. En **Data**:
   - Símbolo elegido, por ejemplo NAS100.
   - Timeframe M30 o H1.
   - Periodo histórico amplio.
   - Precision inicial: Selected timeframe.
8. En **Building Blocks**:
   - Habilitar price data, señales comunes, indicadores de momentum y volatilidad.
   - Aplicar calibración de indicadores si se solicita.
9. En **Trading Options**:
   - SL ATR con rango amplio.
   - TP opcional o None.
   - Exit Friday ON.
   - Realistic gaps handling ON.
10. En **ATM**: opcional.
11. En **Money Management**: **Fixed size**.
12. En **Cross Checks**: solo básicos.
13. En **Rankings & Filtering**:
    - Ranking: OOS o total.
    - Filtros relajados: PF > 1.2, trades > 80.
    - Max strategies = 1000.
14. Clic en **Progress**.
15. Clic en **Start**.
16. Monitorear hasta finalización.
17. Abrir **Databank**, ordenar por retorno, seleccionar top candidatos.
18. Abrir **Retester**, mover selección.
19. En Retester ejecutar:
    - Higher precision.
    - Monte Carlo manipulation.
    - Additional markets.
    - Monte Carlo retest methods.
    - Walk-Forward Optimization.
    - Walk-Forward Matrix.
20. Revisar **Results** en Retester y exportar solo estrategias passed.

### 6.4 Recomendaciones operativas para `computer_use`
- Usa capturas `mode='som'` para identificar botones por índice y no por coordenadas frágiles.
- Antes de escribir en campos numéricos, haz `capture` y valida el foco.
- Para selects/listas usa `set_value` cuando esté soportado.
- Si un diálogo nativo bloquea, cambia a `foreground` solo para ese paso puntual.
- Guarda settings tras cada configuración relevante.
- Si el proceso es largo, ejecútalo en segundo plano y vuelve a capturar periódicamente para verificar avance.

---

## 7. Resumen de técnicas recomendadas
[OBS] Esta sección resume la doctrina del catálogo `06_CATALOGO_TECNICAS_STRATEGYQUANT.md` referenciado por el proyecto.

### Para “miles de %” controladas
- X-Builder con Genetic evolution agresiva: islas, decimation, fresh blood y reinicio automático.
- Plantillas sesgadas hacia breakout/momentum.
- Filtros relajados en Builder, filtrado duro en Retester.
- Validación obligatoria en Retester:
  - Multi-market / multi-TF.
  - Slippage elevada.
  - Monte Carlo manipulación de trades.
  - Walk-Forward Matrix.

### Para fondeo
- Builder conservador: pocas islas, población moderada, OOS generoso.
- Plantillas robustas y conocidas.
- Ranking por ratios estables:
  - PF > 1.4–1.7
  - WR/DD > 4–6
  - Trades/mes ≥ 2
- Portfolio Master para combinar estrategias no correlacionadas.
- Walk-Forward Efficiency > 0.6.
- Walk-Forward Matrix como último filtro.

### Regla final
> Encuentra muchas ideas en Builder, pero gana el dinero en Retester. Si una estrategia no pasa el funnel de robustness, no existe.
