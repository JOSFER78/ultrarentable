---
id: F10
titulo: "Operaciones e infraestructura — tareas para agentes (AGY)"
estado: EN_CURSO
depende_de: []
desbloquea: []
verificacion_global: "Cada tarea la verifica el orquestador re-ejecutando sus comandos de aceptación. Un parte de entrega sin salida cruda pegada no se acepta."
actualizado: "2026-09-03"
---

# FASE 10 — OPERACIONES E INFRAESTRUCTURA

Trabajo de máquinas: seguridad de los servidores, traslado de StrategyQuant X al servidor dedicado
de Hetzner, túneles, y la web que enseña todo esto. No es una fase del camino a la estrategia
certificada, pero sin ella las demás no corren.

## Dónde están las tareas

**En el tablero, no aquí.** Las tareas vivas están en `orchestration/tablero/` (un fichero por
tarea) y se ven en `/plan` → pestaña **Tareas AGY**, con su estado real leído del disco. Este
bloque no las duplica a propósito: dos listas de lo mismo siempre acaban contradiciéndose, que es
justo el fallo que este proyecto arrastra desde el principio.

- Cómo funciona el ciclo (estados, quién hace qué, cómo se avisa): `orchestration/tablero/README.md`.
- Reparto de las tres máquinas y por qué: `orchestration/ARQUITECTURA_RECURSOS.md`.
- Cierre de seguridad del Hetzner, paso a paso: `orchestration/RUNBOOK_HETZNER_SEGURIDAD.md`.

## Qué se está haciendo en esta fase (2026-09-03)

1. **Cerrar el Hetzner.** Llegó sin cortafuegos y con el escritorio remoto público sin contraseña
   (`curl` a la URL de noVNC devolvía 200, y `x11vnc` corría con `-nopw` en la IPv6 pública). Es lo
   primero porque en esa máquina va la licencia de StrategyQuant y, después, las campañas.
2. **Trasladar StrategyQuant X a Hetzner.** En Oracle está estrangulado a 1,2 núcleos y 4 GB de
   memoria compartiendo máquina con Hermes, la API y la web. En Hetzner puede usar 8 hilos y hasta
   48 GB. Hallazgo que condiciona el traslado: la instalación de Oracle es ARM y el Hetzner es
   Intel, así que se instala de nuevo y solo se copian los datos.
3. **La web enseña el tablero.** `/api/tablero` lee la carpeta de tareas en vivo; la pestaña
   **Tareas AGY** las pinta. Emilio ve sin abrir una terminal qué está pendiente, qué está haciendo
   cada agente y qué he verificado yo.
