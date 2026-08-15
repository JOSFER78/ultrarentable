# 📊 ESTADO.md — Estado vivo del proyecto Ultrarentable

> **Última actualización:** 2026-08-09
> **Próxima acción:** ver sección "Próximo paso".
> Este archivo se actualiza al final de cada sesión de trabajo.

---

## Resumen ejecutivo

El laboratorio está **operativo**: servicios 24/7, web funcional, SQX generando candidatos reales. La investigación teórica y el framework de validación están completos. **El cuello de botella actual es que no se ha encontrado ninguna estrategia de miles de %** — el mejor candidato real tiene ~2.24% IS retorno. Hay que afinar la búsqueda kamikaze (fitness, universo de indicadores, generaciones).

---

## ✅ Hecho

| Qué | Fecha | Detalle |
|-----|-------|---------|
| Investigación consolidada | 2026-07 | Catálogo de 28 técnicas de trading algorítmico, informe máster de bots, corroboración de hechos clave |
| Blueprint controlador de estrategias | 2026-08 | Protocolo completo para validar estrategias de miles de % (`plan_implementacion/BLUEPRINT_CONTROLADOR_ESTRATEGIAS_MUNDIAL.md`) |
| Guía de uso experto de SQX | 2026-08 | Flujo kamikaze y fondeo documentado como lo haría un experto (`plan_implementacion/GUIA_EXPERTO_USAR_SQUANT.md`) |
| Auditoría de candidatos kamikaze | 2026-08-09 | Scorecard de calidad con criterios cuantitativos. Resultado: 0 candidatos válidos de miles de %; las 24 estrategias viejas eran mediocres (`plan_implementacion/AUDITORIA_CANDIDATOS_KAMIKAZE.md`) |
| Core backend Ultra/Fondeo | 2026-07 | Configurador con modos Ultra y Fondeo, 125 tests passing en `services/api/tests/` |
| Panel configurador IA (web) | 2026-07 | Frontend Next.js con panel de configuración de búsqueda de estrategias |
| SQX desbloqueado | 2026-08-09 | SQX generando candidatos nuevos reales (serie 4.1.x) vía MCP. Databank desbloqueado |
| Servicios 24/7 desplegados | 2026-07 | API FastAPI (:8000), Web Next.js (:3000), SQX (:8080 MCP) corriendo como systemd --user |
| Acceso Obsidian vía Tailscale | 2026-08-08 | REST API funcional desde VPS al PC del usuario (`http://100.106.212.23:27123`) |
| Plan de orquestación motor de búsqueda | 2026-08-09 | Documento de orquestación del controlador creado (`plan_implementacion/ORQUESTACION_MOTOR_BUSQUEDA_20260809.md`) |

---

## 🔴 Pendiente

| Qué | Prioridad | Notas |
|-----|-----------|-------|
| **Encontrar estrategia de miles de %** | 🔴 CRÍTICA | El objetivo principal. Mejor candidato actual: ~2.24% IS retorno. Ninguno cerca de 1000%+ |
| Afinar búsqueda kamikaze nivel 2 | 🔴 ALTA | Cambiar fitness de SQX a retorno puro (no Sharpe/Profit Factor), ampliar universo de indicadores, más generaciones, más pares |
| Resolver acceso GUI virtual de SQX | 🟡 MEDIA | Poder ver la GUI de SQX remotamente (VNC/noVNC a DISPLAY=:99) para inspección visual |
| Ejecutar plan de orquestación | 🟡 MEDIA | Implementar el controlador de búsqueda según `ORQUESTACION_MOTOR_BUSQUEDA_20260809.md` |
| Pipeline fondeo completo | 🟡 MEDIA | Integrar prop firms con cuenta gratis, definir criterios de aprobación de examen |
| Backfill histórico paginado | 🟠 BAJA | Completar ingesta de datos históricos de BingX |
| Motores de backtest adicionales | 🟠 BAJA | NautilusTrader, adaptador BingX |

---

## 🎯 Próximo paso concreto

**Afinar la búsqueda kamikaze nivel 2 en SQX:**

1. Cambiar la función fitness de SQX a **retorno neto puro** (no Sharpe ni Profit Factor) — el modo kamikaze no penaliza volatilidad.
2. Ampliar el **universo de indicadores/bloques genéticos** disponibles para la generación.
3. Aumentar el número de **generaciones** y **población** en la búsqueda genética.
4. Expandir los **pares/timeframes** bajo prueba (no solo BTCUSDT).
5. Monitorear la serie 4.1.x de candidatos y evaluar con el scorecard de `AUDITORIA_CANDIDATOS_KAMIKAZE.md`.

---

## 📁 Dónde está cada cosa

| Recurso | Ubicación |
|---------|-----------|
| Estado vivo (este archivo) | `ESTADO.md` |
| **Modelo multiagente + sistema de seguimiento** | `MULTIAGENTE_Y_SEGUIMIENTO.md` |
| Guía de entrada (web/Obsidian/servicios) | `README.md` |
| Bitácora de sesiones | `plan_implementacion/bitacora/<fecha>.md` |
| Documentos de plan/investigación | `plan_implementacion/*.md` |
| Espejo de teoría Obsidian | `docs/` |
| Backend API | `services/api/` |
| Frontend web | `apps/web/` |
| Tests canónicos | `services/api/tests/` |
| BD operacional | `~/.local/state/ultrarentable/ultrarentable.sqlite3` |
