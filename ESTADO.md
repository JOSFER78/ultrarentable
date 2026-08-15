# 📊 ESTADO.md — Mapa Único y Estado Vivo del Proyecto

> **Última actualización:** 2026-08-15 (Fases 0 a 5 Completadas)  
> **Doctrina:** REAL-ONLY · **Prioridad:** FONDEO-PRIMERO (Modo ULTRA Congelado)

---

## 1. Resumen Ejecutivo y Realidad Verificada

El laboratorio opera bajo la doctrina de **Fondeo Primero**. El generador de StrategyQuant X ha sido completamente reconfigurado con los **10 cambios anti-overfit** del Plan Maestro, produciendo los primeros candidatos reales aprobados con ventaja matemática fuera de muestra (OOS):

- **Histórico Previo:** 95 estrategias / 77 backtests (0 aprobados).
- **Run de Prueba Fondeo (2026-08-15):** 100 estrategias evaluadas ➔ **2 candidatas aprobadas** bajo los 5 gates canónicos de fondeo:
  - 🥇 `Strategy 1.0.54`: Net Profit IS +13.45% (55 trades, PF 1.38, DD 10.0%) | **Net Profit OOS +16.85% (29 trades, PF 1.75, DD 10.1%)** | Ratio OOS/IS: **1.27**
  - 🥈 `Strategy 1.0.32`: Net Profit IS +7.35% (49 trades, PF 1.47, DD 5.3%) | **Net Profit OOS +3.10% (25 trades, PF 1.32, DD 3.7%)** | Ratio OOS/IS: **0.90**
- **Datos Disponibles en SQX:** 3.840 barras H1 de `BTCUSDT_AUTO` (26-feb a 4-ago 2026, 5,2 meses). Sin M1 (bar magnifier desactivado).
- **Servicios VPS:** Frontend Next.js en `:5000` (ONLINE), API FastAPI en `:8000` (ONLINE), SQX MCP en `:8081/mcp` (ONLINE).
- **Control de Versiones:** Repositorio privado [`https://github.com/JOSFER78/ultrarentable`](https://github.com/JOSFER78/ultrarentable) sincronizado en `main`.

---

## 2. Estado de Fases de Ejecución

| Fase | Descripción | Estado | Evidencia en Disco |
|---|---|---|---|
| **FASE 0** | Inventario Real y Auditoría Cuádruple | ✅ **COMPLETA** | 4 informes en `plan_implementacion/AUDITORIA_LECTURA_FASE0_*.md` (16.601 bytes total) |
| **FASE 1** | Congelar ULTRA y Perfil Fondeo Canónico | ✅ **COMPLETA** | UI (`apps/web/app/page.tsx`), API (`routes.py`) y `plan_implementacion/PERFIL_FONDEO_CANONICO.md` |
| **FASE 2** | Corrección XML del CFX (10/10 cambios) | ✅ **COMPLETA** | `project.cfx` (26.444 bytes) con `ReturnDDRatio`, WFO ON, Sesión LondonNY, `plan_implementacion/CFX_FONDEO_APLICADO.md` |
| **FASE 3** | Run Corto de Prueba con Gates Fondeo | ✅ **COMPLETA** | 100 evaluadas, 2 aprobadas, scorecard en `plan_implementacion/RESULTADOS_RUN_FONDEO_2026-08-15.md` |
| **FASE 4** | Decisión de Mercado (Sandbox vs Futuros) | ✅ **COMPLETA** | `plan_implementacion/DECISION_MERCADO_FONDEO.md` |
| **FASE 5** | De 1 Superviviente a Operativa | ✅ **COMPLETA** | Árbol y Kill-Switches en `plan_implementacion/PIPELINE_DE_SUPERVIVIENTE_A_OPERATIVA.md` |

---

## 3. Próximo Paso Concreto (Esperando Decisión de Mercado)

El usuario debe indicar qué ruta prefiere para la ejecución de la primera candidata (`Strategy 1.0.54`):
1. **Rama B (Recomendada):** Exportación a formato nativo de Futuros CME (Topstep / Apex / TradeDay) para cuenta financiada de $50.000.
2. **Rama A:** Simulación paper trading en el sandbox de BingX con el stack Python.
3. **Modo Híbrido:** Despliegue de ambas en paralelo.
