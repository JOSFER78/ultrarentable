---
tipo: informe-maestro-definitivo
proyecto: 01 Ultrarentable
categoria: conexiones-automatizar
fecha: 2026-08-25
ficha_maestra: "[[Ultrarentable]]"
estado: DEFINITIVO — investigación cerrada
tags: [ultrarentable, fondeo, definitivo, linux, hermes, ip, antibaneo]
---

# 🧭 DEFINITIVO: Conexión y Automatización desde VPS Linux ARM64 con Hermes

> **Investigación cerrada el 2026-08-25.** Este es el documento de entrada. Todo lo demás en esta carpeta son los detalles de cada decisión. Lo descartado está en `archive/`.

## Los 4 requisitos del usuario → sus 4 respuestas definitivas

### ✅ 1. "Todo usable desde Linux para que Hermes lo revise"

| Sistema | Veredicto Linux | Cómo |
|---|---|---|
| **Tradovate** | ✅ **NATIVO — vía principal** | API REST + WebSocket desde Python en tu ARM64. Detalles → `03` |
| **TradingView** | ✅ Sí (visor/señalera) | Webhooks → receptor FastAPI propio $0 en el VPS. Detalles → `04` |
| **NinjaTrader 8** | ⚠️ Programa no; órdenes sí | NT8 vive en un Windows remoto si una firma lo exige; puente OIF/CrossTrade/NinjaScript. Detalles → `02` |
| Rithmic | ✅ Sí | R\|API+ / WebSockets nativos Linux |

**Matiz Apex (aclaración de auditoría):** en Apex los bots están permitidos formalmente en FASE DE EVALUACIÓN; en cuenta fondeada (PA) sus reglas de consistencia auditan operativa de bot no supervisado — tratar con precaución y revisar su ToS vigente antes de automatizar en PA.
| "JA/Ya Trader" | ❌ No existe | Era daytradr (Windows) o J-Trader legacy Java. Detalles → `08` |

**Hermes supervisa todo desde el mismo VPS:** crons definidos en `04` §crons (risk_watchdog 1min · ws_healthcheck 5min · kill_switch_guard · conciliación · resumen EOD) + `scripts/ip_guard.py` ya creado y probado.

### ✅ 2. "Una IP / seguridad anti-baneos" → PROXY ISP ESTÁTICO RESIDENCIAL

**DECISIÓN FINAL:** contratar 1 IP residencial fija de ISP (Proxy-Seller Madrid ~$1.50–2.50/mes, alternativa IPRoyal $2.70) y sacar por ella TODO el tráfico de trading.

- Aparece como "residencial" ante MaxMind/IPQS (fraud score 0–5). No es VPN, no es datacenter.
- Sirve para TODAS las firms, incluso Topstep.
- Configuración: SOCKS5 en el código Python (`httpx[socks]`, `aiohttp-socks`) — solo bots la usan; SSH intacta. Paso a paso → `09` §8.
- Vigilancia: `ip_guard.py` como cron Hermes → si la IP cambia/cae, fail-closed.
- Descartadas y por qué → `07` (NordVPN Dedicated: flag VPN), `05` §Opciones (exit-node PC: dependencia), Oracle directa: solo vale para firmas tolerantes.

⚠️ Único paso humano obligatorio: confirmar POR ESCRITO con el soporte de la firma elegida que aceptan esa IP antes de pagar evaluación.

### ✅ 3. "No banearme por nada (bots, HFT, etc.)" → REGLAS DE ORO

1. **IP consistente**: siempre la misma (proxy ISP fijo resuelve).
2. **Nada de HFT/latencia-abuse**: las firms prohíben arbitraje de latencia y colocación rápida abusiva. Tu bot opera señales de estrategia normal (segundos-minutos), eso sí está permitido en MFFU/FundedNext/Apex/Bulenox.
3. **Reglas específicas por firma** → matriz completa en `03` §prop-firms y `06`: TPT prohíbe TODOS los bots ❌; Apex exige origen manual/copiador ⚠️; MFFU/FundedNext/Bulenox permiten bots propios ✅.
4. **Límites de rate**: Tradovate ~120–200 req/min, P-Ticket = cooldown 60min → respetar token-bucket (doc `03`).
5. **Kill-switch + límites de pérdida diaria** (doc `04`) — protege también contra fallos técnicos que parezcan comportamiento anómalo.
6. Marco legal: nada de esto es ley, son ToS contractuales; violarlos = baneo/pérdida de fondos de la cuenta, no sanción legal → `06`.
7. Fiscal España: payouts tributan en IRPF (rendimientos actividad económica) → `06` §7.

### ✅ 4. "Acceder a todos los proveedores (Ninja/Tradovate/TradingView)"

Resumen ejecutivo de costes de conexión:

| Vía | Coste/mes | Qué da |
|---|---|---|
| Proxy ISP fijo | ~$1.50–2.70 | Identidad limpia universal |
| Tradovate add-on API | $25 | Órdenes + user sync WS (sin licencia CME) |
| Feed de datos externo | $0–15 | Velas/ticks para el motor |
| TradingView Plus (opcional visor) | ~$30 | Webhooks de alertas |
| Receptor webhooks propio | $0 | FastAPI en el VPS |
| **TOTAL típico** | **~$28–47** | Sistema completo automatizado |

## Orden de ejecución recomendado

1. Elegir firma MVP → preguntar a su soporte política VPS/IP (plantilla lista abajo).
2. Comprar proxy ISP Madrid (Proxy-Seller) → verificar reputación (checklist `09` §5.1).
3. Configurar SOCKS5 en el motor Python (`09` §8.1) + actualizar `EXPECTED_IP` en `scripts/ip_guard.py`.
4. Activar crons Hermes de supervisión (`04`).
5. Demo Tradovate end-to-end: auth → order/test → WS heartbeat (`03`).
6. Solo entonces: pagar evaluación.

## Mapa final de la carpeta

| Doc | Contenido definitivo |
|---|---|
| `00` | Este índice maestro |
| `01` | VPN/IP: análisis completo de opciones y reglas VPN por firm |
| `02` | NinjaTrader desde Linux (5 rutas, costes) |
| `03` | Tradovate API completa + compatibilidad firms + rate limits |
| `04` | TradingView + arquitectura global + crons Hermes + seguridad |
| `05` | Evolución de la decisión de IP única (histórico de opciones) |
| `06` | Marco legal real: ley vs ToS, fiscalidad España |
| `07` | Por qué NO NordVPN Dedicated (auditoría forense) |
| `08` | "YA trader": resolución (no existe) |
| `09` | ⭐ SOLUCIÓN IP DEFINITIVA: proxy ISP estático (compra+config) |
| `archive/` | Primeras pasadas y apoyos (no leer salvo necesidad histórica) |
