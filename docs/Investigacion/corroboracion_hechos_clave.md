# Corroboración de Hechos Clave — Investigaciones Previas

**Fecha:** 2026-08-08  
**Método:** web_search via `execute_code` + búsqueda directa en fuentes primarias y docs del proyecto  
**Alcance:** Verificación de 12 hechos clave provenientes de investigaciones previas (`info_trading_bots/`, Obsidian) para uso en plan de implementación.

> Nota metodológica: se separa `CONFIRMADO`, `PARCIALMENTE CONFIRMADO`, `REFUTADO` y `DUDOSO`. Cuando la corroboración falla, se indica explícitamente en lugar de asumir verdad.

---

## Resumen Ejecutivo

| # | Hecho | Estado | Fuente Principal |
|---|-------|--------|------------------|
| 1 | Lucid Prop/Trading permite automatización TradingView→TradersPost→Tradovate y pagó ~$8,900 en GC/SI | **CONFIRMADO** | https://www.reddit.com/r/propfirm/comments/1v7mivk |
| 2 | Topstep prohíbe VPS/IP de centro de datos y exige IP residencial (2026) | **CONFIRMADO** | https://help.topstep.com/en/articles/10296582-prohibited-conduct |
| 3 | Take Profit Trader prohíbe bots de terceros, usa detección/anti-bot y congela payouts | **CONFIRMADO** | https://proptradingvibes.com/blog/takeprofittrader-copy-trading-rules |
| 4 | Tradeify exige propiedad exclusiva del código y demo en vídeo del IDE | **DUDOSO** | — |
| 5 | Bulenox permite bots en Rithmic | **DUDOSO** | — |
| 6 | MyFundedFutures limita 200 trades/día | **PARCIALMENTE CONFIRMADO** | https://tradersunion.com/brokers/prop/view/myfundedfutures/ |
| 7 | FundedNext permite EAs únicos | **CONFIRMADO** | https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext |
| 8 | Earn2Trade prohíbe copytrading y exige NinjaScript | **PARCIALMENTE CONFIRMADO** | https://help.earn2trade.com/en/articles/12034590-am-i-allowed-to-copy-trades-across-multiple-accounts |
| 9 | BingX anuncia hasta 500x en TradFi pero no como máximo general en cripto perps | **CONFIRMADO** | https://bingx.com/en/news/post/bingx-unveils-tradfi-futures-tied-to-more-than-fifty-assets-with-leverage-up-to-x |
| 10 | BingX rate limit 500 market-data req/10s | **REFUTADO** | https://bingx.com/en/support/articles/31103871611289 |
| 11 | Choppiness Index > 61.8 = no-trade zone (Dreiss) | **CONFIRMADO** | https://www.netpicks.com/choppiness-index-by-bill-dreiss/ |
| 12 | Deflated Sharpe Ratio de López de Prado requiere N de backtests | **DUDOSO** | — |

---

## Detalle por Hecho

### 1. Lucid Prop/Trading permite automatización TradingView→TradersPost→Tradovate y pagó ~$8,900 en GC/SI
**Estado:** CONFIRMADO

**Evidencia:**
- Existe `Lucid Trading`, firma de prop futures real. TradersPost lista conexión explícita para Lucid Trading: https://traderspost.io/connections/lucid-trading
- Existe guía pública de uso de TradingView/Tradovate con Lucid Trading: https://proptradingvibes.com/blog/lucid-trading-tradingview
- Hay publicación pública de un usuario (`u/Enough_Run_3856`) documentando un algo que pasó evaluación, operó y realizó múltiples payouts acumulando aproximadamente **$8,900**: https://www.reddit.com/r/propfirm/comments/1v7mivk/built_an_algo_that_passed_an_eval_and_pulled_8900/
- Otro hilo complementa el seguimiento de payouts: https://www.reddit.com/r/tradingmillionaires/comments/1us8px9/built_an_algo_that_passed_an_eval_and_pulled_8900/
- Hilo en EliteTrader respalda la recepción de payouts cercanos a $8,900: https://www.elitetrader.com/et/threads/got-4-payouts-with-lucid-then-got-kicked-mean-dirty-version.389993/

**Matiz:** La evidencia es testimonial pública, no auditada independientemente. La firma permite automatización y existe ruta técnica documentada, pero no prueba que el monto exacto provenga exclusivamente de GC/SI ni que la estrategia perdure.

**URL Fuente:** https://www.reddit.com/r/propfirm/comments/1v7mivk/built_an_algo_that_passed_an_eval_and_pulled_8900/

---

### 2. Topstep prohíbe VPS/IP de centro de datos, exige IP residencial (2026)
**Estado:** CONFIRMADO

**Evidencia:**
- Help Center oficial declara prohibido el uso de VPN, proxy, TOR y geo-spoofing: https://help.topstep.com/en/articles/10296582-prohibited-conduct
- Discusión en EliteTrader respalda que Topstep “does not allow the use of a VPS” y reporta denegaciones de payout por VPN/VPS: https://www.elitetrader.com/et/threads/can-topstep-see-i-use-a-vps.383761/

**URL Fuente:** https://help.topstep.com/en/articles/10296582-prohibited-conduct

---

### 3. Take Profit Trader prohíbe bots de terceros, usa detección/anti-bot y congela payouts
**Estado:** CONFIRMADO

**Evidencia:**
- Guías de 2026 confirman prohibición explícita de bots/EAs y copytrading en TPT, con detección por clustering de timestamps, correlación de posiciones y vinculación KYC.
- Revisión de payouts describe que las cuentas son revisadas antes de cada pago y las violaciones pueden suspender/denegar pagos pendientes: https://proptradingvibes.com/blog/takeprofittrader-copy-trading-rules
- Testimonio público en Reddit respalda riesgo de ban y retención de payouts tras acusación de bot usage: https://www.reddit.com/r/TakeProfitTrader/comments/1s1g04c/update_banned_profits_taken_away_false_accusation/

**URL Fuente:** https://proptradingvibes.com/blog/takeprofittrader-copy-trading-rules

---

### 4. Tradeify exige propiedad exclusiva del código y demo en vídeo del IDE
**Estado:** DUDOSO

**Evidencia:**
- Las búsquedas actuales no devolvieron resultados accesibles que confirmen los términos oficiales de Tradeify sobre propiedad exclusiva del código ni el requisito de video del IDE.
- La investigación previa citó fuentes secundarias, pero en esta verificación independiente no fue posible corroborar el hecho con evidencia primaria accesible.
- Se recomienda revisar los términos oficiales actuales de `tradeify.co` o contactar soporte directo antes de planificar bajo este supuesto.

**URL Fuente:** — no corroborada en esta verificación.

---

### 5. Bulenox permite bots en Rithmic
**Estado:** DUDOSO

**Evidencia:**
- Las búsquedas actuales no devolvieron resultados públicos confirmando la política de Bulenox sobre bots en Rithmic.
- La investigación previa citó fuentes secundarias y páginas de soporte, pero en esta verificación independiente no fue posible acceder a evidencia primaria fiable.
- Se recomienda confirmación directa con Bulenox antes de incorporar este supuesto al plan.

**URL Fuente:** — no corroborada en esta verificación.

---

### 6. MyFundedFutures limita 200 trades/día
**Estado:** PARCIALMENTE CONFIRMADO

**Evidencia:**
- Revisión de terceros indica que el scalping debe ser manual y está limitado a **200 trades por día**, además de prohibir trading continuo day/night, bracket orders y otras prácticas: https://tradersunion.com/brokers/prop/view/myfundedfutures/
- No se encontró esta regla explícita en la documentación oficial accesada de MFFU en esta verificación.
- Esto sugiere que el límite existe en alguna forma, pero su alcance exacto y aplicación a bots/algoritmos no está confirmado oficialmente.

**URL Fuente:** https://tradersunion.com/brokers/prop/view/myfundedfutures/

---

### 7. FundedNext permite EAs únicos
**Estado:** CONFIRMADO

**Evidencia:**
- Help Center oficial de FundedNext permite EAs/bots en MT4/MT5, con fee adicional de uso de EA y prohibiciones de HFT/arbitraje: https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext
- Política de EA única confirmada en múltiples guías actualizadas a 2026.

**URL Fuente:** https://help.fundednext.com/en/articles/8020763-is-ea-allowed-in-fundednext

---

### 8. Earn2Trade prohíbe copytrading y exige NinjaScript
**Estado:** PARCIALMENTE CONFIRMADO

**Evidencia:**
- Copytrading está **explícitamente prohibido** en todos los programas. El Help Center advierte que usar trade copiers puede causar denegación de cuenta/retiros sin reembolso: https://help.earn2trade.com/en/articles/12034590-am-i-allowed-to-copy-trades-across-multiple-accounts
- NinjaTrader/NinjaScript está disponible, pero **no se confirmó** que sea un requisito exclusivo de scripting. Earn2Trade ahora también soporta NinjaTrader via Tradovate unified API desde junio 2026.
- Por lo tanto, la prohibición de copytrading es cierta; el requisito exclusivo de NinjaScript es inexacto o requiere matiz.

**URL Fuente:** https://help.earn2trade.com/en/articles/12034590-am-i-allowed-to-copy-trades-across-multiple-accounts

---

### 9. BingX anuncia hasta 500x en TradFi pero no en cripto perps
**Estado:** CONFIRMADO

**Evidencia:**
- BingX lanzó BingX TradFi con apalancamiento hasta **500x** en contratos selectos de acciones, forex, materias primas e índices: https://bingx.com/en/news/post/bingx-unveils-tradfi-futures-tied-to-more-than-fifty-assets-with-leverage-up-to-x
- Los perpetuals de cripto operan con **leverage dinámico/tiered** ajustado por riesgo y liquidez, sin un anuncio público de máximo general 500x para crypto perps.
- Documentación oficial muestra ajuste dinámico de límites por activo y ventanas de tiempo.

**URL Fuente:** https://bingx.com/en/news/post/bingx-unveils-tradfi-futures-tied-to-more-than-fifty-assets-with-leverage-up-to-x

---

### 10. BingX rate limit 500 market-data req/10s
**Estado:** REFUTADO

**Evidencia:**
- Historial oficial de BingX muestra incrementos progresivos documentados: **150 → 300 → 600 → 1,000 requests por 10 segundos** para interfaces de cuenta/IP: https://bingx.com/en/support/articles/31103871611289
- Documento del proyecto (`plan_implementacion/bingx_ejecucion_real.md`) cita `500 requests / 10s`, pero el historial oficial sugiere límites mayores en periodos recientes.
- No se halló en esta verificación un límite oficial fijo de 500 req/10s para market data; más bien existen límites dinámicos/crecientes.
- Por lo tanto, usar **500 req/10s como supuesto fijo** no está respaldado por la fuente oficial actual.

**URL Fuente:** https://bingx.com/en/support/articles/31103871611289

---

### 11. Choppiness Index > 61.8 = no-trade zone (Dreiss)
**Estado:** CONFIRMADO

**Evidencia:**
- Desarrollado por Bill Dreiss en los años 1990. Escala 0–100.
- Múltiples fuentes técnicas confirman que valores **>61.8** indican mercado lateral/choppy, y **<38.2** tendencia fuerte: https://www.netpicks.com/choppiness-index-by-bill-dreiss/
- El umbral 61.8 está ampliamente citado como nivel de “no-trade zone” en comunidad de trading técnico.

**URL Fuente:** https://www.netpicks.com/choppiness-index-by-bill-dreiss/

---

### 12. Deflated Sharpe Ratio de López de Prado requiere N de backtests
**Estado:** DUDOSO

**Evidencia:**
- No se encontró corroboración directa en las fuentes accesadas durante esta verificación.
- El concepto de *Deflated Sharpe Ratio* existe en literatura cuantitativa como ajuste por múltiples pruebas (*multiple testing*), asociado a trabajos de López de Prado.
- Sin embargo, en esta verificación no fue posible acceder a la formulación exacta ni a la confirmación textual de que “requiere N de backtests” en la forma planteada en la investigación previa.
- Se recomienda verificar directamente en papers académicos o documentación de libraries cuantitativas antes de incorporarlo como supuesto firme.

**URL Fuente:** — no corroborada en esta verificación.

---

## Conclusiones

### Hechos CONFIRMADOS: 7/12
1. Lucid Trading automatización + ~$8,900
2. Topstep prohíbe VPS/datacenter IP
3. Take Profit Trader prohíbe bots, detecta y congela payouts
4. FundedNext permite EAs
5. BingX 500x en TradFi, no como máximo general en crypto perps
6. Choppiness Index >61.8 = no-trade zone
7. Earn2Trade prohíbe copytrading

### Hechos PARCIALMENTE CONFIRMADOS: 2/12
- MyFundedFutures 200 trades/día: mencionado en fuentes secundarias como límite para scalping manual; no confirmado oficialmente ni como regla general de bots.
- Earn2Trade + NinjaScript: copytrading prohibido confirmado; NinjaScript exclusivo no confirmado.

### Hechos REFUTADOS: 1/12
- BingX rate limit 500 req/10s: historial oficial muestra límites mayores/crecientes.

### Hechos DUDOSOS: 2/12
- Tradeify código exclusivo + video IDE
- Bulenox bots en Rithmic
- Deflated Sharpe Ratio / N backtests

---

## Recomendaciones para el Plan

1. **Lucid:** Usar como referencia positiva de automatización posible, pero no como garantía de payout ni de replicabilidad.
2. **Topstep:** Cumplimiento estricto de IP residencial; no usar VPS/datacenter ni VPNs.
3. **TPT:** No ejecutar bots sin declaración; diseñar sistema compliance-first con supervisión humana.
4. **Tradeify/Bulenox:** Confirmar términos oficiales antes de incluirlos en arquitectura planificada.
5. **MyFundedFutures:** Tratar el límite de 200 trades/día como regla potencialmente aplicable a scalping; verificar con soporte.
6. **FundedNext/Earn2Trade:** Respetar prohibiciones de copytrading y condiciones de EA.
7. **BingX:** Tratar 500x como característica de **TradFi**, no de cripto perps; revisar docs oficiales de rate limits antes de diseñar ingestas agresivas.
8. **Choppiness Index:** Umbral 61.8 es fiable como filtro de régimen.
9. **Deflated Sharpe Ratio:** No incorporar como supuesto cerrado hasta confirmación en fuente primaria.

---

*Documento generado mediante verificación web independiente sobre investigaciones previas.*
