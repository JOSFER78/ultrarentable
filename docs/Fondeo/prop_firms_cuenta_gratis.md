# Prop Firms de FUTUROS con CUENTA GRATUITA DE PRUEBA (free trial) — 2026
## Informe para MVP de fondeo: ejecución automatizada + seguimiento por script/cron

> **Regla del proyecto:** no inventar métricas ni reglas. Cada dato proviene de fuente oficial **[OFICIAL]** o de sitios de revisión **[TERCERO]**. *NO CONFIRMADO* = sin fuente accesible en el momento de la investigación (2026-08-08).

---

## 1. Resumen ejecutivo

| Prop firm | Free trial | Duración | Futuros | Bots/EA | API | IP/VPS | Recomendación MVP |
|---|---|---|---|---|---|---|---|
| **FundedNext** | ✅ Free Trial Account **[OFICIAL]** | 14 días desde el 1er trade | ❌ solo CFDs (MT5/Match-Trader) | ❌ prohibido en trial | No en trial | No publicado | ⚠️ Solo para validar CFDs |
| **TradeDay** | ✅ 14-Day Free Trial **[TERCERO]** | 14 días | ✅ | ❌ NO CONFIRMADO | ❌ NO CONFIRMADO | ❌ NO CONFIRMADO | ⚠️ Candidato condicional |
| **Apex Trader Funding** | ❌ No | — | ✅ | ✅ Permitidos | Por plataforma (NT8/Rithmic/Tradovate/TV) | No publicado | ✅ Mejor para bots (pagando) |
| **Topstep** | ❌ No (Practice 150K solo con subscripción) | — | ✅ | ✅ Permitidos con condiciones | ❌ No API pública | VPN/proxy prohibido | ❌ Sin trial |
| **MyFundedFutures** | ❌ No | — | ✅ | ✅ [TERCER] | No publicado | No publicado | ❌ Sin trial |
| **Bulenox** | ✅ Mencionado: “Rithmic 14 Day Free Trial” **[TERCERO]** + texto en su web | 14 días | ✅ | ❌ NO CONFIRMADO | ❌ NO CONFIRMADO | No publicado | ⚠️ Validar con soporte |
| **Tradeify** | ❌ No find | — | ✅ | NO CONFIRMADO | NO CONFIRMADO | NO CONFIRMADO | ❌ |
| **Take Profit Trader** | ❌ No | — | ✅ | NO CONFIRMADO | NO CONFIRMADO | NO CONFIRMADO | ❌ |
| **Earn2Trade** | ❌ No | — | ✅ | NO CONFIRMADO | NO CONFIRMADO | NO CONFIRMADO | ❌ |
| **Lucid Trading** | ❌ No trial oficial (solo paper) | — | ✅ | ✅ [TERCERO] | NO CONFIRMADO | NO CONFIRMADO | ❌ |

### Conclusión para el MVP

**Ninguna prop firm de futuros combina en 2026: free trial + futuros + bots/API autorizados + seguimiento automatizable por cron** (verificado). La mejor ruta de menor riesgo inicial:

1. **Fase 0 (coste $0):** paper/demo en NinjaTrader / Rithmic / Tradovate para desarrollar y validar tu bot contra datos de mercado reales.
2. **Si quieres trial de FUTUROS** → la única encontrada es **TradeDay (14 días)**; contactar a soporte ANTES de automatizar para confirmar política de bots/API/VPS.
3. **Si quieres trial con reglas exactas publicadas** → **FundedNext Free Trial** (reglas 100% documentadas, pero CFDs y sin EA).
4. **Fase 1 (pago, automatización real):** una evaluación que permita bots con reglas públicas: **FundedNext Futures Rapid/Flex (~$70–$250 one-time)** o **Apex Trader Funding** (bots permitidos).

---

## 2. Detalle por firma

### 2.1 FundedNext — Free Trial Account **[OFICIAL]**
**Fuente:** https://help.fundednext.com/en/articles/8902893-fundednext-free-trial-rules (actualizado 2026)

- **Duración:** 14 días desde la fecha del primer trade; al vencer se desactiva automáticamente.
- **Proceso:** 1-step.
- **Profit target:** 5% del balance inicial.
- **Daily loss limit:** 5% (se resetea a medianoche hora del server).
- **Max loss:** 10%.
- **Mínimo de días de trading:** 3 dentro de los 14 días.
- **Nº cuentas:** una activa por email+IP; al deshabilitarse se puede pedir otra (trials ilimitados).
- **Reset:** no disponible.
- **Posiciones abiertas:** máx. 30.
- **EA/bots:** ❌ **no permitidos** en el trial (bloqueo de nuevas órdenes).
- **Leverage:** 1:100 forex, 1:40 commodities, 1:20 indices.
- **Plataforma:** **MT5** (Match-Trader para clientes de EE.UU.).
- **Mercado:** **CFD** — no es futuros.
- **Recompensa:** al llegar al 5% → cupón 5% dto. en planes CFD (14 días, nuevos usuarios).

**Planes de FUTUROS (pago, 2026) [OFICIAL** — https://fundednext.com/general-rules/futures/trading-objectives]:
| Plan | Profit target 25/50/100K | Max loss | Daily loss | Consistency | Split |
|---|---|---|---|---|---|
| Rapid Pro | $1,500/$3,000/$5,000 | $1,000/$2,000/$2,500 | Ninguno | Ninguna | 90% |
| Rapid Daily | $1,500/$3,000/$5,000 | $1,000/$2,000/$2,500 | $500/$1,000/$1,250 | Ninguna | 90% |
| Flex | $2,500/$5,000/$8,000 (50/100/150K) | $1,500/$2,500/$4,000 | Ninguno | 40% | 95% |

- MLL = trailing sobre balance pico EOD; se endurece al llegar al balance inicial.
- **Bots/EAs:** permitidos explícitamente en challenge/funded de futures.
- **Precio (promos 2026):** desde ~$70 hasta ~$500 one-time **[TERCERO]**.
- **Seguimiento:** dashboard web propio.

### 2.2 TradeDay — 14-Day Free Trial **[TERCERO]**
**Fuentes:** https://propfirmplus.com/tradeday-14-day-free-trial/ · https://propfirmdeck.com/futures/prop-firms/tradeday · https://www.tradeday.com/

- **Trial:** 14 días; acceso similar al de un miembro, **sin evaluación para cuenta funded** (no hay meta de profit).
- **Futuros:** sí, 100% futures.
- **Reglas detalladas del trial:** no publicadas oficialmente → confirmar con soporte.
- **Bots/API/VPS en el trial:** NO CONFIRMADO → **contactar soporte antes de automatizar**.
- **Planes de pago (2026)**: Quick Pay 50K $125/mo (~$62 con 50%), DD $2K intraday o EOD trailing, 30% consistencia solo en eval, min 5 días, 80% split, $0 activación, reset $60; 100K $230 (~$115), DD $3K; 150K $350 (~$175), DD $4.5K. Fast Pass sin mín de días (45% consistencia).

### 2.3 Apex Trader Funding
**Fuentes:** https://traderpayout.com/apex/apex-trader-funding-free-trial · https://apextraderfunding.com/ · https://www.quantvps.com/blog/apex-trader-funding-automated-trading-bots

- **Free trial:** ❌ **No existe** free trial/demo/eval gratuita.
- **Futuros:** sí, one-step evaluation.
- **Bots/automatización:** ✅ permitidos (integración con NT8, Rithmic, TradingView).
- **Plataformas:** NinjaTrader 8, Rithmic, Tradovate, TradingView.
- **Seguimiento:** dashboard propio.
- **IP/VPS:** no publicado oficialmente.
- **Coste:** evaluación one-time (con descuentos frecuentes ~$20–$150) **[TERCERO]**.

### 2.4 Topstep **[OFICIAL]**
**Fuentes:** https://help.topstep.com/en/articles/8284134-practice-account · https://help.topstep.com/en/articles/8284197-account-combine-parameters · https://www.topstep.com/

- **Free trial:** ❌ no hay; Practice Account 150K solo con subscripción Combine activa.
- **Combine (50/100/150K):** target $3K/$6K/$9K; MLL $2K/$3K/$4.5K trailing EOD; DLL opcional $1K/$2K/$3K; consistencia 50%; mínimo 2 días.
- **XFA:** split 90/10 desde el primer dólar; cambios de payout paths en 2026.
- **Bots:** permitidos con condiciones (prohibido scalping algorítmico que explote fills SIM, órdenes masivas de alta velocidad, AI/ultra-high speed, account stacking).
- **IP/VPS:** VPN/proxy/TOR prohibido explícitamente (error 403); requiere dirección residencial real.
- **API:** no hay REST pública para ejecución externa (se opera vía TopstepX).

### 2.5 MyFundedFutures (MFFU)
**Fuentes:** https://myfundedfutures.com/plans · https://myfundedfutures.com/terms · https://algofunded.com/firms/myfundedfutures/ · https://www.roboquant.dev/blog/my-funded-futures-automation-guide

- **Free trial:** ❌ no.
- **Planes (2026):** Rapid EOD 50K $126 one-time; Builder 25K/50K $63/mo; Pro 100K ~$114/mo. Rapid: eval 2 días, target $3K, DD $2K EOD, 90/10, payout diario. Builder: 1 día, 80/20, payout 48h. Pro: 2 días, 80/20, bi-weekly.
- **Bots:** permitidos en plan de pago **[TERCERO]**.
- **Plataformas:** TradingView, NinjaTrader, Quantower, Tradovate, Fintevo.

### 2.6 Bulenox
**Fuentes:** https://bulenox.com/member/signup · https://test-max.com/prop-firms/bulenox/ · https://propjournal.net/prop-firms/bulenox/rules

- **Free trial:** su web menciona posibilidad de free trial/sample (texto genérico en signup); **[TERCERO]** reporta "Rithmic 14 Day Free Trial". Reglas del trial NO documentadas.
- **Planes (2026) [TERCERO]:** 25K target $1,500/DD $1,500; 50K $3,000/$2,500; 100K $6,000/$3,000; 150K $9,000/$4,500; 250K $15,000/$5,500. Suscripción mensual $145/$125/$155/$325/$535 (con cupones).
- **Bots/API:** NO CONFIRMADO.

### 2.7 Tradeify
**Fuentes:** https://tradeify.co/ · https://tradeify.app/refunds-and-cancellations · https://quantcrawler.com/learn/tradeify-review

- **Free trial:** NO para cuentas funded (el "30-day free trial" citado es de la app, no del prop account).
- **Planes (2026):** Growth, Select (sin daily loss limit), Lightning (instant funded). EOD trailing DD; split 90–100%; compra única.

### 2.8 Take Profit Trader
**Fuentes:** https://takeprofittrader.com/ · https://tradingtoolshub.com/blog/takeprofittrader-pricing-guide-2026/

- **Free trial:** ❌ no.
- **Modelo:** Test account ~$75–$360 one-time **[TERCERO]** → 5 días de trading → PRO (day-one payouts, 80/20; PRO+ EOD, 90/10).
- **Plataformas:** NinjaTrader, TradingView, Tradovate, Rithmic, Quantower, MotiveWave, RTrader.

### 2.9 Earn2Trade
**Fuentes:** https://earn2trade.com/gauntlet-mini · https://earn2trade.com/

- **Free trial:** ❌ no.
- **Gauntlet Mini (50K):** target $3,000; EOD DD $2,000; DLL $1,100; consistencia 30%; hasta 4 días; 6 contratos; live trailing $2,000; split 80% s/$2,250 **[TERCERO]**.

### 2.10 Lucid Trading
**Fuentes:** https://lucidtrading.com/ · https://quantcrawler.com/learn/lucid-trading-review

- **Free trial:** ❌ no oficial; solo paper trading dentro de la plataforma **[TERCERO]**.
- **Bots:** automation permitido **[TERCERO]**.

---

## 3. Evaluación para el MVP

| Criterio del MVP | Peso | Firma que mejor lo cumple |
|---|---|---|
| (a) Ejecución automatizada real con API/bots | 1 | **Apex** (Bots confirmados, plataformas API-ready) / **FundedNext Futures** (bots [OFICIAL]) |
| (b) Seguimiento automatizable por script/cron | 2 | **FundedNext** (dashboard + reglas públicas) / **Apex** (dashboard propio); en ambos se lecta el dashboard vía HTTP |
| (c) Bajo riesgo inicial (trial) | 3 | **TradeDay** (trial futuros 14 días) / **FundedNext** (trial CFD sin cost, reglas exactas) |

**Recomendación final (una sola firma para el MVP):**

1. **Si el trial es innegociable y debe ser FUTUROS** → **TradeDay 14-Day Trial** (única con trial de futuros). Riesgo: no confirmado bots/API/VPS → *validar con soporte* en cuanto a “¿se permite EA en el trial? ¿VPS ok?”. Si la respuesta es sí → MVP sobre esa cuenta (trial real 14 días, seguimiento manual-dashboard).
2. **Si la automatización es innegociable y pagar está bien** → **FundedNext Futures Rapid Pro** (~$150-$250 one-time): bots/EA **permitidos [OFICIAL]**, reglas públicas, 90% split, seguimiento por dashboard/CSV → ciclo completo con cron.
3. **Ruta híbrida cero-riesgo** → NinjaTrader/Rithmic paper (gratis) para el bot → TradeDay trial (si confirman bots) → FundedNext/Apex evaluación paga.

---

## 4. URLs de origen

- https://help.fundednext.com/en/articles/8902893-fundednext-free-trial-rules
- https://fundednext.com/general-rules/futures/trading-objectives
- https://propfirmplus.com/tradeday-14-day-free-trial/
- https://vettedpropfirms.com/best-futures-prop-firm-free-trial-accounts/
- https://www.tradeday.com/
- https://help.topstep.com/en/articles/8284134-practice-account
- https://help.topstep.com/en/articles/8284197-account-combine-parameters
- https://traderpayout.com/apex/apex-trader-funding-free-trial
- https://apextraderfunding.com/
- https://www.quantvps.com/blog/apex-trader-funding-automated-trading-bots
- https://algofunded.com/firms/myfundedfutures/
- https://myfundedfutures.com/terms
- https://bulenox.com/member/signup
- https://test-max.com/prop-firms/bulenox/
- https://propjournal.net/prop-firms/bulenox/rules
- https://tradeify.co/
- https://tradeify.app/refunds-and-cancellations
- https://takeprofittrader.com/
- https://earn2trade.com/gauntlet-mini
- https://lucidtrading.com/
- https://quantcrawler.com/learn/lucid-trading-review

---

## 5. Próximo paso inmediato

1. Abrir **cuenta demo** en NinjaTrader o Rithmic (gratis) y validar la lógica del bot.
2. Escribir a **TradeDay support** preguntando: «¿Se permite EA/bot automatizado durante el 14-day free trial? ¿Es posible operar desde VPS sin IP residencial?».
3. Si OK → inscribirse al trial y preparar el script de monitorización (scrape del dashboard → CSV → cron → alertas).
4. Si NO → comprar una evaluación **FundedNext Futures Rapid Pro** (bots permitidos [OFICIAL]) y montar el pipeline de seguimiento directamente sobre su dashboard.

---

*Informe generado el 2026-08-08 para el plan de implementación de Ultrarentable. Todos los enlaces citados fueron consultados online; los datos con fuente oficial están marcados [OFICIAL] y los de terceros [TERCERO].*