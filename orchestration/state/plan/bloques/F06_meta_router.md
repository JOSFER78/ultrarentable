---
id: F06
titulo: "Meta-estrategias ULTRA: el router"
estado: PENDIENTE
depende_de: ["F05"]
desbloquea: ["F08"]
verificacion_global: "La curva del router debe batir a la media de sus componentes en winrate Y en drawdown; si no, fracaso explícito y se descarta."
aparcado: true
motivo_aparcado: "Foco 100% en FONDEO por orden de Emilio (2026-09-01). Estado congelado en orchestration/state/PUNTO_GUARDADO_ULTRA.md"
actualizado: "2026-09-01"
---

# FASE 6 — META-ESTRATEGIAS ULTRA: EL ROUTER

> **APARCADO — no es abandono.** Emilio ordenó el 2026-09-01 centrar el 100 % del
> trabajo en FONDEO y sus meta-estrategias, y dejar ULTRA guardado para más adelante.
> Nada de esta fase se descarta ni se borra: el estado completo, con lo hecho y lo que
> faltaba, está congelado en `orchestration/state/PUNTO_GUARDADO_ULTRA.md`. Se retoma
> cuando FONDEO tenga estrategias certificadas.

Que un conjunto funcione **como una sola estrategia**, con router dinámico multi-activo y debate
IA, **sin reglas hardcodeadas**.

- Decide asignación por ventana según: régimen detectado, correlación viva entre componentes y
  estado de cada bala.
- **Debate IA:** varios agentes proponen asignación y se critican; la decisión **y su
  razonamiento** quedan persistidos y son auditables a posteriori.
- **Criterio de éxito duro:** la curva del router debe batir a la media de sus componentes en
  winrate **y** en drawdown. Si no lo hace, se declara fracaso explícito y se descarta.
- El router **nunca** puede saltarse los límites 70 %/80 %.
