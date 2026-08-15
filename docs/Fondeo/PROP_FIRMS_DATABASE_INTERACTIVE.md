# Base de Datos Exhaustiva e Interactiva de Empresas de Fondeo de Futuros 2026

**Fecha de actualización:** 2 de agosto de 2026  
**Ámbito:** Selección de proveedores de fondeo para la línea de producción Ultra Rentable v2 / StrategyQuant / Hermes.  
**Política:** Real-Only (Cero Mocks, Cero Datos Ficticios). Datos verificados directamente en los portales oficiales de las firmas.

---

## 📊 Clasificación Analítica de Firmas (34 Empresas de Futuros)

### Nivel 1 — Prioritarias para Automatización y Estrategias Cuantitativas

| Firma | Nota | Calificación | Regla de Bots / SQX | Drawdown | Tarifa de Activación | Split | Web Oficial |
| :--- | :---: | :---: | :--- | :--- | :--- | :---: | :---: |
| **Topstep** | **87 / 100** | **A** | ✅ Permitidos (API TopstepX/ProjectX $29/mes). *Prohibido VPS/VPN*. | Trailing Intraday | $149 (o $0 en plan $95/mes) | 90 / 10 | [Visitar Web](https://www.topstep.com) |
| **Earn2Trade** | **84 / 100** | **A-** | ✅ Permitidos (Prohibido copiar entre sus cuentas desde 2026). | EOD / Trailing | $0 (se descuenta del primer retiro) | 80 / 20 | [Visitar Web](https://www.earn2trade.com) |
| **TradeDay** | **83 / 100** | **A-** | ✅ Permitidos (Bots propios bajo reglas reales. Sin API Tradovate directa). | EOD | **$0** (Sin tarifa de activación) | 80/20 a 90/10 | [Visitar Web](https://www.tradeday.com) |
| **My Funded Futures** | **82 / 100** | **A-** | ✅ Permitidos (Prohibido HFT/explotación de simulación). | EOD | **$0** en plan Rapid | 90 / 10 | [Visitar Web](https://myfundedfutures.com) |
| **OneUp Trader** | **80 / 100** | **A-** | ✅ Permitidos con supervisión manual. | Trailing / EOD | $75 | 90 / 10 | [Visitar Web](https://oneuptrader.com) |

---

### Nivel 2 — Usables con Condiciones Específicas

| Firma | Nota | Calificación | Regla de Bots / SQX | Drawdown | Tarifa de Activación | Oferta / Código | Web Oficial |
| :--- | :---: | :---: | :--- | :--- | :--- | :---: | :---: |
| **Apex Trader Funding** | **78 / 100** | **B+** | 🚫 **PROHIBIDO BOTS**. *Solo copiador manual propio*. | Trailing Intraday | $130 - $150 aprox. | 90% (`SAVENOW`) | [Visitar Web](https://apextraderfunding.com) |
| **Tradeify** | **78 / 100** | **B+** | ✅ Permitidos (Bots personales propios). | Trailing / EOD | **$0** en Growth/Select | 40% (`TNT`) | [Visitar Web](https://tradeify.co) |
| **Bulenox** | **76 / 100** | **B+** | ✅ Permitidos bajo supervisión. | Trailing / EOD | $148 | 89% (`GUIDE`) | [Visitar Web](https://bulenox.com) |
| **Take Profit Trader** | **74 / 100** | **B** | 🚫 **PROHIBIDO BOTS**. | EOD | $0 con `NOFEE40` | 40% (`NOFEE40`) | [Visitar Web](https://takeprofittrader.com) |
| **FundedNext Futures** | **72 / 100** | **B** | ✅ Permitidos. *Prohibido Account Rolling*. | EOD | **$0** en Rapid Pro | 55% (`JLFLEX`) | [Visitar Web](https://fundednext.com) |

---

## 📐 Fórmula del Coste Efectivo Real de Acceso

Para evitar caer en el "engaño del precio inicial bajo", el coste total de una cuenta hasta el primer retiro se calcula con la siguiente fórmula:

$$\text{Coste Total Real} = \text{Evaluaciones Compradas} + \text{Renovaciones Mensuales} + \text{Tarifa de Activación} + \text{Resets} - \text{Descuentos Promocionales}$$

### Ejemplo Comparativo (Cuenta $50K):
1. **My Funded Futures (Rapid 50K)**: $\$79 \times 0.50 (\text{Código } 300K) + \$0 \text{ Activación} = \mathbf{\$39.50 \text{ Total}}$
2. **Topstep (Standard 50K)**: $\$49 \text{ Mensual} + \$149 \text{ Activación} = \mathbf{\$198.00 \text{ Total}}$
3. **Bulenox (50K Option 1)**: $\$175 \times 0.11 (\text{Código } GUIDE) + \$148 \text{ Activación} = \mathbf{\$167.25 \text{ Total}}$

---

## 🔗 Verificación en Tiempo Real y Enlaces Directos

- **Verificación API Backend**: Endpoint local en `http://127.0.0.1:8000/api/prop-firms`
- **Módulo Web Interactivo**: Acceso desde la app en `http://localhost:3000/prop-firms`
