---
id: F07
titulo: "FONDEO: pasar exámenes en 3-8 días"
estado: PENDIENTE
depende_de: ["F03"]
desbloquea: ["F08"]
verificacion_global: "Ranking con días esperados hasta pasar y probabilidad de quiebre por estrategia, por Monte Carlo sobre operaciones reales."
actualizado: "2026-08-31"
---

# FASE 7 — FONDEO: PASAR EXÁMENES EN 3-8 DÍAS

El problema inverso al de ULTRA: no maximizar, **sobrevivir a un examen**.

- **Simulador exacto de reglas prop:** trailing DD intradiario, pérdida diaria, consistencia,
  cierre obligatorio.
- **Optimizador:** maximizar `P(pasar en ≤ 8 días)` sujeto a `P(violación) < umbral`. La
  distribución se obtiene por Monte Carlo **remuestreando operaciones reales del backtest**,
  nunca retornos sintéticos.
- **Meta-fondeo:** combinar estrategias poco correlacionadas para bajar la varianza del examen.
  En fondeo, la varianza mata más que la media baja.
- **Salida:** ranking con días esperados hasta pasar y probabilidad de quiebre por estrategia.
- Export a **PickMyTrade + Tradovate** (ya configurado, esperando estrategias).
- La gestión de cuentas prop sigue **pospuesta** (decisión #10).

Antecedente: el resultado de `fondeo_examen.py` del 31-08 (`UR_FONDEO_CL_1H`, P(pasar)=36,3 %,
ROI cartucho +1.147 %) quedó **formalmente invalidado** por el hallazgo 02 (falta de
`point_value`); hay que rehacerlo con candidatas certificadas por el motor ≥ 5.6.0.
