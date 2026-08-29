> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: sub-nota antigua que describe SQX como MCP 8080/8081; el motor real es sqcli HTTP :5050 — ver docs/00_MASTER_IDEAS_Y_PLAN.md §2.1. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

---
tipo: sub-nota
categoria: trading
estado: activo
vigencia: actual
estado_conocimiento: implementacion_pendiente_de_prueba_viva
fecha: 2026-08-03
tags:
  - candidatos
  - estrategias
  - sqx
  - strategyquant
  - sub-nota
  - trading
  - ultrarentable
proyecto: 01 Ultrarentable
ficha_maestra: '[[Ultrarentable]]'
subtema: motor-sqx
fecha_creacion: 2026-08-03
---

# ⚙️ Motor StrategyQuant X — Fábrica de Candidatos

> StrategyQuant X actúa como **única fuente de candidatos a estrategias**. No tiene autoridad final para aprobar ninguna estrategia; eso lo decide el validador independiente.

> [!WARNING]
> El adaptador existe en el código de la VPS, pero todavía no se ha certificado el recorrido real con StrategyQuant X abierto. Ver [[Estado verificado de Ultrarentable]].

---

## 🎯 Navegación y Enlaces Bidireccionales
- 📌 **Ficha Maestra:** [[Ultrarentable]]
- 🔗 **Sub-notas Relacionadas:** [[Plan 10 Fases]] | [[Motor de Fondeo y Prop Firms]] | [[Dashboard Web]]

---

## Integración y Conexión

- **Ubicación:** SQX corre localmente en el PC.
- **Servidor MCP:** Escucha en el puerto `http://localhost:8080/mcp`.
- **Protocolo:** HTTP JSON-RPC 2.0 + Server-Sent Events (SSE).
- **Cliente:** `services/sqx_bridge/sqx_client.py`.

---

## El Embudo de Candidatos (Pipeline Secuencial)

```text
Generación SQX
      ↓
Filtro Rápido (métricas básicas)
      ↓
Retest (verificación interna)
      ↓
Robustez (stress test de parámetros)
      ↓
Monte Carlo (simulación estocástica)
      ↓
Walk-Forward (optimización por ventanas)
      ↓
Exportación → Conversión a StrategySpec YAML (`converter.py`)
```

---

## Validador Independiente (`validator.py`)

Cualquier estrategia extraída de SQX pasa obligatoriamente por estos filtros antes de ir al Leaderboard:
- Mínimo 30 operaciones (`min_trades`).
- Profit Factor ≥ 1.3.
- Drawdown Máximo ≤ 20%.
- Cierre obligatorio de posiciones al final de sesión (Overnight Risk = 0).
- Descarte de sobreajuste o dependencia de operaciones anómalas.
