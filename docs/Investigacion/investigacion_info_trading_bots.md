# Informe consolidado: Investigación de info_trading_bots
**Ruta fuente:** `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/info_trading_bots/`
**Fecha:** 8 de agosto de 2026
**Objetivo:** consolidar hallazgos de investigaciones previas sobre bots de trading, prop firms, DaviddTech, ejecución, compliance y filtros anti-overfitting, con foco en un MVP real.

---

## 1) Prop firms investigadas y reglas exactas

> **Nota:** Las políticas cambian. Estas reglas se extraen de los documentos disponibles en la carpeta `info_trading_bots/` y deben verificarse contra los términos oficiales antes de conectar cualquier bot.

### 1.1 Resumen de firmas encontradas

| Prop firm | Evidencia de automatización | Payouts documentados | Fuente en este repo |
|---|---|--:|--|
| **Lucid** | Sí | Múltiples (~8.900 USD acumulados) | `informe_master_trading_bots.md` (caso u/Enough_Run_3856) |
| **Topstep** | Sí | Menor continuidad pública | `informe_master_trading_bots.md` (caso Thraxx) |
| **Tradeify** | Infraestructura demostrada | No atribuible a bot | `informe_master_trading_bots.md` |
| **Bulenox** | Infraestructura demostrada | No atribuible a bot | `informe_master_trading_bots.md` |
| **MyFundedFutures** | Infraestructura + payouts de la firma | No atribuible a bot | `informe_master_trading_bots.md` |
| **FundedNext Futures** | Infraestructura + certificados de payout | No atribuible a bot | `informe_master_trading_bots.md` |
| **Take Profit Trader** | Demostración de automatización | Testimonio negativo de ban/pérdida de payouts | `informe_master_trading_bots.md` |
| **Earn2Trade / Alpha Futures / TradeDay** | Candidatas por API/webhooks | Pendiente de verificación primaria | `informe_master_trading_bots.md` |

### 1.2 Dimensiones de reglas que deben modelarse

Aunque en los archivos presentes no se transcriben textualmente los términos oficiales de cada firma, la investigación agrupa las reglas en bloques operativos:

- **Profit target** de evaluación y de cuenta funded.
- **Drawdown máximo** y **trailing drawdown / high water mark**.
- **Límites diarios** de pérdida.
- **Reglas de consistencia** (si aplican): proporción de ganancia por sesión o restricciones de concentración.
- **Política de bots/automatización**: si exigen declaración, permiten webhooks, prohíben cierta automatización o exigen VPS/IP fija.
- **Restricciones de horario, noticias, sesiones, overnight y flat before close**.
- **Límites de tamaño**: contratos máximos, riesgo por operación, exposición por instrumento.
- **Cuenta gratuita / prueba**: se menciona como dato relevante cuando existe, pero no se detalla en los archivos leídos.

**Conclusión operativa:** para un MVP real, no se debe conectar un bot hasta tener una tabla por prop firm con `profit_target`, `daily_loss_limit`, `trailing_drawdown`, `consistencia`, `noticias`, `overnight`, `max_contracts` y `allowed_automation_mode` extraídos de sus términos oficiales.

---

## 2) Metodología DaviddTech

Fuente principal: `01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md`.

### 2.1 Enfoque general
DaviddTech propone una evolución:
`indicadores → estrategias → bots → IA para desarrollar estrategias → Strategy Factory → portfolios de micro-bots → agentes → ejecución`.

El LLM no debe usarse como predictor directo del precio, sino como:
- investigador,
- programador,
- generador de hipótesis,
- orquestador de backtesting,
- documentador y monitor.

### 2.2 Pipeline de 5–6 etapas

1. **In-Sample (IS)** — desarrollar la hipótesis. No es prueba final.
2. **Out-of-Sample (OOS)** — evaluación en datos temporales separados del desarrollo.
3. **Walk-Forward Analysis (WFA)** — reoptimizar en ventanas móviles y evaluar en ventanas siguientes.
4. **Forward / Incubación** — ejecutar con reglas congeladas y datos nuevos.
5. **Paper / Testnet** — validar señales, latencia, fills, slippage, reconexión y duplicación.
6. **Live pequeño** — solo después de superar las etapas anteriores.

### 2.3 NNFX / Strategy Boilerplate
DaviddTech usa frameworks estructurados como referencia:
1. mercado,
2. régimen,
3. señal primaria,
4. confirmación,
5. filtro,
6. entrada,
7. stop,
8. salida,
9. position sizing,
10. límites de riesgo.

Principio: la IA explora dentro de reglas bien definidas, no inventa libremente el sistema que supuestamente “más gana”.

### 2.4 Régimen y filtros
- No todas las estrategias deben operar en todas las condiciones.
- Ejemplos: tendencia, rango, alta/baja volatilidad, mercado caótico, persistencia.
- Herramientas citadas: Choppiness Index, TDFI, Lyapunov, ATR.
- Uso recomendado: como **filtro**, no como señal primaria.

### 2.5 Position sizing adaptativo
```text
PositionSize ≈ RiskBudget / (ATR × Multiplicador × ValorMonetarioPorTick)
```
Objetivo: controlar el riesgo monetario, no maximizar ganancia por trade.

---

## 3) Prop-Firm Constraint Engine

Fuente principal: `informe_master_trading_bots.md`.

### 3.1 Arquitectura recomendada
La señal nunca debe enviar una orden directamente. Debe pasar por:

```text
Estrategia → Señal → Prop-Firm Constraint Engine → Risk Engine → Execution → Broker/Prop → State Reconciliation
```

### 3.2 Reglas de veto que debe implementar

| Veto | Detalle de implementación |
|---|---|
| **Daily loss limit** | No permitir exposición nueva si el P&L del día puede superar el límite oficial. |
| **Trailing drawdown / HWM** | Mantener máximo interno permitido y actualizarlo según reglas de la prop firm. |
| **Position size** | Aplicar contratos máximos, riesgo por operación y riesgo total. |
| **Session rules** | Bloquear entradas fuera de horario permitido, gestionar flat before close y overnight. |
| **News rules** | Bloquear/modificar operación en ventanas de noticias si la firma lo exige. |
| **Consistency** | Calcular y hacer cumplir reglas de consistencia cuando existan, sin ambigüedad. |
| **Kill switch** | STOP NEW ENTRIES → MANAGE / FLATTEN IF REQUIRED → LOCK TRADING. |

### 3.3 Máquina de estados obligatoria

```text
FLAT → ENTRY_PENDING → PARTIALLY_FILLED → OPEN → EXIT_PENDING → FLAT
```

Después de cada reconexión: **estado local vs. estado broker/prop**, para detectar:
- órdenes huérfanas,
- posiciones duplicadas,
- fills no registrados,
- stops inexistentes.

### 3.4 OCO server-side
Cuando la API lo permita, preferir brackets OCO gestionados por servidor:
- entry + stop + target;
- uno ejecutado → cancelar el otro.

Reduce dependencia del cliente, pero debe verificarse comportamiento exacto por broker/API.

---

## 4) Anti-baneo / Compliance

Fuente principal: `informe_master_trading_bots.md`.

### 4.1 Postura doctrinaria
> **Compliance-first, no anti-detection.**

Si la firma exige declarar el bot, se declara. Si prohíbe una modalidad, no se disfraza. Si permite bots bajo condiciones, el sistema se diseña para cumplirlas de forma verificable.

### 4.2 Técnicas investigadas y su uso aceptable

| Técnica | Uso aceptable | Uso NO aceptable |
|---|---|---|
| **Jitter** | Mitigar fingerprinting de red/IP legítimamente | Ocultar automatización prohibida |
| **Permanencia mínima** | Cumplir reglas de evaluación/funded | Simular comportamiento humano artificialmente |
| **Modificación deliberada de timing** | Ajuste operativo normal | Evitar sistemas de detección |
| **Cambios de parámetros** | Gestión de régimen/robustez | Eludir monitoreo |

### 4.3 Regulación mencionada
- **CME Rule 575** se menciona en la investigación paralela como referencia normativa relevante en el ecosistema de futuros; en los archivos actuales se advierte que cualquier práctica debe alinearse con compliance-first y no con técnicas anti-detección.

### 4.4 Riesgos operativos que sí deben evitarse
- HFT / latency arbitrage.
- Order spam.
- Quote stuffing.
- Scalping extremadamente corto si la firma lo restringe.
- Copy trading no permitido.

---

## 5) Middleware de ejecución

Fuente principal: `informe_master_trading_bots.md` y `01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md`.

### 5.1 Rutas típicas estudiadas

```text
TradingView → Webhook → Middleware → Broker/API → Prop Firm
```

### 5.2 Herramientas

| Herramienta | Rol observado | Observación |
|---|---|---|
| **TradersPost** | Middleware webhook → broker/prop | Compatible con varias props investigadas |
| **PickMyTrade** | Middleware para Bulenox/MyFundedFutures | Infraestructura demostrada |
| **Rithmic** | Conexión de datos/ejecución | Usado en arquitecturas investigadas |
| **Tradovate API** | Broker/API | Ruta alternativa para ejecución |
| **TradingView webhooks** | Origen de señal | Punto de entrada más común |

### 5.3 Consideraciones de latencia
- Un webhook perdido, WebSocket desconectado o token expirado pueden convertir una señal correcta en una operación incorrecta.
- Por eso se requiere un **State Manager** y reconciliación continua.
- Cuando la API lo permita, los OCO server-side reducen dependencia del cliente.

---

## 6) Filtros anti-overfitting

Fuente principal: `01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md`.

### 6.1 Enemigos principales

| Riesgo | Descripción |
|---|---|
| **Data-mining bias** | Selección retrospectiva de la estrategia que mejor funcionó. |
| **Look-ahead bias** | Uso de información no disponible en el momento de la decisión. |
| **Repainting** | La señal histórica cambia después de generarse. |
| **Sample-size bias** | Pocas operaciones con resultado extraordinario sin suficiente evidencia. |
| **Costes irreales** | Ausencia de comisión, spread, slippage, latencia y fills parciales. |

### 6.2 Filtros estadísticos recomendados

1. Número mínimo de operaciones.
2. Costes y slippage realistas.
3. Separación IS / OOS / Holdout.
4. Walk-Forward Analysis.
5. Monte Carlo / resampling.
6. Análisis de sensibilidad.
7. Estabilidad de parámetros / plateau test.
8. Evitar dependencia de un único periodo.
9. Analizar distribución de resultados, no solo beneficio total.
10. Penalizar complejidad.

### 6.3 DSR, WFE y Monte Carlo

- **DSR / defensa estadística:** el documento no provee una fórmula numérica concreta en los archivos leídos; sin embargo, la investigación enfatiza tests de significancia y estabilidad antes de considerar cualquier estrategia.
- **WFE / Walk-Forward Efficiency:** el WFA es el método principal defendido para comprobar si la estrategia mantiene propiedades fuera de muestra.
- **Monte Carlo:** sirve para estimar drawdown probable, rachas de pérdidas, sensibilidad a la secuencia y percentiles de resultados.

### 6.4 Plateau test
No basta con que la estrategia funcione en un parámetro óptimo aislado; debe mantenerse estable en una zona de parámetros.

---

## 7) Recomendaciones accionables para un MVP real

Fuente principal: `informe_master_trading_bots.md` y `01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md`.

### 7.1 MVP de arquitectura, no de “bot mágico”
Construir un **sistema de control** con estas capas obligatorias:

1. **Research** → generación de hipótesis.
2. **Quant** → codificación de reglas.
3. **Validation** → IS/OOS/WFA/Monte Carlo.
4. **Regime** → filtro de condiciones de mercado.
5. **Portfolio** → combinación de estrategias de baja correlación.
6. **Prop Constraint Engine** → reglas de la cuenta.
7. **Risk Engine** → tamaño, stops, límites y kill switch.
8. **Execution Engine** → envío de órdenes con reconciliación.
9. **State Reconciliation** → detección de órdenes huérfanas, fills duplicados y stops ausentes.
10. **Monitoring** → alertas y apagado automático.

### 7.2 Ejecución
- Usar middleware probado para la prop elegida.
- Preferir OCO server-side cuando la API lo soporte.
- Implementar reconciliación post-reconexión obligatoria.
- Diseñar timeouts y protección contra tokens expirados.

### 7.3 Compliance
- Documentar la política de bots de la prop firm elegida.
- No implementar técnicas anti-detección.
- Preparar declaración de automatización si la firma lo requiere.
- Asegurar trazabilidad de IP/VPS si la firma lo pide.

### 7.4 Validación
- Nunca pasar de paper a live sin WFA y forward.
- Aplicar Monte Carlo para estimar drawdown y rachas.
- Descartar estrategias con costes irreales o sesgo de look-ahead.

### 7.5 Riesgos no negociables
- No confundir backtest espectacular con resultado live.
- No escalar sin evidencia de payout continuado y consistente.
- No operar sin kill switch y estado FLAT seguro tras fallos.

---

## 8) Evidencia pública prioritaria encontrada

| Caso | Prop firm | Evidencia | Valoración |
|---|---|---|---|
| u/Enough_Run_3856 | Lucid | múltiples payouts + arquitectura TradingView/TradersPost | 9/10 |
| Thraxx | Topstep | bot + evaluación + seguimiento | 7/10 |
| 12 eval / 5 funded / 1 payout | No especificada | testimonio + resultados | 6/10 |
| TPT bot | Take Profit Trader | demostración técnica de automatización | 4/10 |

Estos casos muestran que la evidencia pública fuerte es escasa. El mejor caso no garantiza que la estrategia siga funcionando ni que el payout sea aceptado incondicionalmente.

---

## 9) Archivos fuente utilizados

- `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/info_trading_bots/informe_master_trading_bots.md`
- `/home/ubuntu/workspace/pro/trading/01 Ultrarentable/info_trading_bots/01_TRADING_BOTS_INVESTIGACION_CONSOLIDADA.md`

> Aunque la tarea menciona 17 archivos incluyendo `informe_subagente_01..10` y otros `.md`/`.html`, en el directorio actual solo se detectaron los 2 archivos anteriores. Este informe se elaboró con esa evidencia disponible y advierte que cualquier regla de prop firm debe validarse contra términos oficiales.

---

## 10) Próximos pasos recomendados

1. Verificar manualmente los términos oficiales de la prop firm objetivo y completar la tabla de reglas exactas.
2. Elegir una sola firma para MVP y modelar su Constraint Engine formalmente.
3. Definir un dataset aprobado y su manifiesto/checksum antes de cualquier backtest.
4. Ejecutar WFA y Monte Carlo sobre una cartera inicial de micro-estrategias.
5. Implementar middleware + reconciliación en paper antes de cualquier live pequeño.
