> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: sub-nota antigua de fondeo; el corpus de negocio vigente es docs/tradesfera/ y docs/Fondeo/. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

---
tipo: sub-nota
proyecto: 01 Ultrarentable
ficha_maestra: "[[Ultrarentable]]"
subtema: prop-firms
categoria: trading
estado: activo
vigencia: actual
estado_conocimiento: investigacion_pendiente_de_actualizacion
ultima_revision_documental: 2026-08-02
fecha_creacion: 2026-08-03
tags:
  - ultrarentable
  - prop-firms
  - fondeo
  - topstep
  - myfundedfutures
  - tradeify
  - apex
  - tradovate
---

# 🏦 Motor de Fondeo y Prop Firms — Ultrarentable V2

> El Motor de Fondeo evalúa automáticamente si una estrategia descubierta por StrategyQuant X califica matemáticamente para pasar las pruebas de empresas prop sin violar sus reglas.

> [!WARNING]
> La función descrita es el objetivo del módulo, no una capacidad certificada. Precios, promociones y reglas pueden haber cambiado y deberán comprobarse en fuentes oficiales antes de elegir la cuenta del MVP. Ver [[Estado verificado de Ultrarentable]].

---

## 🎯 Navegación y Enlaces Bidireccionales
- 📌 **Ficha Maestra:** [[Ultrarentable]]
- 🔗 **Sub-notas Relacionadas:** [[Plan 10 Fases]] | [[Motor StrategyQuant X]] | [[Dashboard Web]]

---

## 🏆 1. Clasificación Completa de Empresas Prop (Fotografía 2026)

### Nivel 1 — Proveedores Recomendados (Máxima Fiabilidad)

| Firma | Puntuación | Razón Principal | Condición Bots |
|---|:---:|---|---|
| **My Funded Futures (MFFU)** | **88 / 100 (A)** | Sin cuota de activación en Rapid. Pagos rápidos. | ✅ Permitidos EAs/bots propios. Prohíbe HFT. |
| **Topstep** | **85 / 100 (A)** | Marca histórica. API oficial ProjectX / TopstepX ($29/mes). | ✅ Permitidos bots. **Prohíbe VPS/remoto** (debe correr en PC local). |
| **OneUp Trader** | **80 / 100 (A-)** | Sin sorpresas de costes. Trayectoria muy larga. | ✅ Permitidos bots propios. |

### Nivel 2 — Proveedores Utiles con Condiciones

| Firma | Puntuación | Condición Crítica |
|---|:---:|---|
| **Apex Trader Funding** | **78 / 100 (B+)** | **PROHÍBE ESTRICTAMENTE BOTS/ALGORITMOS**. Solo se admite el copiador si la orden original se introduce **manualmente** por el titular en la cuenta maestra. |
| **Tradeify** | **78 / 100 (B+)** | Muy económico (código `TNT` 40% descuento). Sin cuota de activación en Growth/Select. |
| **FundedNext Futures** | **72 / 100 (B)** | Permite bots y copiadores entre cuentas propias. |
| **Bulenox** | **76 / 100 (B+)** | Muy barato de entrada, pero cobra **$148 de cuota de activación**. |
| **Take Profit Trader** | **74 / 100 (B)** | Prohíbe automatizaciones completas por bot. |

---

## 📊 2. Comparativa de Costes de Cuentas 50K (Precios Reales 2026)

```text
Métrica Real: Retiros Netos = Retiros Brutos - (Coste Examen + Activación + Mantenimiento + Datos + Reinicios)
```

| Firma / Plan | Precio Base 50K | Promo Conocida | Activación | Coste Real Aprobación 1er Mes |
|---|---:|---:|---:|---:|
| **MFFU Rapid 50K** | $79 / mes | 50% (código `300K`) | **$0** | **~$39.50** |
| **Tradeify Growth 50K** | $97 | 40% (código `TNT`) | **$0** | **~$58.20** |
| **TradeDay 50K Intraday** | $131 base / $59 oferta | 55% ya aplicado | **$0** | **$59.00** |
| **Topstep Standard 50K** | $49 / mes | — | $149 | **$198.00** |
| **Topstep Sin Activación** | $95 / mes | — | **$0** | **$95.00** |
| **Bulenox 50K** | $175 / mes | 89% (código `GUIDE`) | **$148** | **~$167.25** |
| **OneUp Trader 50K** | $75 / mes | — | $75 | **$150.00** |

---

## 🚀 3. Arquitectura del MVP de 1 Cuenta

El motor no arranca con 20 cuentas a la vez. Su ciclo de vida para 1 cuenta es:

```text
Estrategia SQX → Validador Independiente → Simulación Virtual → Paper Trading → Shadow Mode → 1 Cuenta Live (Tradovate / NinjaTrader)
```

- **Gateway de Ejecución:** El conector de órdenes cuenta con **Kill Switches estrictos**:
  - Parada automática al **80% del Drawdown Máximo diario permitido** (nunca apura al 100%).
  - Bloqueo de martingalas y grids recuperadores.
- **Plataformas objetivo futuras:** Tradovate, Tradezilla, NinjaTrader, TradingView DOM.
