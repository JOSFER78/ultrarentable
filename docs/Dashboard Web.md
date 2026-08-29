> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: sub-nota antigua del dashboard; el stack web real (API :8000 / Web :3005) vive en docs/00_MASTER_IDEAS_Y_PLAN.md §2.4. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

---
tipo: sub-nota
categoria: trading
estado: activo
vigencia: actual
estado_conocimiento: codigo_existente_runtime_no_certificado
fecha: 2026-08-03
tags:
  - dashboard
  - leaderboards
  - nextjs
  - sub-nota
  - trading
  - ultrarentable
proyecto: 01 Ultrarentable
ficha_maestra: '[[Ultrarentable]]'
subtema: dashboard-web
fecha_creacion: 2026-08-03
---

# 🖥️ Dashboard Web (Next.js - Puerto 3000)

> Panel de control dual en React / Next.js (`apps/web`) para la gestión visual del ecosistema.

> [!WARNING]
> Existe código y una compilación anterior en la VPS. Su funcionamiento actual y sus conexiones todavía no están certificados. Ver [[Estado verificado de Ultrarentable]].

---

## 🎯 Navegación y Enlaces Bidireccionales
- 📌 **Ficha Maestra:** [[Ultrarentable]]
- 🔗 **Sub-notas Relacionadas:** [[Plan 10 Fases]] | [[Motor StrategyQuant X]] | [[Motor de Fondeo y Prop Firms]] | [[Gestion de Capital — Balas y Estados]]

---

## Vistas Principales

1. **Leaderboards (BingX):** Ranking de las mejores estrategias clasificadas por fiabilidad. Separa strictly métricas FAST (aproximadas) de métricas CANÓNICAS (verificadas tick a tick).
2. **Base de Datos de Prop Firms:** Catálogo vivo con reglas actualizadas, costes de exámenes, límites de trailing drawdown y normas de consistencia para seleccionar qué cuentas comprar.
3. **Command Center:** Telemetría en tiempo real, estado de los servidores (FastAPI, SQX MCP) y logs de ejecución.
