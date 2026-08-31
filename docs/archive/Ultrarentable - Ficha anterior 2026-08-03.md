> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: ficha histórica anterior (2026-08-03) marcada 'archivo'; la ficha vigente es docs/00_MASTER_IDEAS_Y_PLAN.md. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

---
tipo: referencia
categoria: trading
estado: archivo
fecha_creacion: 2026-08-03
fecha_archivado: 2026-08-04
proyecto: 01 Ultrarentable
motivo_archivo: Sustituida por una ficha canónica basada en confirmación del usuario e inspección por SSH.
tags:
  - ultrarentable
  - legado-documental
---

# Ultrarentable — Ficha anterior del 3 de agosto de 2026

> Copia íntegra de la ficha anterior. Se conserva para recuperar información, pero no describe por sí sola el estado actual verificado.

## Contenido anterior

# 🚀 01 Ultrarentable — Ficha Maestra

> **Laboratorio cuantitativo integral de descubrimiento de estrategias y fondeo.** Es el proyecto más avanzado y prioritario del ecosistema de trading. Funciona en modo *Local Real-Only* sin Docker sobre SQLite WAL.

## 🎯 1. Misión del Sistema

Ultrarentable opera **dos líneas de explotación paralelas**:

1. **Ultra Rentable (Bot BingX):** Estrategias de rentabilidad máxima con gestión de capital por "Balas y Estados". Operativa 100% en el exchange BingX.
2. **Motor de Fondeo de Futuros:** Estrategias diseñadas para superar las reglas de empresas prop. La métrica no es la rentabilidad bruta sino la **economía real neta**: `retiros netos - (coste de exámenes + activaciones + reinicios + licencias + data)`.

## 🏗️ 2. Arquitectura de Servicios y Puertos

| Servicio | Puerto | Tecnología | Estado | Función |
|:---|:---:|---|:---:|---|
| **Dashboard UI** | `3000` | React / Next.js (`apps/web`) | Activo (`http://localhost:3000`) | Control de campañas, Leaderboards, laboratorio DSL y base de prop firms |
| **FastAPI Backend** | `8000` | Python 3.11 (`services/api`) | Activo (`http://127.0.0.1:8000`) | Base de datos SQLite WAL, compilador DSL Engine y endpoints REST |
| **SQX Bridge**| `8080` | Java / Jetty + Python Client (`services/sqx_bridge`) | Requiere app SQX | Conector HTTP JSON-RPC 2.0 + SSE con StrategyQuant X local |

## 📂 3. Mapa del Código Fuente Real

```text
ultrarentable/
├── STATUS.md
├── README.md
├── ESTADO_PROYECTO/
├── apps/web/
├── services/api/
├── services/sqx_bridge/
├── services/strategy_core/
├── services/exploitation_engines/
├── packages/bingx-client/
├── ultrarentablev2/
└── data/
```

## 🗺️ 4. Sub-Notas Modulares de Profundidad

- [[Plan 10 Fases]]
- [[Motor StrategyQuant X]]
- [[Motor de Fondeo y Prop Firms]]
- [[Gestion de Capital — Balas y Estados]]
- [[Dashboard Web]]
- [[Ultrarentable_Residuales]]

## 🔗 5. Enlaces con Proyectos del Ecosistema

- [[TraderBot]]
- [[TV Lot Calculator]]
