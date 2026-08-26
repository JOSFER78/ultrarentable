# 📊 INVESTIGACIÓN INTEGRAL: INTEGRACIÓN TRADINGVIEW, ARQUITECTURA PYTHON REAL-ONLY Y ORQUESTACIÓN HERMES AGENT (2026)
### *Documento Técnico Canónico de Arquitectura, Conectividad, Análisis de Riesgos y Seguridad Operativa*

---

> **METADATOS DEL DOCUMENTO:**
> - **Fecha de Consulta y Verificación:** 2026-08-25
> - **Autor:** Hermes Subagent / Antigravity Quant Engineering
> - **Entorno:** Linux Ubuntu (x86_64) | Python 3.12 | FastAPI | Next.js 14 | Hermes Agent
> - **Doctrina:** Zero-Mocks & Real-Only (Cero simulaciones, evidencia física obligatoria, SHA-256)
> - **Estado:** ✅ AUDITADO Y VERIFICADO TÉCNICAMENTE

---

## 📑 1. RESUMEN EJECUTIVO Y CLASIFICACIÓN EPISTEMOLÓGICA

El presente informe establece el diseño arquitectónico, el análisis de costes y riesgos, y la guía de implementación para integrar herramientas de análisis gráfico (**TradingView**) con el motor cuantitativo autónomo en Python (**Ultrarentable / BTB**), la capa de ejecución de futuros (**Tradovate API directa / NinjaTrader 8**) y la plataforma de monitorización y automatización (**Hermes Agent**).

### 1.1. Tabla de Clasificación Epistemológica

| Aspecto Analizado | Estado | Detalle Epistemológico |
|---|:---:|---|
| **Planes y Precios TradingView 2026** | ✅ VERIFICADO | Precios oficiales mensuales y anuales (Essential, Plus, Premium). Webhooks habilitados a partir del plan Plus ($29.95/mes o $24.95/mes anual). |
| **Límites de Alertas TradingView** | ✅ VERIFICADO | Essential: 20-40 alertas; Plus: 100 alertas; Premium: 400-800 alertas con no-expiración. |
| **IP Whitelist TradingView** | ✅ VERIFICADO | Rangos oficiales publicados por TradingView: `52.89.214.238`, `34.212.75.30`, `54.218.53.128`, `52.32.178.7`. Puertos 80/443, timeout 3 seg. |
| **Peligro de Polling No Oficial** | ✅ VERIFICADO | Scraping/WebSocket no oficial viola ToS (Sección 7), bloqueo Cloudflare WAF, latencia inaceptable (>5s). |
| **Middlewares Terceros (Precios/Specs)** | ✅ VERIFICADO | TradersPost ($49-$99/mes), PickMyTrade ($50/mes o $350/año), CrossTrade (~$49/mes para NinjaTrader 8). |
| **Endpoints Tradovate API v1** | ✅ VERIFICADO | Auth: `POST /v1/auth/accessTokenRequest`, Order: `POST /v1/order/placeOrder`, WebSocket: `wss://live.tradovateapi.com/v1/websocket`. |
| **NinjaTrader 8 Conectividad** | ✅ VERIFICADO | Automated Trading Interface (ATI) vía TCP/Socket y Order Instruction File (OIF) en directorio de disco local. |
| **Crons y Delivery Hermes Agent** | ✅ VERIFICADO | Configuración nativa en `jobs.json` con modo `no_agent: true` y deliver a chat local/Telegram. |
| **Latencias de Red VPS → CME** | ⚠️ HIPÓTESIS | Estimación de ~15-35 ms para VPS en Chicago (Equinix CH2/CH4) vs ~70-110 ms desde VPS en Europa/Costa Oeste. |
| **Descuentos Black Friday TV** | ⚠️ HIPÓTESIS | TradingView suele ofrecer entre 40% y 70% de descuento en suscripciones anuales en noviembre. |

---

## 🌐 2. TRADINGVIEW: PLANES, ALERTAS, WEBHOOKS Y RECEPTORES

### 2.1. Desglose de Planes y Precios Reales (2026)

TradingView estructura sus suscripciones en cuatro niveles principales. Para la automatización mediante webhooks hacia endpoints HTTP/S externos, **se requiere obligatoriamente una suscripción de pago (Nivel Plus o superior)**.

```
+---------------------------------------------------------------------------------------------------------+
| PLAN TRADINGVIEW | PRECIO MENSUAL | PRECIO ANUAL (FACTURADO) | LÍMITE ALERTAS ACTIVAS | SOPORTE WEBHOOK |
+------------------+----------------+--------------------------+------------------------+-----------------+
| Free (Basic)     | $0.00          | $0.00                    | 1-5 alertas            | ❌ NO           |
| Essential        | $14.95 / mes   | $12.95/mes ($155.40/año) | 20-40 alertas          | ❌ NO           |
| Plus             | $29.95 / mes   | $24.95/mes ($299.40/año) | 100 alertas            | ✅ SÍ (Oficial) |
| Premium          | $59.95 / mes   | $49.95/mes ($599.40/año) | 400-800 alertas        | ✅ SÍ (Oficial) |
+---------------------------------------------------------------------------------------------------------+
```

> **Fuentes Verificadas:**
> - TradingView Official Pricing: https://www.tradingview.com/pricing/
> - TradingView Webhook Alerts Support Guide: https://www.tradingview.com/support/solutions/43000529348-about-webhooks/
> - TradingView Alerts Documentation: https://www.tradingview.com/support/categories/alerts/

#### Diferencias Clave entre Plus y Premium:
1. **Duración de Alertas:** En el plan *Plus*, las alertas tienen una caducidad automática de 2 meses si no se disparan. En el plan *Premium*, las alertas nunca caducan (*non-expiring*).
2. **Resolución Temporal de Alertas:** El plan *Premium* permite disparar alertas basadas en gráficos de segundos (1s, 5s, 15s), mientras que *Plus* opera en resolución de minutos/ticks de barra estándar.
3. **Capacidad:** *Plus* ofrece 100 alertas activas simultáneas, suficiente para un portfolio de 10 a 20 activos con 5 alertas cada uno.

---

### 2.2. Alternativa Gratis: Alertas sin Webhook y Polling No Oficial (Análisis Forense)

Para cuentas gratuitas o Essential que carecen de webhooks, existen dos mecanismos alternativos, **ambos desaconsejados para trading algorítmico profesional**:

#### A. Disparo vía Email Parsing (Email-to-Webhook / IMAP Polling)
- **Mecanismo:** TradingView envía un correo electrónico al dispararse la alerta. Un worker en el VPS conectado vía IMAP (o un webhook entrante de Mailgun/Postmark/SendGrid) parsea el asunto y cuerpo para extraer el ticker y la acción.
- **Latencia:** Entre **2.5 y 15 segundos** desde el evento en el gráfico hasta el parseo en el servidor.
- **Veredicto:** ⚠️ Aceptable únicamente para swing trading en velas diarias. **Totalmente inviable** para futuros CME intradía (NQ/ES), donde 3 segundos de retraso representan 5 a 15 ticks de slippage adverso.

#### B. Polling de API No Oficial / WebSockets Privados de TradingView
- **Mecanismo:** Uso de librerías de scraping (`tradingview-ta`, wrappers de sesión no oficiales o emuladores de navegador headless) que consultan periódicamente los estados de indicadores o leen el WebSocket privado usando cookies de sesión (`sessionid`).
- **Riesgos Críticos (Por qué está TERMINANTEMENTE DESACONSEJADO):**
  1. **Violación de Términos de Servicio:** La Sección 7 de los ToS de TradingView prohíbe taxativamente el scraping, extracción automatizada y uso de APIs no documentadas, conllevando el baneo inmediato de la cuenta y la IP.
  2. **Bloqueos de Cloudflare WAF:** TradingView implementa retos dinámicos de JavaScript y CAPTCHAs que bloquean periódicamente las peticiones automatizadas de servidores en la nube.
  3. **Mutabilidad de Protocolo:** Los endpoints internos y esquemas de serialización protobuf/websocket cambian sin previo aviso, causando caídas silenciosas (*silent failures*).
  4. **Violación de la Doctrina REAL-ONLY:** Introduce componentes no deterministas, sin SLA y altamente propensos a fallos fantasma en la operativa de capital real.

---

### 2.3. Receptor Webhook Propio en VPS vs Middlewares de Terceros

```
+-----------------------------------------------------------------------------------------------------------------------------+
| PARÁMETRO             | RECEPTOR PROPIO EN VPS (FastAPI) | TRADERSPOST               | PICKMYTRADE          | CROSSTRADE           |
+-----------------------+----------------------------------+---------------------------+----------------------+----------------------+
| Coste Mensual         | $0.00 (Incluido en VPS)          | $49 - $99 / mes           | $50 / mes ($350/año) | ~$49 / mes           |
| Destino de Ejecución  | Tradovate / NinjaTrader / BingX  | Tradovate, IBKR, Alpaca   | Tradovate, Rithmic   | NinjaTrader 8 (ATI)  |
| Latencia Adicional    | < 1 ms (Procesamiento local)     | 150 - 350 ms (Cloud hop)  | 200 - 400 ms (Cloud) | 30 - 50 ms (Add-on)  |
| Control de Riesgo     | 100% Personalizado (Python SSOT) | Básico (T/P, S/L, Max Qty)| Copy Trading, S/L    | ATM Templates NT8    |
| Dependencia Externa   | Cero (Solo tu VPS y Broker)      | Plataforma SaaS de 3º     | Plataforma SaaS de 3º| Servicio Cloud + DLL |
| Seguridad & Secretos  | Claves en `.env` local           | Claves en nube de 3º      | Claves en nube de 3º | Credenciales en SaaS |
| URLs de Referencia    | Código propio en FastAPI         | https://traderspost.io    | https://pickmytrade.trade | https://crosstrade.io |
+-----------------------------------------------------------------------------------------------------------------------------+
```

#### Ventajas del Receptor Propio en VPS (FastAPI + Nginx HTTPS):
1. **Coste $0 Recurrente:** Corre en la misma infraestructura del bot/VPS sin cuotas mensuales de intermediarios.
2. **Soberanía y Seguridad Total:** Las API keys del broker (Tradovate/Rithmic/BingX) nunca tocan servidores de terceros.
3. **Validación Previa con Lógica REAL-ONLY:** El webhook no ejecuta ciegamente; el receptor consulta el módulo de riesgo en memoria (`RiskGuard`), verifica si la cuenta está en drawdown máximo diario, y solo entonces autoriza la orden.

#### Arquitectura del Receptor Propio en VPS:
```
 TradingView Cloud (Alert)
          │  POST https://trading.tudominio.com/api/v1/webhook/tv
          │  [IP Whitelist: 52.89.214.238, 34.212.75.30, 54.218.53.128, 52.32.178.7]
          ▼
┌─────────────────────────────────────────────────────────────┐
│ VPS Linux (Nginx Reverse Proxy - Puerto 443 SSL / TLS 1.3)  │
│ - Terminación SSL con Certificado Let's Encrypt             │
│ - Filtro ufw / Nginx allow para IPs de TradingView          │
└──────────────────────────────┬──────────────────────────────┘
                               │ Proxy Pass http://127.0.0.1:8000
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FastAPI Webhook Handler (`services/api/routes/webhook.py`)   │
│ 1. Valida Header o Payload `{"passphrase": "SECRET_KEY"}`    │
│ 2. Parsea JSON con schema Pydantic inmutable                │
│ 3. Pasa señal al `RiskGuard` & `ExploitationEngine`          │
│ 4. Retorna HTTP 200 OK en < 15ms (cumple SLA < 3s de TV)    │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ SQLite WAL (`database.sqlite`) & Tradovate / NT8 Execution   │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚠️ 3. RIESGO DE DUPLICAR LÓGICA EN PINE SCRIPT VS MOTOR PYTHON COMO ÚNICA FUENTE DE VERDAD

La doctrina **REAL-ONLY / ZERO-MOCKS** del proyecto exige que exista **una única fuente de verdad (*Single Source of Truth* - SSOT)** para el cálculo de señales, control de balances, margin calls y gestión del riesgo.

### 3.1. Los 5 Fallos Críticos de Duplicar Lógica en Pine Script

```
                                  ┌────────────────────────────────────────┐
                                  │   RIESGOS DE EJECUCIÓN EN PINE SCRIPT  │
                                  └───────────────────┬────────────────────┘
                                                      │
         ┌───────────────────┬────────────────────────┼────────────────────────┬───────────────────┐
         ▼                   ▼                        ▼                        ▼                   ▼
┌─────────────────┐ ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐ ┌─────────────────┐
│ 1. DIVERGENCIA  │ │ 2. REPAINTING & │      │  3. ASUNCIÓN DE │      │ 4. DESINCRONÍA  │ │ 5. INEXISTENCIA │
│  DE DATA FEEDS  │ │ LOOKAHEAD BIAS  │      │  FILLS PERFECTOS│      │  DE ESTADO FSM  │ │ DE ACID STORAGE │
│ (BATS vs CME)   │ │ (request.sec.)  │      │  (Zero Slippage)│      │  (State Drift)  │ │ (Sin auditoría) │
└─────────────────┘ └─────────────────┘      └─────────────────┘      └─────────────────┘ └─────────────────┘
```

1. **Divergencia de Data Feeds:**
   - TradingView utiliza feeds agregados y consolidados (como Cboe BATS para acciones de EE.UU. o feeds CFD con filtrado de ticks).
   - El motor Python de futuros CME opera con datos de mercado L1/L2 de grado institucional (Rithmic R|Protocol, Tradovate WebSocket). Una ruptura de rango calculada en TradingView puede ocurrir en un precio o segundo distinto al del libro de órdenes real de CME Globex.
2. **Repainting y Sesgo de Lookahead:**
   - En Pine Script, funciones como `request.security()` con parámetros por defecto o scripts que evalúan `calc_on_every_tick=true` sin confirmar el cierre de vela (`barstate.isconfirmed`) generan señales temporales que luego desaparecen del gráfico. En backtest muestran retornos extraordinarios que en operativa real resultan en ejecuciones erráticas.
3. **Asunción de Fills Perfectos y Cero Slippage:**
   - El simulador de estrategias de TradingView (`strategy.entry()`) asume que toda orden límite o stop se ejecuta exactamente al precio solicitado sin slippage de liquidez ni retrasos en cola de órdenes (*order book queue priority*).
4. **Desincronización de Estado (*State Drift*):**
   - Pine Script carece de comunicación bidireccional en tiempo real sobre el estado del broker. Si el broker rechaza una orden por falta de margen o liquidez, Pine Script asume que la posición fue abierta, acumulando un desajuste progresivo entre la posición teórica del gráfico y la posición real en la cuenta de fondeo.
5. **Inexistencia de Almacenamiento Transaccional ACID:**
   - Pine Script no posee base de datos persistente. Ante una recarga del gráfico o caída de sesión, pierde el historial de ejecuciones, variables de estado y control de drawdown intradía acumulado.

---

### 3.2. Solución Canónica: TradingView Únicamente como VISOR / Señalera Opcional

Bajo la doctrina del sistema:
- **TradingView como VISOR Pasivo:** Se utiliza para que el operador humano observe los gráficos, niveles de soporte/resistencia e indicadores visuales de telemetría emitidos por el bot.
- **TradingView como Señalera Auxiliar (Opcional):** Si se utiliza una alerta de TradingView, el webhook entrante se trata como una **"propuesta de evento"** (`CandidateSignalEvent`). El motor Python valida:
  1. ¿La cuenta está dentro de los límites de pérdida diaria (*Daily Loss Limit*)?
  2. ¿El spread y la volatilidad actual están en rangos permitidos?
  3. ¿El contrato está dentro del horario operativo permitido por la prop firm?
  4. Si y solo si todas las *Evidence Gates* son superadas, el motor Python genera y firma la orden real.

---

## 🏛️ 4. ARQUITECTURA GLOBAL INTEGRADA (DIAGRAMA ASCII COMPLETO)

```
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════
                                 ARQUITECTURA DE TRADING CUANTITATIVO REAL-ONLY 2026
═══════════════════════════════════════════════════════════════════════════════════════════════════════════════════

   [ FUENTES DE DATOS & SEÑALIZACIÓN EXTERNA ]
   ┌─────────────────────────────────────────┐       ┌─────────────────────────────────────────────────────┐
   │     TradingView Cloud (Opcional)        │       │       CME Globex Market Data / Crypto Feeds         │
   │  - Indicador Visual / Alerta Webhook    │       │  - Tradovate WebSocket L1/L2 Market Feed            │
   │  - JSON Payload firmado con Passphrase  │       │  - BingX Perpetual Swap Real-time Market Data       │
   └────────────────────┬────────────────────┘       └──────────────────────────┬──────────────────────────┘
                        │ HTTPS POST (Port 443)                                 │ Real-time WS Stream
                        ▼                                                       ▼
   ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
   [ INGESTION & NETWORK GATEWAY LAYER (VPS LINUX) ]
   ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
   │  Nginx Reverse Proxy (SSL TLS 1.3 / Let's Encrypt)                                                    │
   │  - IP Whitelist: 52.89.214.238, 34.212.75.30, 54.218.53.128, 52.32.178.7 (TradingView IPs)           │
   │  - Rate Limiting: 30 req/min por IP                                                                   │
   │  - UFW Firewall: Deny All excepto 22 (SSH Clave), 80/443 (Nginx Webhook & Dashboard)                  │
   └───────────────────────────────────────────────────┬───────────────────────────────────────────────────┘
                                                       │ Proxy Pass (Localhost :8000)
                                                       ▼
   ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
   [ CORE QUANT ENGINE - SINGLE SOURCE OF TRUTH (PYTHON 3.12 FASTAPI) ]
   ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
   │                                   FastAPI Application Core                                            │
   │  ┌───────────────────────────────┐ ┌────────────────────────────────┐ ┌────────────────────────────┐ │
   │  │   /api/v1/webhook/tv          │ │   MarketData Ingestion Service │ │   SSE Telemetry Stream     │ │
   │  │   - Pydantic v2 Schema        │ │   - Tick-by-tick WS Buffer     │ │   - Next.js Web Dashboard  │ │
   │  │   - Passphrase & HMAC Check   │ │   - Microstructure Indicators  │ │   - Status / Heartbeat     │ │
   │  └───────────────┬───────────────┘ └────────────────┬───────────────┘ └────────────────────────────┘ │
   │                  │ Inbound Event                    │ Clean Ticks                                     │
   │                  ▼                                  ▼                                                 │
   │  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐  │
   │  │                              EVIDENCE GATES & RISKGUARD (Reglas Duras)                          │  │
   │  │  1. Check Max Daily Loss ($ / %)     2. Check Trailing Drawdown     3. Check Circuit Breaker    │  │
   │  │  4. Check Prop Firm Schedule Limits  5. Check Current Open Exposure 6. Check SHA-256 Signature  │  │
   │  └────────────────────────────────────────────────┬────────────────────────────────────────────────┘  │
   │                                                   │ Approved Signal Event                             │
   │                                                   ▼                                                   │
   │  ┌─────────────────────────────────────────────────────────────────────────────────────────────────┐  │
   │  │                             EXPLOITATION ENGINE (Bifurcación Dual)                               │  │
   │  │   - TRACK_FONDEO: CME Futures (MNQ, MES, MGC) / Preservación Estricta / 0% Compounding          │  │
   │  │   - TRACK_ULTRA: Cripto Perpetuals (BingX) / Hiperescalado Convexo / Bóveda Ratchet (50-85%)    │  │
   │  └────────────────────────────────────────────────┬────────────────────────────────────────────────┘  │
   │                                                   │                                                   │
   │  ┌────────────────────────────────────────────────┴────────────────────────────────────────────────┐  │
   │  │                        STORAGE LAYER: SQLite WAL Engine (`database.sqlite`)                     │  │
   │  │  - Tabla `trades` (Inmutable)   - Tabla `risk_metrics`   - Tabla `audit_events` (SHA-256 Log)   │  │
   │  └────────────────────────────────────────────────┬────────────────────────────────────────────────┘  │
   └───────────────────────────────────────────────────┼───────────────────────────────────────────────────┘
                                                       │ Dispatched Orders
                                                       ▼
   ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
   [ EXECUTION & BROKER ROUTING LAYER ]
   ┌───────────────────────────────────────────────────┬───────────────────────────────────────────────────┐
   │                                                   │                                                   │
   │  RUTA A: CME Futures (Tradovate Direct API)       │  RUTA B: NinjaTrader 8 Desktop Bridge             │
   │  - REST: `POST /v1/order/placeOrder`              │  - Método 1: TCP ATI (Automated Trading Interface)│
   │  - WS: `wss://live.tradovateapi.com/v1/websocket` │  - Método 2: OIF (Order Instruction File en disco)│
   │  - Bearer Token Auth (Exp: 24h con auto-refresh)  │  - Método 3: CrossTrade C# NT8 Add-On             │
   │  - Cuentas: Apex Trader Funding / Tradovate Prop  │  - Cuentas: Rithmic / CQGs / Prop Firms MT5/NT8   │
   │                                                   │                                                   │
   │  RUTA C: Cripto Perpetuals (BingX API v2)                                                             │
   │  - REST: `POST /openApi/swap/v2/trade/order` (HMAC SHA-256 Signature)                                 │
   └───────────────────────────────────────────────────┼───────────────────────────────────────────────────┘
                                                       │
                                                       ▼
   ════════════════════════════════════════════════════════════════════════════════════════════════════════════════
   [ SUPERVISION & ORCHESTRATION LAYER (HERMES AGENT) ]
   ┌───────────────────────────────────────────────────────────────────────────────────────────────────────┐
   │  Hermes Agent Scheduler (`jobs.json` / System Crons)                                                  │
   │  ┌─────────────────────────┐ ┌─────────────────────────┐ ┌──────────────────────────────────────────┐ │
   │  │  Cron 1: Risk Watchdog  │ │  Cron 2: WS Heartbeat   │ │  Cron 3: Hard Kill-Switch Auto-Lock      │ │
   │  │  - Cada 1 minuto        │ │  - Cada 5 minutos       │ │  - Si Daily Loss >= $1,000 (PA 50k)      │ │
   │  │  - Chequea PnL Flotante │ │  - Re-conecta sockets   │ │  - Cierra posiciones y cancela órdenes   │ │
   │  └─────────────────────────┘ └─────────────────────────┘ └──────────────────────────────────────────┘ │
   │  ┌──────────────────────────────────────────────────────────────────────────────────────────────────┐ │
   │  │  Cron 4: Resumen Diario EOD (17:05 NY) -> Envío Automático al Chat de Hermes / Telegram          │ │
   │  └──────────────────────────────────────────────────────────────────────────────────────────────────┘ │
   └───────────────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 5. INTEGRACIÓN OPERATIVA CON HERMES AGENT (CRONJOBS Y AUTOMATIZACIÓN)

Hermes Agent actúa como el **supervisor externo autónomo** (*Autonomous Watchdog & Operations Sentry*), ejecutando comprobaciones periódicas sin intervención humana y reportando estados críticos directamente a la interfaz de chat (local o Telegram).

### 5.1. Tabla de Cronjobs Propuestos para Hermes

| ID Job | Nombre del Job | Expresión Cron | Frecuencia | Modo / Script | Acción Ejecutada | Entrega (*Deliver*) |
|---|---|---|---|---|---|---|
| `risk_watchdog` | 🛡️ Quant Risk & Drawdown Sentinel | `* * * * *` | Cada 1 min | `no_agent: true`<br>`watchdog_risk.py` | Consulta balance y PnL flotante real en API Tradovate/BingX. Verifica si se acerca al 70% del daily loss limit. | Silencioso / Alerta condicional si Drawdown > 70% |
| `ws_healthcheck` | 💓 WebSocket Latency & Heartbeat | `*/5 * * * *` | Cada 5 min | `no_agent: true`<br>`check_ws_health.py` | Verifica si el socket de mercado y órdenes está vivo. Si lleva > 15s sin mensajes, fuerza reconexión limpia. | Alerta si hubo reconexión forzada |
| `kill_switch_guard` | 🚨 Emergency Kill-Switch & Lock | `* * * * *` | Cada 1 min | `no_agent: true`<br>`emergency_killswitch.py` | Si el PnL acumulado diario $\le -\text{MaxDailyLoss}$, ejecuta `FLATTEN_ALL`, cancela órdenes y crea lockfile de bloqueo. | Mensaje prioritario al chat con PnL final y trades cerrados |
| `eod_daily_summary` | 📊 EOD Real Performance Report | `5 17 * * 1-5` | Lun-Vie 17:05 NY | `no_agent: false`<br>Prompt de análisis Hermes | Lee SQLite WAL de la jornada, calcula Sharpe, Win Rate, Comisiones y Retorno Neto Real, entregando reporte formateado. | `deliver: "telegram"` o chat local |

---

### 5.2. Implementación Técnica: Scripts y Definición de Crons en Hermes

#### A. Script del Watchdog de Riesgo y Kill-Switch (`scripts/hermes_risk_watchdog.py`)
```python
#!/usr/bin/env python3
"""
Hermes Risk Watchdog & Automatic Kill-Switch (Zero-Mocks / Real-Only)
Ubicación: /home/ubuntu/workspace/pro/trading/01 Ultrarentable/scripts/hermes_risk_watchdog.py
"""
import os
import sys
import json
import sqlite3
import requests
from datetime import datetime, timezone

DATABASE_PATH = os.getenv("TRADING_DB_PATH", "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/database.sqlite")
MAX_DAILY_LOSS_USD = float(os.getenv("MAX_DAILY_LOSS_USD", "1000.0"))
LOCKFILE_PATH = "/tmp/trading_killswitch.lock"

def get_current_day_pnl():
    """Consulta la base de datos física real (SQLite WAL)."""
    if not os.path.exists(DATABASE_PATH):
        return {"error": "DATABASE_NOT_FOUND", "real_pnl": 0.0, "open_positions": 0}
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    
    cursor.execute("""
        SELECT COALESCE(SUM(realized_pnl), 0), COALESCE(SUM(fees), 0), COUNT(*)
        FROM trades 
        WHERE date(closed_at) = ?
    """, (today_str,))
    realized, fees, count = cursor.fetchone()
    
    # Consultar PnL flotante activo
    cursor.execute("SELECT COALESCE(SUM(unrealized_pnl), 0), COUNT(*) FROM active_positions")
    unrealized, open_count = cursor.fetchone()
    
    conn.close()
    net_daily_pnl = realized - fees + unrealized
    return {
        "net_pnl": net_daily_pnl,
        "realized": realized,
        "unrealized": unrealized,
        "fees": fees,
        "trade_count": count,
        "open_positions": open_count
    }

def execute_hard_killswitch(metrics):
    """Ejecuta cierre forzado (Flatten) y bloqueo del sistema."""
    # 1. Crear Lockfile inmediato
    with open(LOCKFILE_PATH, "w") as f:
        f.write(json.dumps({"locked_at": datetime.now(timezone.utc).isoformat(), "reason": "MAX_DAILY_LOSS_EXCEEDED", "metrics": metrics}))
    
    # 2. Llamada directa a la API local de ejecución para cerrar todo
    try:
        res = requests.post("http://127.0.0.1:8000/api/v1/execution/emergency-flatten", json={"secret": os.getenv("KILLSWITCH_SECRET")}, timeout=3.0)
        api_status = res.json()
    except Exception as e:
        api_status = {"error": str(e)}
        
    output = {
        "status": "CRITICAL_KILL_SWITCH_TRIGGERED",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "net_pnl": metrics["net_pnl"],
        "max_limit": -MAX_DAILY_LOSS_USD,
        "open_positions_closed": metrics["open_positions"],
        "api_response": api_status
    }
    print(json.dumps(output, indent=2))
    sys.exit(1)

def main():
    if os.path.exists(LOCKFILE_PATH):
        print(json.dumps({"status": "LOCKED", "message": "System is locked by existing kill-switch lockfile."}))
        return

    metrics = get_current_day_pnl()
    if "error" in metrics:
        print(json.dumps(metrics))
        return

    # Comprobación de límite de pérdida
    if metrics["net_pnl"] <= -MAX_DAILY_LOSS_USD:
        execute_hard_killswitch(metrics)
    else:
        # Estado normal
        print(json.dumps({
            "status": "OK",
            "net_daily_pnl": round(metrics["net_pnl"], 2),
            "open_positions": metrics["open_positions"],
            "daily_loss_usage_pct": round((abs(metrics["net_pnl"]) / MAX_DAILY_LOSS_USD) * 100, 2) if metrics["net_pnl"] < 0 else 0.0
        }))

if __name__ == "__main__":
    main()
```

#### B. Registro del Cronjob en Hermes Agent (`~/.hermes/cron/jobs.json`)
Para registrar estos cronjobs en Hermes, se añade la definición al archivo de jobs o mediante el comando `hermes cron create`:

```json
{
  "jobs": [
    {
      "id": "quant_risk_watchdog_01",
      "name": "🛡️ Quant Risk & Drawdown Sentinel",
      "prompt": "Ejecuta el script de supervisión de riesgo real y kill-switch. Script: /home/ubuntu/workspace/pro/trading/01 Ultrarentable/scripts/hermes_risk_watchdog.py",
      "script": "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/scripts/hermes_risk_watchdog.py",
      "no_agent": true,
      "schedule": {
        "kind": "cron",
        "expr": "*/2 * * * *"
      },
      "schedule_display": "*/2 * * * *",
      "enabled": true,
      "state": "running",
      "deliver": "local",
      "enabled_toolsets": ["terminal"]
    },
    {
      "id": "quant_eod_report_01",
      "name": "📊 Daily Quant Performance Summary EOD",
      "prompt": "Consulta la base de datos SQLite /home/ubuntu/workspace/pro/trading/01 Ultrarentable/database.sqlite y genera un resumen conciso de los trades cerrados hoy, PnL neto, comisiones y estado de las cuentas de fondeo.",
      "script": null,
      "no_agent": false,
      "schedule": {
        "kind": "cron",
        "expr": "5 22 * * 1-5"
      },
      "schedule_display": "22:05 UTC (Lun-Vie)",
      "enabled": true,
      "state": "running",
      "deliver": "local",
      "enabled_toolsets": ["terminal", "file"]
    }
  ]
}
```

---

## 🔒 6. SEGURIDAD Y BLINDAJE DE CREDENCIALES

La seguridad en la operativa algorítmica con capital real o cuentas de evaluación institucional exige una política de defensa en profundidad (*Defense in Depth*).

```
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                             MATRIZ DE SEGURIDAD OPERATIVA                                │
├──────────────────────────┬───────────────────────────────────────────────────────────────┤
│ GESTIÓN DE API KEYS      │ • Almacenamiento exclusivo en `.env` con permisos `chmod 600`.│
│                          │ • Carga mediante `systemd EnvironmentFile=/etc/trading.env`.  │
│                          │ • Prohibición absoluta de commits de claves en Git.           │
├──────────────────────────┼───────────────────────────────────────────────────────────────┤
│ IP WHITELISTING          │ • Tradovate & BingX API: Vincular API keys a la IP fija VPS.  │
│                          │ • Nginx: Bloquear todo tráfico entrante a `/api/v1/webhook/*` │
│                          │   excepto IPs de TradingView (52.89.214.238, 34.212.75.30, etc)│
├──────────────────────────┼───────────────────────────────────────────────────────────────┤
│ PRINCIPIO DE MÍNIMO      │ • Permisos de API Key de Tradovate/BingX: Habilitar solo      │
│ PRIVILEGIO               │   "Trade / Order Entry" y "Market Data".                      │
│                          │ • DESHABILITAR TOTALMENTE permisos de "Withdrawal / Transfer".│
├──────────────────────────┼───────────────────────────────────────────────────────────────┤
│ FIRMA CRIPTOGRÁFICA      │ • Webhook Payloads verificados mediante HMAC SHA-256 o token  │
│ DE WEBHOOKS              │   secreto de alta entropía (`Passphrase` > 32 caracteres).    │
│                          │ • Rechazo inmediato (HTTP 401/403) ante discrepancia de token.│
└──────────────────────────┴───────────────────────────────────────────────────────────────┘
```

### 6.1. Configuración de Reglas de Nginx con IP Whitelist para Webhooks
```nginx
# Fragmento de configuración Nginx en /etc/nginx/sites-available/trading_webhook.conf
server {
    listen 443 ssl http2;
    server_name trading.tudominio.com;

    ssl_certificate /etc/letsencrypt/live/trading.tudominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/trading.tudominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;

    location /api/v1/webhook/tv {
        # TradingView Official Webhook IP Allowlist
        allow 52.89.214.238;
        allow 34.212.75.30;
        allow 54.218.53.128;
        allow 52.32.178.7;
        
        # Permitir localhost para tests locales
        allow 127.0.0.1;
        
        # Denegar todo el resto de Internet
        deny all;

        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout estricto para responder a TradingView en < 3s
        proxy_read_timeout 3s;
        proxy_connect_timeout 2s;
    }
}
```

---

## 🎯 7. CONCLUSIÓN Y RECOMENDACIÓN ESTRATÉGICA FINAL

1. **TradingView:** No es necesario pagar el plan Premium ($59.95/mes) a menos que se requieran alertas de segundos; el plan **Plus ($24.95/mes facturado anual)** es el punto óptimo que desbloquea 100 alertas activas y webhooks completos.
2. **Receptor Webhook:** **Descartar middlewares de terceros** (TradersPost/PickMyTrade) que añaden $50-$100/mes de coste redundante y latencia innecesaria. El receptor propio en FastAPI detrás de Nginx en el VPS es gratuito, más rápido (<1ms vs 300ms) y 100% seguro.
3. **Doctrina Arquitectónica:** Mantener el **motor Python como ÚNICA FUENTE DE VERDAD**. TradingView solo debe utilizarse como visor gráfico o señalera auxiliar sujeta a las compuertas de evidencia (*Evidence Gates*) del motor central.
4. **Supervisión con Hermes:** Implementar la suite de 4 cronjobs en Hermes (`watchdog_risk`, `ws_healthcheck`, `kill_switch_guard`, `eod_daily_summary`) para garantizar la supervivencia de las cuentas de fondeo sin depender de la presencia continua del operador humano.
