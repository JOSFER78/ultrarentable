---
id: F08
titulo: "Verificación end-to-end y paper"
estado: PENDIENTE
depende_de: ["F06", "F07"]
desbloquea: ["F09"]
verificacion_global: "Reconciliación paper vs backtest medida y realimentada. Ni un euro real sin autorización explícita del usuario."
actualizado: "2026-08-31"
---

# FASE 8 — VERIFICACIÓN END-TO-END Y PAPER

- ULTRA en paper BingX con el motor de balas real; FONDEO en demo Tradovate.
- **Reconciliación paper vs backtest:** los fills reales vuelven al sistema y se mide la
  divergencia contra lo que el backtest predijo. **Esto es lo único que demuestra que el backtest
  se parece al real.** No se garantiza a priori: se mide y se realimenta.
- Estrategia que diverja por encima del umbral ⇒ se marca y sale de producción.
- **Ni un euro real sin autorización explícita del usuario.**
