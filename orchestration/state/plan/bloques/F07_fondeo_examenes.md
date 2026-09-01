---
id: F07
titulo: "FONDEO: pasar exámenes en 3-8 días"
estado: PENDIENTE
depende_de: ["F03"]
desbloquea: ["F08"]
verificacion_global: "Ranking con días esperados hasta pasar y probabilidad de quiebre por estrategia, por Monte Carlo sobre operaciones reales. OBJETIVO SELLADO: >=20 % mensual SOSTENIBLE sobre la mediana de la distribución, con P(romper cuenta) acotada."
actualizado: "2026-09-01"
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

## OBJETIVO DE RENTABILIDAD — SELLADO (Emilio, 2026-08-31)

Hasta hoy este bloque sólo fijaba un objetivo de **velocidad** (3-8 días, decisión #11). El
objetivo de **rentabilidad** que el usuario persigue no estaba escrito en ninguna parte del
plan, con lo que era inauditable. Queda sellado así:

**FONDEO debe alcanzar ≥ 20 % mensual SOSTENIBLE.**

"Sostenible" no es adorno: es la métrica que manda. Ante el conflicto entre maximizar el ROI
por cartucho y mantener viva la cuenta, **manda la rentabilidad mensual sostenible** (decisión
del usuario, 2026-08-31). El sistema venía optimizando ROI por cartucho, que es otra cosa y
lleva a estrategias distintas.

**Cómo se verifica (obligatorio, no negociable):**

1. Sobre la **distribución completa** por Monte Carlo remuestreando operaciones reales, nunca
   sobre la media: se reportan **mediana, p5, p95 y P(romper cuenta)**.
2. El umbral del 20 % mensual se mide sobre la **mediana**, no sobre la media (la media la
   inflan las colas derechas y miente en distribuciones asimétricas).
3. **`P(romper cuenta) ≤ 20 %` en horizonte de 6 meses.** Una estrategia que rinda 40 %
   mensual con 60 % de probabilidad de reventar la cuenta NO cumple: no es sostenible.
   (Umbral propuesto por el orquestador; ajustable por el usuario, pero debe existir un techo
   explícito o "sostenible" no significa nada.)
4. **Si ninguna estrategia alcanza el objetivo, se reporta la cifra real alcanzada.** Ajustar
   costes, datos, reglas de la firma o gates para llegar al número es violación grave de la
   doctrina, igual que en F05.

**Precedente que obliga a la cautela:** el único resultado histórico de examen daba
`p_pasar` 36,3 % con **`p_romper_cuenta` 63,6 %**, y además estaba calculado con un simulador
que tenía el límite de pérdida diaria roto (ver más abajo). Con el bug corregido, el riesgo
medido de romper cuenta pasó de **0,27 % a 48,9 %** en el escenario de control: el sistema
llevaba infraestimando el riesgo de ruina por dos órdenes de magnitud.

**Deuda técnica que bloquea la medición honesta de este objetivo:** F02.3 (trailing DD
intradiario sobre equity FLOTANTE, pérdida diaria, consistencia y cierre de sesión dentro del
motor de backtest). Hoy el examen se mide sobre PnL realizado operación a operación, que es
precisamente el error que revienta cuentas reales: la excursión adversa DENTRO de un trade no
se ve.

Antecedente: el resultado de `fondeo_examen.py` del 31-08 (`UR_FONDEO_CL_1H`, P(pasar)=36,3 %,
ROI cartucho +1.147 %) quedó **formalmente invalidado** por el hallazgo 02 (falta de
`point_value`); hay que rehacerlo con candidatas certificadas por el motor ≥ 5.6.0.

## Actualización 2026-09-01 — el examen ya no miente sobre la ruina, pero todavía no decide con la verdad

Lo corregido y verificado:

- El **límite de pérdida diaria no se aplicaba nunca**: `pnl_dia += 0.0` hacía que la condición
  `pnl_dia < 0` fuera siempre falsa, y además se comparaba la pérdida acumulada contra el límite
  diario. Con el arreglo, la P(romper cuenta) medida pasa de **0,27 % a 48,9 %**: el riesgo estaba
  subestimado unas 180 veces.
- El **ritmo de operaciones se asumía** (60 días fijos) en vez de deducirse de la duración real de
  la serie. Ahora se deriva de `duration_info` y, si no está, el resultado es `NO_EVALUABLE`.
- Se añade selección de firma desde `PROP_FIRM_CATALOG` y la regla de consistencia.

**Hueco abierto y grave, declarado sin disimular**: el motor sabe evaluar las reglas de prop firm
sobre equity **flotante** desde la release 5.15.0, y el examen ya sabe invocarlo
(`reejecutar_examen_barra_a_barra()`), pero **ese resultado no gatea nada**. Las dos fases del
examen siguen decidiendo "CUMPLE" con el bootstrap sobre PnL ya cerrado, que es ciego a la
excursión adversa intradía. Hoy es inerte porque hay 0 candidatas FONDEO certificadas, pero en
cuanto exista la primera, el script podrá declarar "CUMPLE" para una cuenta que la propia
verificación honesta marca como `prop_firm_busted=True`.

Es exactamente el tipo de fallo que la doctrina prohíbe: un número optimista donde debería haber
un fallo cerrado. **Cerrar esto es condición previa a certificar ninguna estrategia de fondeo**, no
un pulido posterior.
