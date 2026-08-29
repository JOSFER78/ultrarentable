> ⚠️ **SUPERSEDED (2026-08-29)** — Este documento es HISTÓRICO y ya NO es la fuente de verdad. Motivo: plan de 10 fases antiguo (2026-08-17); las fases y su estado real viven en docs/00_MASTER_IDEAS_Y_PLAN.md §4. **Fuente canónica vigente: `docs/00_MASTER_IDEAS_Y_PLAN.md`.** Contenido conservado intacto solo como referencia histórica. NO actualizar este archivo.

---
tipo: sub-nota
categoria: trading
estado: activo
vigencia: historico
estado_conocimiento: plan_no_verificado
fecha: 2026-08-03
tags:
  - fases
  - fondeo
  - hoja-de-ruta
  - sub-nota
  - trading
  - ultrarentable
proyecto: 01 Ultrarentable
ficha_maestra: '[[Ultrarentable]]'
subtema: plan-fases
fecha_creacion: 2026-08-03
---

# 🗺️ Plan Maestro de 10 Fases — Ultrarentable V2

> Hermes Agent usa este plan como guía estricta para construir el sistema capa por capa. Cada fase tiene entregables verificables.

> [!WARNING]
> **Documento histórico.** Los estados de esta tabla no demuestran el funcionamiento actual. La referencia vigente es [[Estado verificado de Ultrarentable]] y la dirección operativa actual corresponde a Codex, no a Hermes.

---

## 🎯 Navegación y Enlaces Bidireccionales
- 📌 **Ficha Maestra:** [[Ultrarentable]]
- 🔗 **Sub-notas Relacionadas:** [[Motor StrategyQuant X]] | [[Motor de Fondeo y Prop Firms]] | [[Gestion de Capital — Balas y Estados]] | [[Dashboard Web]] | [[Ultrarentable_Residuales]]

---

## Estado General

| Fase | Título | Estado | Entregable Real |
|:---:|---|:---:|---|
| **1** | Inventario completo y estabilización | 🟢 COMPLETADO | `STATUS.md` con fotografía del sistema |
| **2** | Nueva estructura modular (`apps/`, `services/`, `packages/`, `launcher/`) | 🟢 COMPLETADO | Carpeta `launcher/` con ejecutables `.bat` aislados |
| **3** | Formato común y neutro de estrategia (`StrategySpec`) | 🟢 COMPLETADO | Esquema Pydantic/YAML + tests al 100% |
| **4** | Adaptador e integración real con StrategyQuant X MCP | ⏳ PENDIENTE | Código listo (`services/sqx_bridge`). Requiere SQX abierto en puerto 8080 |
| **5** | Capa de validación independiente (anti-lookahead, anti-sobreajuste) | ⚪ PENDIENTE | Motor de reverificación fuera de SQX |
| **6** | Motor Ultra Rentable (Balas y Estados) | ⚪ PENDIENTE | Motor de interés compuesto y protección progresiva para BingX |
| **7** | Motor de Fondeo de Futuros (evaluación de reglas prop) | ⚪ PENDIENTE | Simulación contra reglas reales de empresas prop |
| **8** | Capa de Ejecución — Gateway (Tradovate / NinjaTrader / TradingView) | ⚪ PENDIENTE | Conector para plataformas de fondeo |
| **9** | Orquestador Hermes Agent (telemetría y control remoto) | ⚪ PENDIENTE | Agente autónomo de control, alertas e informes |
| **10** | Integración Frontend Consolidada | ⚪ PENDIENTE | Dashboard del laboratorio en `apps/web` (Next.js) |

---

## Detalle de Fases Clave

### Fase 4 — Integración SQX MCP
- Cliente `services/sqx_bridge/sqx_client.py` desarrollado.
- Requiere StrategyQuant X abierto escaneando en el puerto `8080`.

### Fase 5 — Validación Independiente
Exige que ninguna estrategia pase a producción sin superar:
- Anti-lookahead (uso de datos futuros)
- Anti-outlier (dependencia de 1 sola operación anómala)
- Cierre diario de sesión (Riesgo Overnight = 0)

### Fase 6 — Motor Ultra Rentable
Gestión de capital para BingX mediante el sistema de Balas y Estados.

### Fase 7 y 8 — Fondeo y Gateway
Evaluación de reglas prop y conectividad con Tradovate / Tradezilla / NinjaTrader.
