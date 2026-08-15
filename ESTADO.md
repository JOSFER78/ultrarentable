# 📊 ESTADO.md — Mapa Único y Estado Vivo del Proyecto

> **Última actualización:** 2026-08-15 (Sesión Fase 0 y Fase 1)  
> **Doctrina:** REAL-ONLY · **Prioridad:** FONDEO-PRIMERO (Modo ULTRA congelado)

---

## 1. Resumen Ejecutivo y Realidad Verificada

El laboratorio opera bajo la doctrina de **Fondeo Primero**, orientando la generación algorítmica a superar exámenes de prop firms y cobrar retiros reales de **$3.000–$4.000**. Queda eliminada la búsqueda "kamikaze" de 1000%.

- **Histórico Generado:** 95 estrategias y 77 backtests evaluados; **0 aprobados**.
- **Rendimiento Máximo Real en Disco:** ~2.24% IS retorno (cero candidatos de miles de %).
- **Datos Disponibles en SQX:** 3.840 barras H1 de `BTCUSDT_AUTO` (26-feb a 4-ago 2026, 5,2 meses). Sin M1 (bar magnifier desactivado).
- **Servicios VPS:** Frontend Next.js en `:5000` (ONLINE), API FastAPI en `:8000` (ONLINE, WAL activo, 1.051 contratos BingX).
- **Control de Versiones:** Repositorio privado [`https://github.com/JOSFER78/ultrarentable`](https://github.com/JOSFER78/ultrarentable) conectado y sincronizado en rama `main`.

---

## 2. Estado de Fases de Ejecución

| Fase | Descripción | Estado | Evidencia en Disco |
|---|---|---|---|
| **FASE 0** | Inventario Real y Auditoría Cuádruple | ✅ **COMPLETA** | 4 informes en `plan_implementacion/AUDITORIA_LECTURA_FASE0_*.md` (16.601 bytes total) |
| **FASE 1** | Congelar ULTRA y Perfil Fondeo Canónico | 🟡 **EN CURSO** | Bloqueo de UI/API y redacción de `PERFIL_FONDEO_CANONICO.md` |
| **FASE 2** | Corrección XML del CFX (4 cambios pendientes) | ⏳ **PENDIENTE** | Backup confirmado en `/home/ubuntu/backups/ultrarentable/pre_reconfig_20260809_105641/` |
| **FASE 3** | Run Corto de Prueba con Gates Fondeo | ⏳ **PENDIENTE** | Requiere resolver puerto SQX y correr lote acotado |
| **FASE 4** | Decisión de Mercado (Sandbox BTC vs Futuros CME) | ⏳ **PENDIENTE** | Documentación de la ruta para examen real |

---

## 3. Próximo Paso Concreto

1. **Completar FASE 1:**
   - Desactivar/congelar en la UI y API la selección del modo Ultra (fijar por defecto el modo Fondeo).
   - Generar `plan_implementacion/PERFIL_FONDEO_CANONICO.md` con las métricas cuantitativas estándar (Target ~6%, DLL ≤ 2.5%, Max DD ≤ 5%, consistencia 40-50%, trades OOS ≥ 20).
2. **Preparar FASE 2:** Aplicar los 4 cambios XML pendientes en `Build-Task1.xml` dentro del CFX sin alterar el backup.
