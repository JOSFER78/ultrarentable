# I4 — Prop firms de futuros CME, 2026: re-verificación desde fuente primaria

**Subagente:** AG-10 · **Fecha de captura de todos los datos:** 2026-09-01 · **Idioma:** ES

## 0. Nota de método (léase antes que las tablas)

1. **Orden de trabajo respetado:** toda la investigación web de este documento se hizo ANTES de abrir `docs/Fondeo/BASE_DATOS_EMPRESAS_FONDEO_FUTUROS_2026-08-02.md` y `docs/conexiones_automatizar/`. Esos ficheros se leyeron solo al final, para la sección 6 (discrepancias). No se ha copiado ningún valor del corpus a las tablas 1-5.
2. **Bloqueo técnico real y honesto:** los dominios `apextraderfunding.com`, `support.apextraderfunding.com`, `help.tradeify.co`, `bulenox.com` y `takeprofittraderhelp.zendesk.com` devuelven **403 Forbidden** (Cloudflare/JS-challenge) al `WebFetch` directo de este entorno, de forma sistemática, en las dos vías probadas (fetch directo y proxy `r.jina.ai`, que solo funcionó parcialmente para Apex). `help.topstep.com`, `myfundedfutures.com`, `help.myfundedfutures.com` y `tradeday.freshdesk.com` **sí** respondieron a fetch directo con buena tasa de éxito.
3. Por eso cada celda numérica lleva una etiqueta de confianza:
   - **[FETCH]** = contenido obtenido por fetch directo (o vía `r.jina.ai`) de la URL oficial citada, con cita textual. Máxima confianza.
   - **[WS-OFICIAL]** = el dato proviene de un snippet de `WebSearch` que cita y resume literalmente el contenido de la URL oficial indicada, pero el fetch directo de esa URL fue bloqueado (403), así que no pude leer la página completa yo mismo. Confianza media — la URL es primaria, la vía de acceso no lo es al 100 %.
   - **`NO VERIFICABLE`** = no encontré cita de fuente oficial (ni fetch ni snippet oficial) que sostenga el dato. No se ha rellenado con el valor del corpus antiguo ni con una estimación.
4. Ningún dato de este documento proviene de una cuenta abierta, un pago realizado ni un registro. Cero acciones prohibidas por el contrato.

---

## 1. Tabla maestra por firma — reglas (pregunta 1 del contrato)

### 1.1 Topstep

| Parámetro | Valor | Cita |
|---|---|---|
| Trailing drawdown — mecanismo | **EOD (fin de día) sobre balance cerrado, pero vigilado en tiempo real sobre P&L NO realizado también.** El suelo (Maximum Loss Limit) solo sube al cierre del día; pero si el equity (realizado + flotante) toca el suelo vigente en CUALQUIER momento intradía, la cuenta se liquida al instante. | [FETCH] https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit (2026-09-01): *"The MLL updates at the end of each trading day but is monitored in real time throughout the session. Both realized and unrealized P&L count toward it."* |
| ¿Deja de trailar al alcanzar balance inicial + X? | Sí. Sube con cada nuevo máximo EOD, nunca baja, y **se bloquea permanentemente al llegar al balance inicial** (X = 0 en Combine; en Express Funded Account arranca en negativo y bloquea en $0). | [FETCH] misma URL: *"rises as your end-of-day balance grows, but never moves down. Once it reaches your starting balance, it locks permanently."* |
| MLL por tamaño de cuenta | 50K: **$2,000** · 100K: **$3,000** · 150K: **$4,500** | [FETCH] misma URL, tabla explícita |
| Daily Loss Limit — ¿existe? ¿sobre flotante? | Existe. Se dispara por **Net P&L** (no se especifica textualmente si es solo realizado o incluye flotante) hito. Al dispararse: se aplanan posiciones, se cancelan pendientes, **no es violación de regla** — se reanuda al día siguiente. | [FETCH] https://help.topstep.com/en/articles/10490293 (2026-09-01): *"Net P&L hits or exceeds the DLL... Open positions are flattened... No new trades until 5 PM CT next session... not a rule violation"* |
| Consistencia — Combine | **50 %**: el mejor día no puede superar el 50 % del Profit Target; si lo supera, el objetivo total sube (no reprueba). | [FETCH] https://help.topstep.com/en/articles/8284208 (2026-09-01): *"Your single best day of profit must stay at or below 50% of your Profit Target."* |
| Consistencia — Express Funded (payout) | **40 %**, no redondeado: `Mejor día / Beneficio neto total ≤ 40 %` para ser elegible a payout. | [FETCH] misma URL: *"Your Consistency % must be 40% or below to be Payout eligible. This is not rounded."* |
| Mínimo días de trading | Combine: se puede aprobar en **2 días**. Payout Express estándar: **5 días ganadores de ≥$150** netos. Payout ruta consistencia: **3 días** con ≥1 operación/día. | [FETCH] https://help.topstep.com/en/articles/8284233 y https://www.topstep.com/express-funded-account-rules (2026-09-01) |
| Contratos/micros por tamaño | 50K: 5 minis / 50 micros · 100K: 10 minis / 100 micros · 150K: 15 minis / 150 micros | [FETCH] https://help.topstep.com/en/articles/8284197 (2026-09-01), tabla explícita |
| Flat time obligatorio y penalización | **3:10 PM CT** todos los días laborables. Los risk managers empiezan a aplanar automáticamente a las **3:08 PM CT**. Es responsabilidad del trader estar plano antes; algunos productos cierran antes y hay que respetarlo. No hay "penalización" adicional descrita más allá del aplanado forzoso — no se documenta que cuente como violación de regla per se, pero si el aplanado forzoso te empuja al MLL, sí liquida la cuenta. | [FETCH] https://help.topstep.com/en/articles/8284206 (2026-09-01) |
| Noticias/eventos prohibidos | **No hay blackout obligatorio general.** Se permite operar NFP/CPI/FOMC. Excepción específica: Topstep **restringe aperturas nuevas en índices (ES, RTY, YM, NQ, NKD) en SIM antes de la publicación del CPI**. Cargar el tamaño máximo de posición justo antes de una noticia programada está en la lista de "Prohibited Trading Strategies" (no confirmado por fetch directo, solo por snippet oficial). | [WS-OFICIAL] artículo "Risk Adjustments: High Risk/High Volatility" en help.topstep.com, citado en WebSearch (2026-09-01) — **`NO VERIFICABLE` por fetch directo del listado completo de Prohibited Trading Strategies** (URL `help.topstep.com/en/articles/10305426`, no fetcheada con éxito en esta sesión) |

### 1.2 Apex Trader Funding

> **Aviso de bloqueo:** todo `apextraderfunding.com` y `support.apextraderfunding.com` devolvió 403 en fetch directo. Un único fetch tuvo éxito vía proxy `r.jina.ai` (la página de Prohibited Activities). El resto de celdas de Apex son **[WS-OFICIAL]** (snippet que cita la URL oficial) o `NO VERIFICABLE`. Trátese esta fila con más cautela que las demás.

| Parámetro | Valor | Cita |
|---|---|---|
| Trailing drawdown — mecanismo | Apex ofrece **dos productos paralelos desde marzo de 2026**: EOD (el suelo se recalcula solo al cierre) e **Intraday** (el suelo sigue el equity con P&L no realizado incluido, en tiempo real). No es un único modelo — hay que elegir el producto en la compra. | [WS-OFICIAL] apextraderfunding.com/help-center/evaluation-accounts-ea/intraday-trailing-drawdown-evaluations/, citado 2026-09-01 |
| ¿Deja de trailar al alcanzar balance + X? | El Safety Net del modelo **Intraday se bloquea al alcanzar balance inicial + $100**. Para EOD, no confirmé el offset exacto por fuente oficial. | [WS-OFICIAL] mismo artículo + resumen de búsqueda (2026-09-01) — offset EOD: `NO VERIFICABLE` |
| Importes de drawdown por tamaño de cuenta (2026 post-reestructuración de marzo) | `NO VERIFICABLE` con fuente primaria directa. Un snippet indexado (no fechado con certeza como "2026 actual", el artículo fuente lleva "Legacy" en el título) da 25K:$1,500 · 50K:$2,500 · 100K:$3,000 · 150K:$3,000 · 250K:$3,500 — **estos números podrían corresponder a la generación "Legacy" anterior a marzo de 2026, no a la actual.** No los doy por buenos. | [WS-OFICIAL, BAJA CONFIANZA] snippet sobre "Legacy Evaluation Rules" (apextraderfunding.com/help-center/evaluation-accounts-ea/legacy-evaluation-rules/), 2026-09-01 |
| Daily Loss Limit — ¿existe? | Según el propio mecanismo descrito por Apex: en el modelo **EOD** el DLL se suma al suelo trailing; en el modelo **Intraday** no hay DLL separado (el propio trailing hace ese papel). Importe exacto: `NO VERIFICABLE`. | [WS-OFICIAL] proptradingvibes/tradecovex citando apextraderfunding.com, 2026-09-01 |
| Regla de consistencia | **50 %** del beneficio usado en la solicitud, aplicado **solo en el momento del payout de la Performance Account**, NO durante la evaluación. Vigente desde que se relajó del 30 % anterior. | [WS-OFICIAL] múltiples snippets convergentes citando apextraderfunding.com, 2026-09-01 |
| Mínimo de días de trading | Evaluación EOD: se puede aprobar en **1 solo día de trading** (no hay mínimo de días en evaluación). Payout: **5 días** mínimo. | [WS-OFICIAL] 2026-09-01 |
| Contratos/micros por nivel | `NO VERIFICABLE` con cifras fiables 2026 — los números indexados están mezclados entre generaciones de producto. | — |
| Flat time obligatorio | `NO VERIFICABLE` — no lo encontré citado con fuente oficial en esta sesión. | — |
| Noticias prohibidas | `NO VERIFICABLE` explícitamente, pero la página oficial "Prohibited Activities" (fetch exitoso vía proxy) prohíbe **estrategias de "tick scalping"** (ratio riesgo/beneficio desproporcionado, ej. TP de 5 ticks con SL de 150 ticks) y **HFT**, lo cual afecta indirectamente a cualquier estrategia de noticias de muy corto plazo. | [FETCH vía r.jina.ai] apextraderfunding.com/help-center/getting-started/prohibited-activities/ (2026-09-01): *"setting a five-tick profit target with a 150-tick stop loss demonstrates unacceptable risk management"* |

### 1.3 My Funded Futures (MFFU)

| Parámetro | Valor | Cita |
|---|---|---|
| Trailing drawdown — mecanismo | **Varía por plan y por fase, esto es crítico y a menudo se simplifica mal:** Rapid en **evaluación** = EOD (el suelo solo sube al cierre del día con nuevo máximo EOD); Rapid en **fase Sim-Funded** = **cambia a Intraday** trailing (el suelo sigue el equity en tiempo real, con no-realizado incluido). Plan Flex = EOD estático (el suelo nunca trepa). Core/Pro = EOD 3 %. | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01) + [WS-OFICIAL] help.myfundedfutures.com sobre Rapid Plan 50K (2026-09-01) |
| ¿Deja de trailar al alcanzar balance + X? | Sí, en la fase Sim-Funded/Intraday de Rapid **se bloquea en balance inicial + $100**. | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01): *"locks At +$100"* |
| Drawdown por tamaño (Rapid) | 25K: $1,000 · 50K: $2,000 · 100K: $3,000 · 150K: $4,500 | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01) |
| Daily Loss Limit — ¿existe? | **NO existe en ningún plan de MFFU** (diferenciador de marca explícito). Único límite de pérdida es el drawdown trailing. | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01): *"None"* en todas las filas/fases + confirmado por [WS-OFICIAL] |
| Regla de consistencia | Rapid: **50 %, solo en evaluación** (se levanta al pasar a fondeada). Core: 50 %. Builder: 50 % solo en la etapa sim-funded, se levanta al pasar a live. Flex y Pro: sin consistencia. | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01) + [WS-OFICIAL] help.myfundedfutures.com/8528339 |
| Mínimo días de trading | **2 días** para aprobar evaluación Rapid/Pro. | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01) |
| Contratos/micros (Rapid) | 25K: 3 minis/30 micros · 50K: 5/50 · 100K: 8/80 · 150K: 10/100 | [FETCH] https://myfundedfutures.com/plans/rapid (2026-09-01) |
| Flat time obligatorio | `NO VERIFICABLE` explícitamente para MFFU en esta sesión (no lo vi citado en ninguna fuente oficial fetcheada). | — |
| Noticias/eventos prohibidos | **Prohibido explotar el "burst" de noticias** (straddles/strangles diseñados para la volatilidad de la publicación) y **disfrazar operaciones de noticias como estrategia normal**. Obligatorio no tener posiciones ni órdenes activas **2 minutos antes y después** de cualquier dato. Para noticias "Tier 1" (FOMC, Employment, CPI): posiciones cerradas **≥2 min antes**, reapertura permitida solo **2 min después**. Rapid Sim y Pro Sim: **T1 prohibido**. Evaluaciones y Builder: **T1 permitido**. | [FETCH] https://help.myfundedfutures.com/en/articles/8230009 (2026-09-01), citas literales incluidas arriba |

### 1.4 TradeDay

| Parámetro | Valor | Cita |
|---|---|---|
| Trailing drawdown — mecanismo | Depende del producto elegido (TradeDay 2.0, 2026): **Quick Pay Intraday** = sobre equity flotante en tiempo real. **Quick Pay EOD** y **Fast Pass EOD** = recalculado solo al cierre del día. La cuenta financiada de **Quick Pay usa SIEMPRE intraday trailing**, incluso si la evaluación fue EOD — **solo Fast Pass conserva EOD también en fondeada**. | [FETCH] https://www.tradeday.com/terms-and-conditions (2026-09-01): *"EOD Trailing Drawdown limits... you must not exceed the maximum amount"* + [WS-OFICIAL] resumen de tradeday.freshdesk.com sobre Quick Pay vs Fast Pass |
| Daily Loss Limit — ¿existe? | **No existe ningún Daily Loss Limit en ningún producto TradeDay 2.0** (rediseño de 2026, diferenciador de marca). | [WS-OFICIAL] múltiples fuentes citando tradeday.com, 2026-09-01 — no localicé el fetch directo de la frase exacta, por lo que queda en confianza media |
| Regla de consistencia | **Quick Pay: 30 %** del beneficio total en un solo día. **Fast Pass: 45 %.** Se elimina en la fase fondeada (Fast Pass). | [FETCH] https://tradeday.freshdesk.com/en/support/solutions/articles/103000008847 (2026-09-01): *"Quick Pay: No day greater than 30% of your total profits"* / *"Fast Pass: No day greater than 45%"* |
| Mínimo días de trading | Quick Pay: **5 días**. Fast Pass: **3 días**. | [FETCH] misma URL, 2026-09-01 |
| Contratos/micros por tamaño (Fast Pass EOD, triangulado, no fetch directo de tabla) | 50K: 2 minis/20 micros escalando +1 contrato por cada $2K de beneficio EOD · 100K: 10/50 · 150K: 15/50 — **cifras con confianza media, no verificadas por fetch directo de una tabla oficial.** | [WS-OFICIAL], 2026-09-01 |
| Flat time obligatorio y penalización | **Todas las posiciones cerradas al menos 10 minutos antes del cierre de cualquier sesión** ("day-trading only"). Penalización explícita no cuantificada más allá de que es una regla dura ("Trading Rules"). | [FETCH] https://www.tradeday.com/terms-and-conditions (2026-09-01): *"Day-trading only and all positions must be closed at least 10 minutes prior to the end of any session"* |
| Noticias/eventos prohibidos | No hay política de noticias específica localizada, pero **prohíbe explícitamente HFT (>200 trades/día), arbitraje de latencia (fills usando feed externo/lento o fuera del BBO), tick-queue gaming, hedging entre cuentas propias, order splitting y spoofing/layering.** Operar dentro del 2 % de un límite de precio hace perder la cuenta fondeada. | [FETCH] https://tradeday.freshdesk.com/en/support/solutions/articles/103000121031 (2026-09-01), citas literales arriba |
| **VPN/VPS — hallazgo crítico para el proyecto** | **TradeDay prohíbe el uso de VPS por completo**, no solo VPN: *"TradeDay does not allow the use of virtual private servers (VPS)"*. También prohíbe VPN/proxy/Apple Private Relay — exige operar desde la IP registrada. Detección en: paso a Funded Live, solicitudes de payout, hitos de $10,000 de beneficio bruto. Consecuencia: cierre de cuenta; reembolso parcial solo de setup fee y evaluaciones ya aprobadas. | [FETCH] https://tradeday.freshdesk.com/en/support/solutions/articles/103000295384 (2026-09-01), cita literal arriba |

### 1.5 Take Profit Trader (TPT)

**Por qué se añade:** marca con alto volumen de payouts rápidos y foco en trading manual/discrecional, mencionada de forma recurrente en 2026 como alternativa a Topstep para traders que priorizan velocidad de cobro (PRO permite solicitudes casi inmediatas). Relevante para contraste porque su política de automatización es de las más restrictivas del sector — sirve de "caso límite" en la matriz de compatibilidad.

| Parámetro | Valor | Cita |
|---|---|---|
| Trailing drawdown — mecanismo | **Test** (evaluación) = EOD, solo el balance de las 5:00 PM ET cuenta, se bloquea al llegar al balance inicial. **PRO** (fondeada) = **cambia a Intraday** (ganancias no realizadas mueven el suelo en tiempo real). **PRO+** vuelve a EOD. | [WS-OFICIAL] convergente de tradecovex/proptradingvibes citando takeprofittraderhelp.zendesk.com, 2026-09-01 |
| Regla de consistencia | **50 %**, no 40 % como afirman varias reseñas de terceros — **cifra confirmada por fetch directo de la página oficial "Rule 5: Be Consistent"**: *"no single trading day may exceed 50% of your total net profits"*. Si se incumple, NO se reprueba el Test: sube el objetivo de beneficio (`Nuevo objetivo = Net P/L × 2` hasta que el mejor día sea <50 %). | [FETCH] https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013 vía proxy r.jina.ai (2026-09-01), cita literal arriba |
| Mínimo días de trading | **3 días** desde el cambio de política de 2026 (antes eran 5). | [WS-OFICIAL] takeprofittrader.com/blog/3-day-evals, 2026-09-01 |
| Daily Loss Limit | `NO VERIFICABLE` con cifra exacta por fuente oficial en esta sesión (bloqueada). Corpus interno menciona $1,100 en 50K — no lo reproduzco como propio porque no lo verifiqué yo mismo. | — |
| Contratos/micros | `NO VERIFICABLE` por fuente oficial directa en esta sesión. | — |
| Comisiones (dato económico, no regla de riesgo) | Futuros: **$4.50 por contrato round-trip**; Micros: **$1.50 por contrato round-trip**, en Test y PRO. | [WS-OFICIAL] takeprofittraderhelp.zendesk.com/15172548967069, 2026-09-01 |
| Flat time / noticias | `NO VERIFICABLE` en esta sesión. | — |
| Automatización | **EAs / bots totalmente autónomos prohibidos.** Sí se permiten señales por webhook y trade copiers, con el trader como responsable de configuración y consecuencias. Bots comerciales compartidos, servicios de señales de pago y algoritmos compartidos entre varios usuarios están prohibidos. | [WS-OFICIAL] convergente, 2026-09-01 — `NO VERIFICABLE` por fetch directo del propio ToS (bloqueado) |

### 1.6 Tradeify

**Por qué se añade:** firma joven (≈2 años) con precio agresivo, sin activación en Growth/Select, y con la política de automatización más permisiva de "bot propio" entre las firmas de precio bajo — es el contraste directo con TPT/Apex y compite directamente con MFFU en la franja "barata + compatible con bot" que el corpus interno ya identificaba como la más relevante para el proyecto.

| Parámetro | Valor | Cita |
|---|---|---|
| Trailing drawdown — mecanismo | El suelo se recalcula **con el balance más alto registrado al CIERRE de una sesión**, y ese suelo se aplica en tiempo real durante la sesión SIGUIENTE — **tocar el suelo basta para reprobar, no hace falta cerrar el día por debajo**: una pérdida flotante intradía que toque el suelo rompe la cuenta aunque luego se recupere. | [WS-OFICIAL] help.tradeify.co citado por proptradingvibes, 2026-09-01 — `NO VERIFICABLE` por fetch directo (bloqueado 403 en help.tradeify.co, también vía proxy) |
| Drawdown por tamaño | 25K: $1,000 · 50K: $2,000 · 100K: $3,500 · 150K: $5,000 | [WS-OFICIAL] help.tradeify.co/10495897 citado, 2026-09-01 |
| Daily Loss Limit | Existe en **Growth, Lightning y Select Daily Funded**. **Select Flex NO tiene DLL.** Al dispararse: pausa el día, NO rompe la cuenta (a diferencia del drawdown, que sí es ruptura permanente). | [WS-OFICIAL] help.tradeify.co/10468321 citado, 2026-09-01 |
| Regla de consistencia | **40 %**: mejor día / beneficio neto total. Solo afecta si se puede operar/cobrar hoy, nunca rompe la cuenta directamente. | [WS-OFICIAL] help.tradeify.co, 2026-09-01 |
| Precio 50K (2026, no promo) | Growth: **$139/mes** · Select: **$159/mes** · Lightning (pago único, instant funding): **$469** | [WS-OFICIAL] blog.traderspost.io citando tradeify.co, 2026-09-01 |
| Split / payout | **90/10**, sin activación en cuentas fondeadas, máximo 5 cuentas Sim-Funded simultáneas por titular. Reset Select: **$95 fijo**. | [WS-OFICIAL] 2026-09-01 |
| **VPN/VPS** | Prohibido usar VPN/VPS **para el LOGIN inicial**; tras el login normal, el uso de VPS queda "a riesgo del trader" (no está expresamente prohibido para correr automatización después de conectarse). Esto es una política más laxa que Topstep/TradeDay pero **ambigua** — no hay declaración blanca-o-negro. | [WS-OFICIAL], 2026-09-01 — `NO VERIFICABLE` por fetch directo del ToS completo |
| Automatización | Permitida si: el trader es único dueño/desarrollador del bot, no es un bot compartido comercialmente, se declara a Tradeify, no hace HFT y solo copia entre cuentas propias del mismo titular (nunca replica a terceros). | [WS-OFICIAL], 2026-09-01 |

---

## 2. Economía real — pregunta 2 del contrato

| Firma | Precio evaluación 50K | Activación | Reset | Datos de mercado | Split | Payout mínimo | Frecuencia payout | Buffer 50K |
|---|---|---|---|---|---|---|---|---|
| Topstep | $49/mes (ruta activación) o $85/mes (ruta sin activación) [FETCH topstep.com/no-activation-fee, 2026-09-01] | $149 en ruta estándar; $0 en ruta "no activation" [FETCH] | = precio de la suscripción mensual [FETCH] | `NO VERIFICABLE` — no mencionado en la página de pricing fetcheada | 90/10 (100 % primeros $10,000 para cuentas legacy pre-12-ene-2026) [FETCH help.topstep.com/8284233] | $125 [FETCH] | Diaria tras 30 días ganadores en Live; si no, por ciclo de 5 días ganadores | No hay concepto de "buffer" explícito — el requisito es MLL + 5 días de $150+ |
| Apex | `NO VERIFICABLE` cifra exacta 2026 — snippet de baja confianza: EOD $390-$1,490 según tamaño / Intraday ~49-60% más barato [WS-OFICIAL, baja confianza] | PA: **$99 EOD / $79 Intraday**, a pagar dentro de 7 días de aprobar [WS-OFICIAL] | `NO VERIFICABLE` | `NO VERIFICABLE` | 100 % hasta cierto umbral, luego reparto — cifra exacta `NO VERIFICABLE` | `NO VERIFICABLE` | `NO VERIFICABLE` | `NO VERIFICABLE` |
| MFFU (Rapid) | "Starting at $105" en promo; **$209 precio regular** [FETCH myfundedfutures.com/plans/rapid] | $0 [FETCH] | `NO VERIFICABLE` cifra exacta, previsiblemente = precio de evaluación | `NO VERIFICABLE` | 90/10 [FETCH] | $500 [FETCH] | Diaria (tras buffer) [FETCH] | **$2,100** [FETCH] |
| TradeDay | `NO VERIFICABLE` cifra oficial exacta por fetch directo — snippets de precio muy dispersos ($59-$175/mes según promo) [WS-OFICIAL, baja confianza — mucha variación por campaña] | $0 en TradeDay 2.0 [WS-OFICIAL] | `NO VERIFICABLE` | `NO VERIFICABLE` | Quick Pay: 80% desde el día 1, hasta 95%; Fast Pass 80-90% [WS-OFICIAL] | `NO VERIFICABLE` (un snippet dice "sin mínimo" para Quick Pay, no confirmado por fetch) | Quick Pay: sin restricción declarada; procesado en 24h [WS-OFICIAL] | `NO VERIFICABLE` |
| Take Profit Trader | $170/mes de base según snippets; comisión aparte $4.50/contrato ($1.50 micros) [WS-OFICIAL / FETCH comisiones] | ~$130 fuera de promo [WS-OFICIAL, no fetch] | `NO VERIFICABLE` | `NO VERIFICABLE` | 90 % (PRO) [WS-OFICIAL] | `NO VERIFICABLE` | Rápida, "casi inmediata" en PRO según reseñas — sin cifra oficial fetcheada | `NO VERIFICABLE` — un snippet afirma PRO+ "no buffer requirement" [WS-OFICIAL, no confirmado] |
| Tradeify | Growth $139/mes, Select $159/mes (precio regular, no promo) [WS-OFICIAL] | $0 en Growth/Select [WS-OFICIAL] | Select: $95 fijo [WS-OFICIAL] | `NO VERIFICABLE` — un snippet afirma "incluye todos los fees de exchange y datos" en Growth [WS-OFICIAL, no confirmado por fetch directo] | 90/10 [WS-OFICIAL] | `NO VERIFICABLE` | `NO VERIFICABLE` | `NO VERIFICABLE` |

**Denegaciones documentadas de payout:** no encontré, en fuente PRIMARIA (oficial), ninguna estadística publicada de tasa de denegación de payout por firma. Lo único con respaldo semi-oficial es la cifra que el propio corpus interno atribuye a Topstep (12,4 % de aprobación de Combine, 28,3 % de financiados con al menos un payout en 2024) y a Earn2Trade (8,89 % aprobación 2025) — **no las re-verifiqué yo mismo esta sesión porque no son el foco de las 6 firmas seleccionadas y el contrato pide fuente primaria; las marco como heredadas del corpus, no confirmadas por mí.**

### Métrica reina: retiros netos − costes totales — lectura honesta

Con los datos que sí pude verificar (o triangular con confianza media), el ranking de **coste de entrada más bajo confirmado** para una cuenta 50K es:

1. **MFFU Rapid 50K:** $209 regular / activación $0 / buffer $2,100 antes del primer retiro — el coste de entrada es solo el precio de la suscripción hasta aprobar. [FETCH]
2. **Tradeify Growth 50K:** $139/mes, $0 activación — pero el drawdown de $2,000 y la consistencia del 40 % en payout son datos de confianza media (no fetch directo). [WS-OFICIAL]
3. **Topstep sin activación 50K:** $85/mes, $0 activación — más caro por mes que MFFU/Tradeify pero con la marca más contrastada y estadísticas públicas de aprobación real. [FETCH]
4. **TradeDay:** precio oficial exacto `NO VERIFICABLE` esta sesión (mucha dispersión promocional), pero split inicial 80 % y sin buffer parece competitivo si el precio real ronda los $60-90/mes reportados por múltiples fuentes.
5. **Apex y Take Profit Trader:** coste de entrada `NO VERIFICABLE` con precisión — no se puede calcular la métrica reina con honestidad para estas dos firmas en este informe.

**No puedo, con honestidad, dar un "beneficio neto" numérico por firma** porque para ninguna de las 6 tengo el conjunto completo {precio evaluación real hoy, activación real hoy, split real, buffer real, tasa de aprobación real} verificado 100 % por fetch directo. Donde el contrato exige elegir un número inventado, elijo `NO VERIFICABLE` en su lugar.

---

## 3. Automatización — pregunta 3 del contrato (la más importante para el proyecto)

Esta es la sección crítica porque el motor simula la firma barra a barra sobre equity flotante, y porque el PC opera con **IP residencial** (relevante porque varias firmas exigen justo eso, y otras lo prohíben si además hay VPS de por medio).

| Firma | ¿Algo/semi-auto permitido en ToS? | ¿Copy-trading entre cuentas propias? | ¿Qué descalifica? | Cita del párrafo del ToS |
|---|---|---|---|---|
| **Topstep** | **Sí, con condición dura:** *"Custom automated strategies and bots are allowed via the TopstepX / ProjectX API, subject to standard platform rules and our prohibition on high-frequency trading (HFT)."* Pero **todo el tráfico de órdenes debe originarse en el dispositivo personal**; un servidor privado solo puede usarse para histórico/backtesting/logging/dashboards de solo lectura — **nunca para transmitir, modificar o cancelar órdenes.** | Permitido (mencionado en fuentes secundarias, no confirmado por fetch directo del ToS de copy-trading) | **VPS, VPN y servidores remotos** para la ejecución → suspensión; conexión VPN dispara **Error 403 Forbidden** automático; HFT. La API ProjectX **no está disponible en la cuenta Live Funded** (según [WS-OFICIAL], no confirmado por fetch). | [FETCH] https://help.topstep.com/en/articles/11187768-topstepx-api-access (2026-09-01): *"All trading activity must originate from your personal device. The use of VPS, VPNs, and remote servers is prohibited by Topstep's Terms of Use."* + *"your server can watch and record, but it cannot trade."* |
| **Apex** | **Ambiguo y potencialmente contradictorio en la propia comunicación de Apex.** El texto oficial de "Prohibited Activities" dice literalmente: *"Rewards are intended to recognize human traders actively participating in the learning process, not to reward automated systems executing preprogrammed logic."* — lectura razonable: **NO para sistemas 100 % autónomos como cuenta originadora.** Fuentes secundarias de 2026 afirman que sí se permiten alertas webhook de TradingView y gestión semi-automática de posiciones ya abiertas manualmente — **no pude confirmar esto último con fetch directo**, así que queda como contradicción sin resolver entre marketing/reseñas y el ToS oficial. | Permitido **solo si la operación original se introduce manualmente**; el copiador replica, no origina. | **VPNs, proxy servers, cloud servers, anonymizing tools** para "misrepresenting, concealing, or disguising your identity, device, or location"; **HFT**; **tick-scalping** (TP muy pequeño con SL desproporcionado); compartir IP/MAC/tarjeta/copia de trades **con otro trader**. | [FETCH vía r.jina.ai] apextraderfunding.com/help-center/getting-started/prohibited-activities/ (2026-09-01), citas literales arriba |
| **MFFU** | Sí, estrategias automáticas propias permitidas. No se localizó una frase ToS explícita "algorithmic trading is permitted" en el fetch de `myfundedfutures.com/terms` — ese documento se centra en prohibiciones, no en permisos. | **Prohibido** usar múltiples cuentas propias para *"hedge, mirror, copy, or coordinate trades in a manner that provides an unfair advantage or manipulates simulated results"* — y explícitamente prohibido **atribuir/transferir el rendimiento de una cuenta a otra**. Esto es más restrictivo de lo que sugieren varias reseñas ("copying across all account types is allowed") — hay contradicción entre el ToS fetcheado y reseñas de terceros. | Tamaños de posición "sustancialmente mayores" a lo típico del historial del trader; actividad "inconsistente, errática, manipuladora o abusiva"; violar límites de drawdown. VPN/VPS: **no mencionado en el documento de Términos fetcheado** — `NO VERIFICABLE` directamente, aunque el corpus interno (sección 6) afirma que MFFU permite VPS con IP estática dedicada. | [FETCH] https://myfundedfutures.com/terms (2026-09-01): *"use multiple accounts to hedge, mirror, copy, or coordinate trades in a manner that provides an unfair advantage or manipulates simulated results"* / *"you may not transfer, combine, or otherwise attribute your Account performance... to or with any other Account or User."* |
| **TradeDay** | Sí, pero **solo mediante las plataformas soportadas** (NinjaTrader, Tradovate, TradingView, Jigsaw, Quantower) usando sus funciones de automatización nativas. **API propia de Tradovate NO expuesta al trader** por TradeDay. | **Riesgo real de confusión con "hedging" prohibido:** copiar operaciones entre cuentas propias en la MISMA dirección se tolera como "escalar estrategia", pero *"If multiple users are making the same trades, then all the accounts will be shut down"* — la frase está redactada pensando en varios TRADERS, no en un solo titular con varias cuentas, pero el riesgo de falso positivo del sistema de detección es real. | **VPS prohibido sin excepciones** (no solo VPN): *"TradeDay does not allow the use of virtual private servers (VPS)"*. Bots/algos de terceros comprados; HFT (>200 trades/día); arbitraje de latencia; tick-queue gaming; hedging entre cuentas; order splitting; spoofing/layering; operar dentro del 2 % de un límite de precio. | [FETCH] https://tradeday.freshdesk.com/en/support/solutions/articles/103000295384 (VPS/VPN, 2026-09-01) + https://tradeday.freshdesk.com/en/support/solutions/articles/103000085101 (algos, 2026-09-01) + https://tradeday.freshdesk.com/en/support/solutions/articles/103000121031 (prohibidas, 2026-09-01) |
| **Take Profit Trader** | **EAs / bots totalmente autónomos prohibidos** por política declarada (no confirmado por fetch directo del ToS-UTP, que devolvió 403). Sí se permiten señales webhook y trade copiers bajo responsabilidad del trader. | Permitido copiar entre hasta 5 cuentas propias (dato de confianza media, [WS-OFICIAL]) | Bots comerciales compartidos; servicios de señales de pago; algoritmos compartidos entre traders; posiciones contrarias simultáneas (hedging) prohibidas explícitamente. VPN/VPS: sin restricción explícita localizada — contrasta con el resto de firmas de esta tabla. | `NO VERIFICABLE` por fetch directo — URL oficial del "Universal Trading Policies" (takeprofittraderhelp.zendesk.com/34431153546397) devolvió 403 en ambas vías intentadas |
| **Tradeify** | Sí, con 4 condiciones: dueño único del bot, no comercial/compartido, declarado a Tradeify, no HFT. | Solo entre cuentas propias del mismo titular, misma dirección, nunca a terceros. | HFT; bot compartido comercialmente; VPN/VPS **para el login inicial** (después del login, "a riesgo del trader", zona gris). | `NO VERIFICABLE` por fetch directo (help.tradeify.co bloqueado en ambas vías) |

**Conclusión de compatibilidad automatización — hallazgo más importante de todo el informe:** de las 6 firmas, **Topstep y TradeDay prohíben VPS de forma absoluta y sin ambigüedad, confirmado por fetch directo del propio ToS** (no por reseña de terceros). Esto es exactamente lo que ya concluía `docs/conexiones_automatizar/06_MARCO_NORMATIVO_IPS_PROP_FIRMS.md` — mi investigación independiente lo **CONFIRMA** con cita textual nueva y de fecha más reciente (2026-09-01 vs. 2026-08-25 del corpus). Apex tiene una postura oficial más restrictiva con la automatización en sí (no solo con la IP) de lo que sugieren varias reseñas de 2026 — este es un punto de fricción real entre "lo que dicen los blogs" y "lo que dice el ToS", y para el objetivo del proyecto (motor barra a barra automático) pesa más el ToS.

Dado que el PC opera con **IP residencial** (no de datacenter), Topstep y TradeDay dejan de ser un problema de "tipo de IP" — el problema es el **VPS como tal**, incluso ejecutándose con salida residencial vía túnel. Si Hermes/el motor corren en un VPS (aunque salga con IP residencial mediante proxy ISP o Tailscale a casa), TradeDay lo prohíbe literalmente por definición ("no VPS"), y Topstep exige que el tráfico de órdenes se origine en el dispositivo personal, no en cualquier servidor. La única forma limpia de operar Topstep/TradeDay con automatización sería ejecutando el motor **en el propio PC físico** (el de IP residencial), no en un VPS con salida residencial simulada.

---

## 4. Compatibilidad con nuestras estrategias — pregunta 4 del contrato

| Firma | ORB/VWAP-reversion (varias operaciones/día) vs. regla de consistencia | Sizing de micros vs. límite de pérdida diaria | Cierre intradía obligatorio |
|---|---|---|---|
| Topstep | Consistencia 50 % en Combine es holgada para una estrategia con >2 días operados; la 40 % en Express payout es más exigente — obliga a repartir beneficio en ≥3 sesiones antes de cobrar. Compatible si el sistema no concentra el 60%+ del PnL en un solo día bueno. | DLL existe y aplica sobre Net P&L (probablemente incluye flotante, no confirmado al 100%) — el motor debe simularlo, no es solo el MLL. | 3:10 PM CT es temprano para NY (16:10 hora de NY) — cualquier ORB de apertura US va sobrado de margen, pero una estrategia con holding hasta el cierre europeo/asiático quedaría cortada. |
| Apex | Sin consistencia en evaluación (facilita pasar rápido con pocos días); 50 % en payout. Compatible en fase de examen. | DLL exacto `NO VERIFICABLE` — el motor NO puede simular Apex con fiabilidad hoy sin ese dato. | `NO VERIFICABLE` flat time — mismo problema. |
| MFFU | 50 % solo en evaluación de Rapid/Core, se cae al pasar a fondeada — muy favorable para frecuencia intradía alta. Sin DLL nunca, así que el único freno real es el trailing (EOD en evaluación, intraday en sim-funded). | **Sin DLL** simplifica el sizing — el único techo es el drawdown trailing, que si es intraday en fase fondeada, el motor debe simularlo sobre equity flotante real (coincide con cómo dice el proyecto que ya simula). | `NO VERIFICABLE` — sin dato de flat time oficial. |
| TradeDay | Quick Pay 30 % es la más estricta de las 6 firmas — una estrategia ORB concentrada en la apertura US puede chocar con esto si un solo día domina el PnL. Fast Pass 45 % es más cómoda. | Sin DLL en ningún producto 2026 — el único freno es el trailing (intraday para Quick Pay fondeada). | Cierre 10 min antes del final de cualquier sesión — compatible con cualquier estrategia que no busque holding sobre el cierre, que es justo el perfil declarado (intradía CME). |
| Take Profit Trader | 50 % consistencia en el Test — igual de holgada que Topstep Combine. PRO cambia a trailing intraday, coherente con cómo simula el motor. | DLL `NO VERIFICABLE` en cifra — no se puede afinar sizing con certeza. | `NO VERIFICABLE`. |
| Tradeify | 40 % consistencia, similar a MFFU/Tradeify — cómoda para frecuencia alta si no hay un día que se lleve más del 40% del total. | DLL existe en Growth/Lightning/Select-Daily (no en Select Flex) — el motor debe elegir el producto sin DLL (Select Flex) si el sizing de micros va ajustado, o simular el DLL si se usa Growth. | `NO VERIFICABLE` flat time. |

**Lectura general:** el "tocar el suelo basta, no hace falta cerrar por debajo" que describe Tradeify para su trailing (y que aplica igual, por diseño, al MLL de Topstep vigilado en tiempo real) es exactamente el motivo por el que el proyecto ya simula barra a barra sobre equity flotante en vez de sobre equity cerrado — la investigación confirma que esa decisión de diseño es correcta para Topstep, MFFU (fase fondeada), Take Profit Trader (fase PRO) y probablemente Apex/TradeDay Quick Pay Intraday. Solo el trailing puramente EOD (evaluación de Topstep/MFFU/TPT, TradeDay Fast Pass) tolera simular sobre balance de cierre — y aun así, el MLL de Topstep confirma por fetch directo que el suelo EOD se vigila con P&L flotante intradía para la LIQUIDACIÓN, aunque el suelo en sí solo suba al cierre. Esto es una distinción sutil que vale la pena dejar explícita para quien construya el simulador: **"EOD" en el nombre del producto no siempre significa "el motor solo mira el cierre del día" — puede significar "el suelo solo SUBE al cierre, pero se puede TOCAR y perder en cualquier momento intradía".**

---

## 5. Ranking final — pregunta 5 del contrato

| # | Firma | Coste entrada 50K confirmado | Facilidad de pasar (consistencia + días mínimos) | Compatibilidad automatización (ToS, no reseñas) | Compatibilidad IP residencial + VPS | Confianza de los datos de este informe |
|---|---|---|---|---|---|---|
| 1 | **MFFU (Rapid)** | $209 regular / $0 activación / buffer $2,100 [FETCH] | 50 % solo eval, 2 días mín, **sin DLL nunca** [FETCH] | Bot propio permitido; **copy-trading entre cuentas propias más restringido de lo que dicen las reseñas** (ToS fetcheado lo prohíbe si "manipula resultados simulados") [FETCH] | VPS: `NO VERIFICABLE` por fetch directo de ToS (el corpus interno dice "permitido con IP estática", no confirmado por mí) | **Alta** — 5 de 8 celdas clave con [FETCH] directo |
| 2 | **Topstep** | $85/mes sin activación, $0 activación [FETCH] | 50 % Combine / 40 % payout, 2 días mín [FETCH] | Bot permitido vía API oficial **[FETCH]**, pero con restricción dura de "solo desde dispositivo personal" | **VPS prohibido de forma absoluta, confirmado [FETCH]** — encaja con IP residencial solo si el motor corre en el PC físico, no en un VPS con salida residencial simulada | **Muy alta** — la firma mejor documentada por fetch directo de las 6 |
| 3 | **TradeDay (Fast Pass)** | Precio exacto `NO VERIFICABLE`, pero 45 % consistencia y 3 días mín. son los más cómodos del grupo [FETCH] | 45 % consistencia, 3 días [FETCH] | Solo vía plataformas soportadas, sin API propia [FETCH] | **VPS prohibido de forma absoluta, confirmado [FETCH]** — mismo problema que Topstep | Alta en reglas, media en precio |
| 4 | **Tradeify (Select Flex)** | ~$159/mes Select, $0 activación [WS-OFICIAL] | 40 % consistencia [WS-OFICIAL] | Bot propio permitido con 4 condiciones [WS-OFICIAL] | VPN/VPS prohibido solo en el login, zona gris después — la más permisiva del grupo en teoría, pero sin confirmación por fetch directo | Media — nada confirmado por fetch directo propio |
| 5 | **Take Profit Trader** | $170/mes + comisión aparte por contrato [WS-OFICIAL/FETCH parcial] | 50 % consistencia [FETCH], 3 días mín [WS-OFICIAL] | **Bots autónomos prohibidos** — solo copiadores/webhooks | Sin restricción de VPN/VPS localizada — pero irrelevante si no se puede automatizar el origen de la operación | Media — un dato de alta confianza (consistencia), resto medio/bajo |
| 6 | **Apex** | `NO VERIFICABLE` con precisión | Sin consistencia en evaluación (fácil pasar) pero 50 % en payout [WS-OFICIAL] | **Postura oficial ambigua/restrictiva con la automatización como origen** [FETCH parcial] — contradice el discurso de varias reseñas 2026 | VPN/proxy prohibido explícitamente para ocultar identidad [FETCH parcial]; VPS no aclarado con la misma claridad que Topstep/TradeDay | Baja-media — la firma peor documentada de las 6 por bloqueo casi total del dominio |

### Recomendación razonada (solo recomendación — la compra la decide Emilio)

Con los números que pude verificar de verdad: **MFFU Rapid 50K** es la mejor primera compra si el motor puede operar sin DLL y con trailing que pasa de EOD a intraday al fondear (que es justo el modelo que el proyecto ya simula sobre equity flotante). Su único punto débil real, encontrado en esta investigación y no en el corpus anterior, es que **el ToS de copy-trading entre cuentas propias es más restrictivo de lo que asumía el corpus** — antes de escalar a multi-cuenta con MFFU, habría que confirmar por escrito con soporte que el patrón de copia previsto no cae en su cláusula de "coordinar operaciones... que manipule resultados simulados".

**Topstep** es la segunda opción, con el dato más sólido de todo el informe (API de automatización con ToS citado literalmente) pero con una limitación de arquitectura real: **el motor no puede correr en el VPS actual del proyecto y salir con IP residencial simulada** — Topstep exige que el tráfico se origine en el dispositivo personal, no en cualquier servidor con cualquier IP. Si la arquitectura de Hermes ya asume ejecución en VPS (como sugieren los documentos de `conexiones_automatizar`), Topstep requeriría o bien mover la ejecución de órdenes al PC físico, o bien aceptar que la API de Topstep queda fuera de alcance.

**TradeDay** comparte exactamente la misma limitación de VPS que Topstep, con reglas de consistencia más cómodas (45 % en Fast Pass) pero peor documentación de precio actual.

No recomiendo Apex ni Take Profit Trader como primera compra para un motor automático: Apex tiene la peor cobertura documental de las 6 (dominio bloqueado casi por completo) y una postura oficial que, leída literalmente, no encaja con "recompensar sistemas automatizados ejecutando lógica preprogramada"; Take Profit Trader prohíbe bots autónomos de forma explícita y consistente en todas las fuentes consultadas.

---

## 6. Discrepancias contra el corpus interno (leído DESPUÉS de la investigación independiente)

Comparado contra `docs/Fondeo/BASE_DATOS_EMPRESAS_FONDEO_FUTUROS_2026-08-02.md` (08-02-2026) y `docs/conexiones_automatizar/00_INFORME_MAESTRO_CONEXIONES.md` + `06_MARCO_NORMATIVO_IPS_PROP_FIRMS.md` (08-25-2026):

| # | Ítem | Corpus interno dice | Esta investigación (2026-09-01) encuentra | Veredicto |
|---|---|---|---|---|
| 1 | Topstep VPS/VPN | "Prohibido en entorno abierto", con matiz de túnel Tailscale como solución (`06`, sección 6.1 y 8.2) | **Confirmado exactamente igual, con cita textual nueva y directa del ToS**: *"All trading activity must originate from your personal device. The use of VPS, VPNs, and remote servers is prohibited."* | **CONFIRMADA** — coincidencia total, con fuente más reciente y más literal |
| 2 | TradeDay VPS/VPN | "Estrictamente Prohibido... no permite el uso de VPS, VPNs, proxies ni servicios como Apple Private Relay" (`06`, sección 6.7) | **Confirmado exactamente igual, cita textual**: *"TradeDay does not allow the use of virtual private servers (VPS)"* | **CONFIRMADA** — coincidencia total |
| 3 | Apex automatización | "Estrictamente Prohibido el trading 100% algorítmico/automatizado en las evaluaciones... diseñados para evaluar la operativa humana discrecional" (`06`, sección 6.3) y sección 1 de la base de datos: "prohíbe bots, algoritmos y automatización de la cuenta originadora" | **Confirmado por fetch directo (vía proxy) del propio texto oficial**: *"Rewards are intended to recognize human traders... not to reward automated systems executing preprogrammed logic."* Pero además encontré **fuentes secundarias de 2026 que afirman lo contrario** (webhooks de TradingView permitidos, DCA bots permitidos) — el corpus no menciona esta tensión. | **CONFIRMADA en la postura oficial**, pero **AMPLIADA**: el corpus no registraba la contradicción entre ToS oficial y discurso de reseñas/comparadores 2026, que sí documento aquí |
| 4 | Topstep pricing 50K sin activación | "95 USD mensuales" (sección 8, tabla de costes, 2026-08-02) | **$85/mes** según fetch directo de `topstep.com/no-activation-fee` el 2026-09-01 | **REFUTADA (parcialmente) o precio cambiado** — diferencia de $10/mes entre el 2 de agosto y el 1 de septiembre. Puede ser cambio real de precio o variación de campaña; no puedo distinguir cuál sin más histórico. Recomiendo re-verificar en checkout antes de comprar, tal como el propio corpus ya advertía que hay que hacer |
| 5 | Take Profit Trader — regla de consistencia | "Sin regla de consistencia tradicional" (sección 10.9, "Reglas 50K") | **Existe y es del 50 %**, confirmado por fetch directo del artículo oficial "Rule 5: Be Consistent": *"no single trading day may exceed 50% of your total net profits"* | **REFUTADA** — este es el hallazgo de discrepancia más claro y mejor sustentado del informe. El corpus estaba equivocado o la regla se introdujo/hizo pública entre agosto y septiembre de 2026 |
| 6 | MFFU copy-trading entre cuentas propias | Sección 1: "permite estrategias automáticas propias" sin matiz negativo sobre copy-trading entre cuentas propias del mismo titular; `06` sección 6.2 dice VPS "✅ Permitido" sin matizar copy-trading | El **propio Términos y Condiciones de MFFU** (fetch directo) prohíbe usar múltiples cuentas para *"hedge, mirror, copy, or coordinate trades in a manner that provides an unfair advantage or manipulates simulated results"* y prohíbe *"transfer, combine, or otherwise attribute"* el rendimiento de una cuenta a otra | **AMPLIADA / matiz nuevo, no exactamente una contradicción** — el corpus no es falso, pero es más optimista de lo que el ToS literal permite. Antes de construir un sistema de copy-trading multi-cuenta sobre MFFU, hay que leer esta cláusula con un abogado o confirmar por escrito con soporte |
| 7 | MFFU Daily Loss Limit | La base de datos (sección 10.4) dice "Sin daily loss limit" — coincide | **Confirmado exactamente**, con cita directa: *"None"* en todas las fases/tamaños de Rapid | **CONFIRMADA** |
| 8 | Apex — importes de drawdown/DLL 2026 | Sección 10.6: "Drawdown EOD: 2.000 USD. Daily Loss Limit: 1.000 USD. Máximo: 6 contratos" para la "cuenta nueva EOD 50K" | No pude confirmar estos números con fuente primaria (dominio bloqueado); un snippet de baja confianza sobre un artículo titulado "Legacy" da cifras distintas ($2,500 drawdown, sin DLL mencionado, 10 contratos) | **NI CONFIRMADA NI REFUTADA** — ninguna de las dos fuentes (corpus ni esta investigación) tiene respaldo de fetch directo verificable hoy; ambas deberían tratarse como no confiables hasta que alguien consiga pasar el bloqueo de Cloudflare de Apex |
| 9 | Tradeify — ausencia en la matriz de IP/VPS del corpus | `06` (Marco Normativo IPs) tiene una matriz de 8 firmas (Topstep, MFFU, Apex, Bulenox, FundedNext, TPT, TradeDay, Earn2Trade) — **Tradeify no aparece en esa tabla en absoluto** | Encontré política propia de Tradeify: VPN/VPS prohibido solo en el login, zona gris después | **AÑADIDA** — no es una discrepancia sino un hueco del corpus que esta investigación llena parcialmente (con confianza media, no fetch directo) |
| 10 | TradeDay — consistencia por producto | Sección 10.3: "30 % en modalidades estándar; 45 % en la modalidad EOD completa" | Confirmado por fetch directo, pero con el mapeo correcto de nombres: **Quick Pay = 30 %, Fast Pass = 45 %** (el corpus usa "estándar"/"EOD completo", que corresponden aproximadamente pero no usa la nomenclatura 2.0 actual de TradeDay) | **CONFIRMADA en cifra, actualizada en nomenclatura** — TradeDay renombró sus productos a "Quick Pay"/"Fast Pass" en su rediseño 2.0 de 2026, y el corpus (fechado 08-02) parece escrito justo en la transición, mezclando ambos vocabularios |
| 11 | Topstep — Maximum Loss Limit por tamaño | El corpus no da la cifra exacta de MLL para Topstep en la sección 10.1 (solo dice "Objetivo: 3.000 USD" y "Maximum Loss Limit" sin cifra) | **$2,000 / $3,000 / $4,500** para 50K/100K/150K, confirmado por fetch directo | **AÑADIDA** — dato que el corpus no tenía, ahora con fuente primaria |

---

## 7. Propuesta de `PROP_FIRM_CATALOG` (Python) — lista para el orquestador

```python
"""
PROP_FIRM_CATALOG — catálogo re-verificado 2026-09-01 por AG-10.
Cada valor lleva su fuente en el campo "source" del mismo nivel o del padre.
confidence: "fetch" (fetch directo de URL oficial) | "ws_official" (snippet de
            WebSearch que cita literalmente una URL oficial, fetch directo bloqueado)
            | "unverified" (no hay fuente primaria — usar con máxima cautela)
NOTA: los campos marcados None + confidence="unverified" son intencionalmente
None. NO SUSTITUIR por valores estimados ni por los del corpus 08-2026 sin
volver a verificar.
"""

from dataclasses import dataclass, field
from typing import Optional, Literal

Confidence = Literal["fetch", "ws_official", "unverified"]


@dataclass
class SourceRef:
    url: str
    captured: str  # ISO date
    confidence: Confidence
    quote: Optional[str] = None


@dataclass
class DrawdownRule:
    mechanism: Literal["eod_closed_balance", "intraday_floating_equity", "eod_static"]
    amount_by_size: dict  # {"50000": 2000, ...}
    locks_at_balance_plus: Optional[float]  # None si no aplica / no verificable
    source: SourceRef


@dataclass
class DailyLossLimitRule:
    exists: bool
    on_floating_equity: Optional[bool]  # None = no verificable
    amount_by_size: Optional[dict]
    breaks_account: bool  # False = solo pausa el día
    source: SourceRef


@dataclass
class ConsistencyRule:
    percent: Optional[float]
    applies_to: str  # "evaluation" | "payout" | "both" | "eval_only_lifts_when_funded"
    source: SourceRef


@dataclass
class AutomationPolicy:
    algo_allowed_as_origin: Optional[bool]  # None = ambiguo/contradictorio (ver Apex)
    copy_trading_own_accounts: Optional[bool]
    vps_allowed: Optional[bool]  # False = prohibido explícitamente
    vpn_allowed: Optional[bool]
    hft_prohibited: bool
    disqualifiers_quote: str
    source: SourceRef


@dataclass
class Economics:
    eval_price_50k: Optional[float]
    activation_fee: Optional[float]
    reset_cost: Optional[float]
    data_fees_separate: Optional[bool]
    payout_split: Optional[float]  # trader's share, e.g. 0.90
    payout_minimum: Optional[float]
    payout_frequency: Optional[str]
    buffer_50k: Optional[float]
    source: SourceRef


@dataclass
class PropFirm:
    firm_id: str
    name: str
    last_verified: str = "2026-09-01"
    drawdown: DrawdownRule = None
    daily_loss_limit: DailyLossLimitRule = None
    consistency: ConsistencyRule = None
    min_trading_days: Optional[int] = None
    min_trading_days_source: Optional[SourceRef] = None
    max_contracts_by_size: Optional[dict] = None
    max_contracts_source: Optional[SourceRef] = None
    flat_time_ct: Optional[str] = None
    flat_time_source: Optional[SourceRef] = None
    news_policy: Optional[str] = None
    news_policy_source: Optional[SourceRef] = None
    automation: AutomationPolicy = None
    economics: Economics = None


PROP_FIRM_CATALOG: dict[str, PropFirm] = {

    "topstep": PropFirm(
        firm_id="topstep",
        name="Topstep",
        drawdown=DrawdownRule(
            mechanism="eod_closed_balance",  # suelo solo sube EOD, PERO se vigila
                                              # en tiempo real sobre equity flotante
                                              # para la liquidacion -> ver nota motor
            amount_by_size={"50000": 2000, "100000": 3000, "150000": 4500},
            locks_at_balance_plus=0,
            source=SourceRef(
                url="https://help.topstep.com/en/articles/8284204-what-is-the-maximum-loss-limit",
                captured="2026-09-01", confidence="fetch",
                quote="The MLL updates at the end of each trading day but is "
                      "monitored in real time throughout the session. Both "
                      "realized and unrealized P&L count toward it.",
            ),
        ),
        daily_loss_limit=DailyLossLimitRule(
            exists=True, on_floating_equity=None, amount_by_size=None,
            breaks_account=False,
            source=SourceRef(
                url="https://help.topstep.com/en/articles/10490293",
                captured="2026-09-01", confidence="fetch",
                quote="Net P&L hits or exceeds the DLL... not a rule violation",
            ),
        ),
        consistency=ConsistencyRule(
            percent=50.0, applies_to="evaluation",
            source=SourceRef(
                url="https://help.topstep.com/en/articles/8284208",
                captured="2026-09-01", confidence="fetch",
                quote="Your single best day of profit must stay at or below "
                      "50% of your Profit Target.",
            ),
        ),
        min_trading_days=2,
        min_trading_days_source=SourceRef(
            url="https://help.topstep.com/en/articles/8284197",
            captured="2026-09-01", confidence="fetch",
        ),
        max_contracts_by_size={"50000": {"minis": 5, "micros": 50},
                                "100000": {"minis": 10, "micros": 100},
                                "150000": {"minis": 15, "micros": 150}},
        max_contracts_source=SourceRef(
            url="https://help.topstep.com/en/articles/8284197",
            captured="2026-09-01", confidence="fetch",
        ),
        flat_time_ct="15:10",
        flat_time_source=SourceRef(
            url="https://help.topstep.com/en/articles/8284206",
            captured="2026-09-01", confidence="fetch",
            quote="All positions must be closed by 3:10 PM CT every weekday.",
        ),
        news_policy="No blackout general; restriccion de apertura en indices "
                    "(ES/RTY/YM/NQ/NKD) antes de CPI en SIM.",
        news_policy_source=SourceRef(
            url="https://help.topstep.com/en/articles/13613539",
            captured="2026-09-01", confidence="ws_official",
        ),
        automation=AutomationPolicy(
            algo_allowed_as_origin=True, copy_trading_own_accounts=True,
            vps_allowed=False, vpn_allowed=False, hft_prohibited=True,
            disqualifiers_quote="All trading activity must originate from your "
                                 "personal device. The use of VPS, VPNs, and "
                                 "remote servers is prohibited by Topstep's "
                                 "Terms of Use.",
            source=SourceRef(
                url="https://help.topstep.com/en/articles/11187768-topstepx-api-access",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
        economics=Economics(
            eval_price_50k=85.0,  # ruta "sin activacion", mensual
            activation_fee=0.0,
            reset_cost=None, data_fees_separate=None,
            payout_split=0.90, payout_minimum=125.0,
            payout_frequency="5 dias ganadores de $150+ por ciclo; diaria tras 30 dias en Live",
            buffer_50k=None,
            source=SourceRef(
                url="https://www.topstep.com/no-activation-fee",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
    ),

    "apex": PropFirm(
        firm_id="apex", name="Apex Trader Funding",
        drawdown=DrawdownRule(
            mechanism="intraday_floating_equity",  # producto "Intraday"; existe
                                                     # tambien producto "EOD" paralelo
            amount_by_size=None,  # NO VERIFICABLE con confianza por fetch directo
            locks_at_balance_plus=100,  # solo confirmado para el producto Intraday
            source=SourceRef(
                url="https://apextraderfunding.com/help-center/evaluation-accounts-ea/intraday-trailing-drawdown-evaluations/",
                captured="2026-09-01", confidence="ws_official",
            ),
        ),
        daily_loss_limit=DailyLossLimitRule(
            exists=None, on_floating_equity=None, amount_by_size=None,
            breaks_account=None,
            source=SourceRef(url="", captured="2026-09-01", confidence="unverified"),
        ),
        consistency=ConsistencyRule(
            percent=50.0, applies_to="payout",
            source=SourceRef(
                url="https://apextraderfunding.com/help-center/legacy-helpful-items/what-are-the-consistency-rules-for-legacy-pa-and-funded-accounts/",
                captured="2026-09-01", confidence="ws_official",
            ),
        ),
        min_trading_days=1,  # evaluacion EOD, segun snippet oficial (aprobable en 1 dia)
        min_trading_days_source=SourceRef(
            url="https://apextraderfunding.com/help-center/evaluation-accounts-ea/legacy-evaluation-rules/",
            captured="2026-09-01", confidence="ws_official",
        ),
        max_contracts_by_size=None,  # NO VERIFICABLE
        flat_time_ct=None, news_policy=None,
        automation=AutomationPolicy(
            algo_allowed_as_origin=False,  # lectura literal del ToS oficial
            copy_trading_own_accounts=True,  # solo si origen es manual
            vps_allowed=None, vpn_allowed=False, hft_prohibited=True,
            disqualifiers_quote="Rewards are intended to recognize human traders "
                                 "actively participating in the learning process, "
                                 "not to reward automated systems executing "
                                 "preprogrammed logic.",
            source=SourceRef(
                url="https://apextraderfunding.com/help-center/getting-started/prohibited-activities/",
                captured="2026-09-01", confidence="fetch",  # via r.jina.ai
            ),
        ),
        economics=Economics(
            eval_price_50k=None, activation_fee=None, reset_cost=None,
            data_fees_separate=None, payout_split=None, payout_minimum=None,
            payout_frequency=None, buffer_50k=None,
            source=SourceRef(url="", captured="2026-09-01", confidence="unverified"),
        ),
    ),

    "mffu": PropFirm(
        firm_id="mffu", name="My Funded Futures",
        drawdown=DrawdownRule(
            mechanism="eod_closed_balance",  # en evaluacion Rapid; pasa a
                                              # intraday_floating_equity al fondear
            amount_by_size={"25000": 1000, "50000": 2000, "100000": 3000, "150000": 4500},
            locks_at_balance_plus=100,  # confirmado para fase Sim-Funded/Intraday
            source=SourceRef(
                url="https://myfundedfutures.com/plans/rapid",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
        daily_loss_limit=DailyLossLimitRule(
            exists=False, on_floating_equity=None, amount_by_size=None,
            breaks_account=False,
            source=SourceRef(
                url="https://myfundedfutures.com/plans/rapid",
                captured="2026-09-01", confidence="fetch",
                quote="None (all sizes, all stages)",
            ),
        ),
        consistency=ConsistencyRule(
            percent=50.0, applies_to="eval_only_lifts_when_funded",
            source=SourceRef(
                url="https://myfundedfutures.com/plans/rapid",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
        min_trading_days=2,
        min_trading_days_source=SourceRef(
            url="https://myfundedfutures.com/plans/rapid",
            captured="2026-09-01", confidence="fetch",
        ),
        max_contracts_by_size={"25000": {"minis": 3, "micros": 30},
                                "50000": {"minis": 5, "micros": 50},
                                "100000": {"minis": 8, "micros": 80},
                                "150000": {"minis": 10, "micros": 100}},
        max_contracts_source=SourceRef(
            url="https://myfundedfutures.com/plans/rapid",
            captured="2026-09-01", confidence="fetch",
        ),
        flat_time_ct=None, news_policy="Prohibido explotar burst de noticias; "
            "sin ordenes/posiciones 2 min antes/despues de cualquier dato; T1 "
            "(FOMC/Employment/CPI) prohibido en Rapid Sim y Pro Sim, permitido "
            "en evaluaciones y Builder.",
        news_policy_source=SourceRef(
            url="https://help.myfundedfutures.com/en/articles/8230009",
            captured="2026-09-01", confidence="fetch",
        ),
        automation=AutomationPolicy(
            algo_allowed_as_origin=True,
            copy_trading_own_accounts=False,  # OJO: el ToS fetcheado lo prohibe
                                                # si "manipula resultados simulados"
                                                # -- mas restrictivo que el corpus
            vps_allowed=None, vpn_allowed=False, hft_prohibited=True,
            disqualifiers_quote="use multiple accounts to hedge, mirror, copy, "
                                 "or coordinate trades in a manner that provides "
                                 "an unfair advantage or manipulates simulated "
                                 "results",
            source=SourceRef(
                url="https://myfundedfutures.com/terms",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
        economics=Economics(
            eval_price_50k=209.0, activation_fee=0.0, reset_cost=None,
            data_fees_separate=None, payout_split=0.90, payout_minimum=500.0,
            payout_frequency="daily_after_buffer", buffer_50k=2100.0,
            source=SourceRef(
                url="https://myfundedfutures.com/plans/rapid",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
    ),

    "tradeday": PropFirm(
        firm_id="tradeday", name="TradeDay",
        drawdown=DrawdownRule(
            mechanism="eod_closed_balance",  # Fast Pass; Quick Pay evaluacion EOD
                                              # pero Quick Pay FONDEADA es intraday
            amount_by_size=None,  # tabla completa NO VERIFICABLE por fetch directo
            locks_at_balance_plus=None,
            source=SourceRef(
                url="https://www.tradeday.com/terms-and-conditions",
                captured="2026-09-01", confidence="fetch",
                quote="EOD Trailing Drawdown limits: You must not exceed the "
                      "maximum amount we set for you to lose during the evaluation.",
            ),
        ),
        daily_loss_limit=DailyLossLimitRule(
            exists=False, on_floating_equity=None, amount_by_size=None,
            breaks_account=False,
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        consistency=ConsistencyRule(
            percent=30.0,  # Quick Pay; Fast Pass = 45.0
            applies_to="evaluation",
            source=SourceRef(
                url="https://tradeday.freshdesk.com/en/support/solutions/articles/103000008847",
                captured="2026-09-01", confidence="fetch",
                quote="Quick Pay: No day greater than 30% of your total "
                      "profits. Fast Pass: No day greater than 45%.",
            ),
        ),
        min_trading_days=5,  # Quick Pay; Fast Pass = 3
        min_trading_days_source=SourceRef(
            url="https://tradeday.freshdesk.com/en/support/solutions/articles/103000008847",
            captured="2026-09-01", confidence="fetch",
        ),
        max_contracts_by_size=None,  # NO VERIFICABLE con tabla oficial fetcheada
        flat_time_ct="closed_10min_before_session_end",
        flat_time_source=SourceRef(
            url="https://www.tradeday.com/terms-and-conditions",
            captured="2026-09-01", confidence="fetch",
            quote="Day-trading only and all positions must be closed at least "
                  "10 minutes prior to the end of any session.",
        ),
        news_policy=None,
        automation=AutomationPolicy(
            algo_allowed_as_origin=True,  # solo via plataformas soportadas
            copy_trading_own_accounts=None,  # zona gris, riesgo de falso
                                               # positivo con deteccion multi-user
            vps_allowed=False, vpn_allowed=False, hft_prohibited=True,
            disqualifiers_quote="TradeDay does not allow the use of virtual "
                                 "private servers (VPS)",
            source=SourceRef(
                url="https://tradeday.freshdesk.com/en/support/solutions/articles/103000295384",
                captured="2026-09-01", confidence="fetch",
            ),
        ),
        economics=Economics(
            eval_price_50k=None, activation_fee=0.0, reset_cost=None,
            data_fees_separate=None, payout_split=0.80, payout_minimum=None,
            payout_frequency=None, buffer_50k=None,
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
    ),

    "take_profit_trader": PropFirm(
        firm_id="take_profit_trader", name="Take Profit Trader",
        drawdown=DrawdownRule(
            mechanism="eod_closed_balance",  # Test; PRO cambia a intraday_floating_equity
            amount_by_size=None,
            locks_at_balance_plus=None,
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        daily_loss_limit=DailyLossLimitRule(
            exists=None, on_floating_equity=None, amount_by_size=None,
            breaks_account=None,
            source=SourceRef(url="", captured="2026-09-01", confidence="unverified"),
        ),
        consistency=ConsistencyRule(
            percent=50.0, applies_to="evaluation",
            source=SourceRef(
                url="https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15170316538013-Rule-5-Be-Consistent",
                captured="2026-09-01", confidence="fetch",  # via r.jina.ai
                quote="no single trading day may exceed 50% of your total net profits",
            ),
        ),
        min_trading_days=3,
        min_trading_days_source=SourceRef(
            url="https://takeprofittrader.com/blog/3-day-evals",
            captured="2026-09-01", confidence="ws_official",
        ),
        max_contracts_by_size=None, flat_time_ct=None, news_policy=None,
        automation=AutomationPolicy(
            algo_allowed_as_origin=False, copy_trading_own_accounts=True,
            vps_allowed=None, vpn_allowed=None, hft_prohibited=None,
            disqualifiers_quote="Expert Advisors (EAs) are prohibited... "
                                 "mass-distributed commercial bots, paid-signal-"
                                 "service EAs, and group-shared algorithms are "
                                 "prohibited.",
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        economics=Economics(
            eval_price_50k=170.0, activation_fee=None, reset_cost=None,
            data_fees_separate=True,  # $4.50/contrato futuro, $1.50/micro
            payout_split=0.90, payout_minimum=None, payout_frequency=None,
            buffer_50k=None,
            source=SourceRef(
                url="https://takeprofittraderhelp.zendesk.com/hc/en-us/articles/15172548967069",
                captured="2026-09-01", confidence="ws_official",
            ),
        ),
    ),

    "tradeify": PropFirm(
        firm_id="tradeify", name="Tradeify",
        drawdown=DrawdownRule(
            mechanism="eod_closed_balance",  # suelo sube al cierre, se vigila
                                              # en tiempo real la sesion siguiente
            amount_by_size={"25000": 1000, "50000": 2000, "100000": 3500, "150000": 5000},
            locks_at_balance_plus=100,
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        daily_loss_limit=DailyLossLimitRule(
            exists=True,  # en Growth/Lightning/Select-Daily; Select Flex = False
            on_floating_equity=None, amount_by_size=None, breaks_account=False,
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        consistency=ConsistencyRule(
            percent=40.0, applies_to="both",
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        min_trading_days=None, max_contracts_by_size=None,
        flat_time_ct=None, news_policy=None,
        automation=AutomationPolicy(
            algo_allowed_as_origin=True, copy_trading_own_accounts=True,
            vps_allowed=None,  # prohibido solo en login; zona gris despues
            vpn_allowed=False, hft_prohibited=True,
            disqualifiers_quote="you must be the sole owner and developer of "
                                 "your bot... copy trading services that mirror "
                                 "another trader's actions are prohibited",
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
        economics=Economics(
            eval_price_50k=139.0,  # Growth, precio regular no-promo
            activation_fee=0.0, reset_cost=95.0, data_fees_separate=False,
            payout_split=0.90, payout_minimum=None, payout_frequency=None,
            buffer_50k=None,
            source=SourceRef(url="", captured="2026-09-01", confidence="ws_official"),
        ),
    ),
}
```

---

## 8. LO QUE NO PUDE VERIFICAR (sección honesta)

- **Todo el dominio `apextraderfunding.com` y `support.apextraderfunding.com`** estuvo bloqueado (403 Cloudflare) en fetch directo durante toda la sesión, en decenas de intentos con URLs distintas. Solo una página se pudo leer completa vía proxy `r.jina.ai` (Prohibited Activities). **No pude confirmar con fuente primaria propia**: importes exactos de drawdown/DLL por tamaño de cuenta 2026, precio de evaluación 2026, contratos máximos por tamaño, flat time, ni la nomenclatura exacta de sus productos post-marzo-2026.
- **`help.tradeify.co` y `bulenox.com` / `bulenox.help`** bloquearon el fetch directo en todos los intentos, y el proxy `r.jina.ai` tampoco funcionó para ellos (también devolvió el 403/JS-challenge). Todo lo que aparece sobre Tradeify y Bulenox en este informe es `[WS-OFICIAL]` (snippet de búsqueda que cita la URL oficial) — nunca leí yo mismo el contenido completo de esas páginas.
- **Descarté Bulenox de las 6 firmas del informe principal** (aunque aparece mencionada tangencialmente) porque, tras intentarlo con varias URLs y con proxy, no conseguí una sola página oficial suya con fetch directo exitoso, y el contrato pide priorizar rigor sobre cobertura. Si se necesita a Bulenox en el catálogo, hay que resolver primero el bloqueo de acceso.
- **`takeprofittraderhelp.zendesk.com`** bloqueó el fetch directo salvo para UNA página (Rule 5, vía proxy `r.jina.ai`). El resto de reglas de Take Profit Trader (DLL exacto, contratos, flat time, ToS completo de automatización) quedan en `NO VERIFICABLE` o `[WS-OFICIAL]`.
- **Ninguna cifra de "denegaciones de payout documentadas"** pudo verificarse con fuente primaria propia para ninguna de las 6 firmas — no encontré páginas oficiales que publiquen tasas de denegación (es información que, razonablemente, las firmas no tienen incentivo a publicar).
- **El offset exacto "+ $X" al que se bloquea el trailing EOD** solo se confirmó para MFFU Rapid ($100) y de forma parcial para Apex Intraday ($100, por snippet). Para Topstep se confirmó que bloquea en balance inicial (+$0 en Combine, +$0/base en XFA), pero no en todas las firmas.
- **Flat time obligatorio** solo se confirmó por fetch directo para Topstep (3:10 PM CT) y TradeDay (10 min antes del cierre de cada sesión). Para Apex, MFFU, Take Profit Trader y Tradeify queda `NO VERIFICABLE`.
- **Estructura de datos de mercado (¿se cobran aparte?)** no se pudo confirmar con fuente oficial para ninguna de las 6 firmas salvo la mención tangencial de que Tradeify "incluye todos los fees de exchange y datos" en Growth (WS-OFICIAL, no confirmado por fetch).
- **La contradicción Apex ToS-oficial vs. discurso de reseñas 2026 sobre automatización** queda documentada pero **sin resolver** — sería necesario contactar directamente al soporte de Apex por escrito (como recomienda el propio corpus interno en su "Procedimiento antes de comprar") para saber si en la práctica se tolera un webhook de TradingView como origen de la operación, algo que el texto literal del ToS parece no permitir.
- No verifiqué precios en checkout real (el contrato prohíbe registrar cuentas), así que **todos los precios de este informe son de página pública, no de checkout final** — coincide con la advertencia que ya hacía el propio corpus interno de verificar siempre en checkout antes de pagar.

---

**Fin del informe. Fichero único entregado:** `orchestration/results/I4_prop_firms_hallazgos.md`
