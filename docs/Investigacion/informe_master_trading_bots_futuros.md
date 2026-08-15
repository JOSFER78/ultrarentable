# Trading Bots en Futuros y Prop Firms — Evidencia, Arquitectura y Compliance

**Fecha:** 8 de agosto de 2026  
**Objetivo:** consolidar las investigaciones sobre bots automatizados en futures prop firms, priorizando evidencia pública de uso real, payouts, infraestructura y restricciones.

> **Advertencia:** las políticas de las prop firms cambian. Las reglas concretas deben verificarse en los Términos oficiales justo antes de conectar un bot. Un testimonio, captura o página de terceros no sustituye las reglas oficiales.

---

# 1. Cómo medir la evidencia

Se separan cinco cosas que a menudo se mezclan:

1. **La prop permite bots.**
2. **Existe infraestructura técnica para automatizarla.**
3. **Una persona afirma utilizar un bot.**
4. **Existe evidencia de payout.**
5. **El payout está razonablemente vinculado al bot y existe continuidad temporal.**

### Escala práctica

- **A:** bot + cuenta + historial + payout + seguimiento.
- **B:** bot + múltiples payouts documentados.
- **C:** bot/cuenta demostrados, sin payout suficientemente verificable.
- **D:** testimonio o captura aislada.
- **E:** afirmación de la empresa.
- **F:** marketing/backtest sin evidencia independiente.

No existe aquí una “certificación” universal.

---

# 2. Mejor caso encontrado: u/Enough_Run_3856 + Lucid

## Qué afirma el autor

Un desarrollador publicó en 2026 que su algoritmo propio:

- pasó una evaluación;
- operaba Gold y Silver futures;
- estaba prácticamente automatizado;
- utilizaba una arquitectura basada en TradingView/Pine Script y TradersPost;
- consiguió varios payouts;
- alcanzó aproximadamente **8.900 USD acumulados** en el periodo documentado.

## Fuentes principales

### Publicación principal
https://www.reddit.com/r/propfirm/comments/1v7mivk/built_an_algo_that_passed_an_eval_and_pulled_8900/

### Seguimiento de payouts
https://www.reddit.com/r/tradingmillionaires/comments/1us8px9/built_an_algo_that_passed_an_eval_and_pulled_8900/

### Publicación anterior
https://www.reddit.com/r/LucidProp/comments/1tsgdnr/built_an_algo_that_passed_an_eval_and_got_me/

### Detalles técnicos
https://www.reddit.com/r/propfirm/comments/1ulye62/built_an_algo_that_passed_an_eval_and_pulled_5900/

## Valoración

**9/10 como evidencia pública**, pero no auditada independientemente.

Lo que le da fuerza:

- continuidad temporal;
- varias publicaciones;
- múltiples payouts;
- explicación técnica;
- reconocimiento de problemas y ajustes;
- conexión concreta entre bot y cuenta.

No demuestra que la estrategia vaya a seguir funcionando indefinidamente.

---

# 3. Thraxx — bot y evaluación de 100K

Thraxx publicó:

**“Idea to Funded: Prop-Firm Bot Passed Topstep's $100K Combine in 5 Days”**

Fuente:
https://www.youtube.com/watch?v=JVvr45ThYbM

También documentó posteriormente el comportamiento del bot:

https://www.youtube.com/watch?v=FPe3bPVX0aA

## Valoración

**7/10.**

Es valioso porque documenta el proceso y también muestra dificultades posteriores. La evidencia de payouts continuados es menor que en el caso Lucid.

---

# 4. Caso: 12 evaluaciones / 5 funded / 1 payout

Conversación:

https://www.reddit.com/r/algotrading/comments/1t86ibb/automating_prop_firms/

El autor describe aproximadamente:

- 12 evaluaciones;
- 5 cuentas funded;
- 1 payout;
- estrategia de continuación;
- automatización.

## Valoración

**6/10.**

Es un testimonio interesante, pero falta suficiente información para auditar estrategia, tamaño de muestra y continuidad.

---

# 5. Take Profit Trader + bot

Vídeo:

https://www.youtube.com/watch?v=0FHNp_LI5tY

Muestra un bot orientado a superar la evaluación de Take Profit Trader.

## Valoración

**4/10 como prueba de rentabilidad.**

Es evidencia de concepto/infraestructura, no de una cadena prolongada de payouts.

---

# 6. Tradeify

La investigación encontró documentación de automatización y middleware para Tradeify.

Fuente oficial investigada:
https://tradeify.co/post/futures-prop-trading-platforms-tradeify

Integración TradersPost:
https://traderspost.io/connections/tradeify

## Lo que sí demuestra

Que existe una vía técnica para automatizar.

## Lo que no demuestra

Que una estrategia concreta sea rentable o que cualquier bot sea aceptado.

**Infraestructura: alta evidencia.**

---

# 7. Bulenox

Infraestructura investigada:

```text
TradingView
    ↓
PickMyTrade
    ↓
Rithmic
    ↓
Bulenox
```

Fuentes:

https://pickmytrade.trade/prop-firm-faq/bulenox-faq/

https://bulenox.com/help/funded-account/

## Valoración

La automatización es técnicamente demostrable.

La rentabilidad de una estrategia concreta mediante bot no quedó suficientemente demostrada.

---

# 8. MyFundedFutures

Fuentes:

https://pickmytrade.trade/prop-firm-faq/myfundedfutures-faq/

https://smartpropfirm.com/firms/myfundedfutures/reviews

Hay:

- infraestructura de automatización;
- evidencia de payouts de traders;
- conexiones middleware.

Pero no debe afirmarse automáticamente:

> “ese payout fue generado por un bot”.

## Valoración

- automatización: alta;
- payouts de la firma: alta;
- payout específicamente atribuible a un bot: insuficiente.

---

# 9. FundedNext Futures

Fuentes:

https://fundednext.com/es/blog/what-is-fundednext

https://helpfutures.fundednext.com/en/articles/14274752-does-fundednext-futures-offer-any-certificates

Existe infraestructura y documentación de payouts/live payout certificates.

La evidencia específica de **bot + payout** es inferior.

---

# 10. Earn2Trade, Alpha Futures y TradeDay

La investigación paralela encontró estas firmas como candidatas relevantes para automatización/API/webhooks.

Sin embargo, no deben colocarse en la categoría de “caso probado de bot + payout” sin una fuente primaria que conecte explícitamente:

**bot → cuenta → resultado → payout.**

Son objetivos prioritarios para una siguiente ronda de verificación.

---

# 11. Arquitectura técnica realista

La ruta general investigada es:

```text
TRADINGVIEW / STRATEGY ENGINE
             ↓
          WEBHOOK
             ↓
       MIDDLEWARE
   ┌─────────┴─────────┐
   ↓                   ↓
TRADOVATE            RITHMIC
   ↓                   ↓
PROP / BROKER        PROP / BROKER
```

Herramientas estudiadas:

- TradingView Webhooks;
- TradersPost;
- PickMyTrade;
- Tradovate API;
- Rithmic.

La compatibilidad exacta depende de la firma y del backend.

---

# 12. Ejecución: separar señal, riesgo y órdenes

Arquitectura recomendada:

```text
STRATEGY
   ↓
SIGNAL
   ↓
PROP-FIRM CONSTRAINT ENGINE
   ↓
RISK ENGINE
   ↓
EXECUTION ENGINE
   ↓
BROKER / PROP
   ↓
STATE RECONCILIATION
```

La señal nunca debería enviar una orden directamente sin pasar por el motor de restricciones.

---

# 13. Prop-Firm Constraint Engine

El motor debe conocer las reglas de la cuenta concreta.

## Controles esenciales

### Daily Loss Limit

No permitir que la exposición prevista pueda superar el límite diario.

### Trailing Drawdown / High Water Mark

Mantener una representación interna del máximo permitido y actualizarla correctamente.

### Position Size

No superar:

- contratos máximos;
- riesgo por operación;
- riesgo total.

### Session Rules

Controlar:

- horarios;
- cierre de sesión;
- posiciones overnight;
- instrumentos autorizados.

### News Rules

Si la firma restringe determinadas operaciones alrededor de noticias, el motor debe bloquearlas.

### Consistency / Payout Rules

Si existe una regla de consistencia, calcularla explícitamente y no dejarla a la interpretación del usuario.

### Kill Switch

Ante una condición crítica:

```text
STOP NEW ENTRIES
        ↓
MANAGE / FLATTEN IF REQUIRED
        ↓
LOCK TRADING
```

---

# 14. Estado y reconciliación

Un bot real debe mantener una máquina de estados:

```text
FLAT
 ↓
ENTRY_PENDING
 ↓
PARTIALLY_FILLED
 ↓
OPEN
 ↓
EXIT_PENDING
 ↓
FLAT
```

Después de cada reconexión debe comparar:

**estado local vs. estado del broker/prop**

para detectar:

- órdenes huérfanas;
- posiciones duplicadas;
- fills no registrados;
- stops inexistentes.

---

# 15. OCO server-side

Cuando la API lo permita, los brackets OCO gestionados por el servidor pueden reducir dependencia del cliente.

```text
ENTRY
  ↓
STOP + TARGET
  ↓
uno ejecutado → cancelar el otro
```

No obstante, debe verificarse el comportamiento concreto de cada broker/API.

---

# 16. Fallos que deben probarse antes de live

## Webhook perdido

La señal llega tarde o no llega.

## WebSocket desconectado

El bot debe reconectar y reconciliar estado.

## Token/API expirado

No debe quedarse intentando órdenes indefinidamente.

## Partial fill

El tamaño real puede no coincidir con el solicitado.

## Slippage

Especialmente relevante en noticias y mercados rápidos.

## Duplicación

Una reconexión nunca debe convertir una única señal en dos entradas.

## Stop ausente

Debe existir un mecanismo para detectar inmediatamente una posición sin protección cuando las reglas lo exijan.

---

# 17. Qué NO debemos hacer con el “anti-ban”

La investigación paralela contiene propuestas de:

- jitter artificial;
- modificación deliberada de parámetros;
- cambios de timing;
- técnicas para evitar fingerprinting;
- simulación de comportamiento humano.

Estas ideas **no deben utilizarse para ocultar automatización o eludir sistemas de detección de una prop firm**.

La arquitectura correcta es:

> **Compliance-first, no anti-detection.**

Si una firma exige declarar el bot, se declara.

Si prohíbe una modalidad de automatización, no se intenta disfrazarla.

Si una firma permite bots bajo determinadas condiciones, el sistema se diseña para cumplirlas de forma verificable.

---

# 18. Riesgos de ejecución que sí deben evitarse

### HFT / latency arbitrage

No debe confundirse una estrategia algorítmica normal con explotación de latencia.

### Order spam

Evitar enviar/modificar órdenes de forma innecesaria.

### Quote stuffing

Evitar una arquitectura que produzca grandes cantidades de cancelaciones/modificaciones sin necesidad operativa.

### Scalping extremadamente corto

Si la firma limita determinadas formas de scalping, el bot debe incorporar esa regla.

### Copy trading no permitido

No replicar órdenes entre cuentas ajenas o utilizar señales de terceros cuando esté prohibido.

---

# 19. Evidencia negativa

La investigación encontró también casos que muestran por qué el cumplimiento es tan importante.

## Take Profit Trader

Un usuario afirma que perdió aproximadamente 30.000 USD en payouts tras ser acusado de utilizar un bot:

https://www.reddit.com/r/TakeProfitTrader/comments/1s1g04c/update_banned_profits_taken_away_false_accusation/

Esto es un **testimonio**, no una sentencia ni una prueba independiente de que la acusación fuera correcta.

El valor de este caso es mostrar el riesgo:

> ganar dinero con un bot no garantiza que el resultado sea finalmente aceptado y pagado.

---

# 20. Qué hace creíble un caso

Un caso debería subir de categoría cuando encontramos:

### Nivel 1
La persona dice que utiliza un bot.

### Nivel 2
Se ve el bot y la cuenta.

### Nivel 3
Se observa la evaluación.

### Nivel 4
Se observa cuenta funded.

### Nivel 5
Existe payout.

### Nivel 6
Hay varios payouts.

### Nivel 7
Existe seguimiento longitudinal.

### Nivel 8
Hay datos técnicos suficientes para reconstruir la arquitectura.

Cuantos más niveles estén presentes, más interesante es el caso.

---

# 21. Ranking consolidado

| Caso | Prop | Evidencia principal | Valoración |
|---|---|---|---:|
| u/Enough_Run_3856 | Lucid | múltiples payouts + seguimiento + arquitectura | **9/10** |
| Thraxx | Topstep | bot + evaluación + seguimiento | **7/10** |
| 12 eval / 5 funded / 1 payout | no especificada | testimonio + resultados | **6/10** |
| Take Profit Trader bot | TPT | demostración de automatización | **4/10** |
| Tradeify | Tradeify | infraestructura + reglas | infraestructura alta |
| Bulenox | Bulenox | infraestructura + integración | infraestructura alta |
| MFFU | MFFU | infraestructura + payouts no ligados al bot | evidencia parcial |
| FundedNext | FundedNext Futures | infraestructura + payout docs | evidencia parcial |

---

# 22. Lo que realmente parece funcionar como enfoque

La investigación conjunta con DaviddTech apunta a una arquitectura muy concreta:

```text
                STRATEGY FACTORY
                      ↓
              VALIDATION ENGINE
                      ↓
              REGIME DETECTOR
                      ↓
              PORTFOLIO ENGINE
                      ↓
             PROP CONSTRAINT ENGINE
                      ↓
                 RISK ENGINE
                      ↓
             EXECUTION ENGINE
                      ↓
              STATE RECONCILIATION
                      ↓
                 MONITORING
```

No es un único bot.

Es un sistema de control.

---

# 23. Arquitectura recomendada para futures prop

## Capa 1 — Research

Generar hipótesis.

## Capa 2 — Quant

Convertirlas en reglas.

## Capa 3 — Validation

IS/OOS/WFA/Monte Carlo.

## Capa 4 — Regime

Decidir cuándo tiene sentido operar.

## Capa 5 — Portfolio

Combinar estrategias.

## Capa 6 — Prop Constraint

Aplicar las reglas de la cuenta.

## Capa 7 — Risk

Controlar riesgo monetario.

## Capa 8 — Execution

Enviar órdenes.

## Capa 9 — Reconciliation

Comprobar que la realidad coincide con el estado interno.

## Capa 10 — Monitoring

Detectar anomalías y apagar el sistema si es necesario.

---

# 24. Conclusiones

1. Los casos públicos realmente fuertes son escasos.
2. El caso Lucid/u/Enough_Run_3856 es uno de los mejores encontrados.
3. Thraxx aporta una segunda referencia interesante de desarrollo público.
4. Que una prop permita automatización no demuestra rentabilidad.
5. Que exista un payout no demuestra automáticamente que proceda de un bot.
6. Un backtest no demuestra que una estrategia sobreviva live.
7. Para una prop, el drawdown y las reglas de la cuenta pueden ser tan importantes como el edge.
8. La ejecución y la reconciliación son parte del sistema de trading.
9. La arquitectura debe ser compliance-first.
10. La siguiente investigación debería ampliar la evidencia de bot+payout por cada prop, buscando fuentes primarias y seguimiento longitudinal.

---

# 25. Lista prioritaria de investigación futura

Buscar específicamente:

- Tradeify + bot + payout;
- Bulenox + bot + payout;
- MyFundedFutures + bot + payout;
- FundedNext Futures + bot + payout;
- Take Profit Trader + bot + payout;
- TradeDay + bot + payout;
- Alpha Futures + bot + payout;
- Earn2Trade + bot + payout;
- otras futures prop firms.

Para cada caso:

**bot → evaluación → funded → payout → segundo payout → continuidad → reglas oficiales.**

Ese es el estándar de evidencia que debería utilizarse antes de considerar un sistema como candidato serio.
