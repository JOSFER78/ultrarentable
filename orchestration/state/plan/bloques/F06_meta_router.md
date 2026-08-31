---
id: F06
titulo: "Meta-estrategias ULTRA: el router"
estado: PENDIENTE
depende_de: ["F05"]
desbloquea: ["F08"]
verificacion_global: "La curva del router debe batir a la media de sus componentes en winrate Y en drawdown; si no, fracaso explícito y se descarta."
actualizado: "2026-08-31"
---

# FASE 6 — META-ESTRATEGIAS ULTRA: EL ROUTER

Que un conjunto funcione **como una sola estrategia**, con router dinámico multi-activo y debate
IA, **sin reglas hardcodeadas**.

- Decide asignación por ventana según: régimen detectado, correlación viva entre componentes y
  estado de cada bala.
- **Debate IA:** varios agentes proponen asignación y se critican; la decisión **y su
  razonamiento** quedan persistidos y son auditables a posteriori.
- **Criterio de éxito duro:** la curva del router debe batir a la media de sus componentes en
  winrate **y** en drawdown. Si no lo hace, se declara fracaso explícito y se descarta.
- El router **nunca** puede saltarse los límites 70 %/80 %.
