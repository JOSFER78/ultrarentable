---
id: F05
titulo: "Envolvente ULTRA: el motor de balas"
estado: PENDIENTE
depende_de: ["F04"]
desbloquea: ["F06"]
verificacion_global: "Distribución completa de resultados (mediana, p5, p95, probabilidad de ruina), nunca la media sola. OBJETIVO SELLADO (decisión #5): ~100 % mensual (miles % anuales) medido sobre la MEDIANA. Si ninguna base alcanza el objetivo, se reporta la cifra real."
aparcado: true
motivo_aparcado: "Foco 100% en FONDEO por orden de Emilio (2026-09-01). Estado congelado en orchestration/state/PUNTO_GUARDADO_ULTRA.md"
actualizado: "2026-09-01"
---

# FASE 5 — ENVOLVENTE ULTRA: EL MOTOR DE BALAS

> **APARCADO — no es abandono.** Emilio ordenó el 2026-09-01 centrar el 100 % del
> trabajo en FONDEO y sus meta-estrategias, y dejar ULTRA guardado para más adelante.
> Nada de esta fase se descarta ni se borra: el estado completo, con lo hecho y lo que
> faltaba, está congelado en `orchestration/state/PUNTO_GUARDADO_ULTRA.md`. Se retoma
> cuando FONDEO tenga estrategias certificadas.

> **Aquí nacen los miles de %.** Todo lo anterior era para tener bases que merezcan la pena.

Parámetros sellados: DD realizado **70 %** · flotante **80 %** · apalancamiento **hasta 500x**
gestionado por IA con cap real del exchange · dimensionamiento **100 % en porcentajes** ·
arranque **100 % paper**.

- **Máquina de estados de la bala:** INICIO → CONFIRMACIÓN → CRECIMIENTO → COSECHA → PROTECCIÓN →
  CIERRE. Todo en % del capital, nunca en cifras absolutas.
- **Piramidación free-risk:** se añade sobre ganadoras, break-even tras +1,5R.
- **Extensión a swing (decisión #24):** una operación intradía que va favorable **puede**
  mantenerse más allá del cierre de sesión y convertirse en swing (`1D`). El umbral de "va
  favorable" lo encuentra la optimización — **jamás una constante hardcodeada**. Exige modelar
  gaps de apertura y riesgo overnight en el backtest. En FONDEO esta extensión está PROHIBIDA.
- **Reciclaje:** el capital de balas cerradas realimenta balas nuevas.
- **Autoinversión de margen flotante:** la ganancia no realizada financia exposición adicional,
  con la liquidación real como límite duro.
- **Bóveda ratchet:** 50-85 % de lo cosechado sale a spot y **no vuelve a entrar jamás**.
- **Gestor dinámico de apalancamiento:** decide el multiplicador por operación según régimen,
  volatilidad y estado de la bala, con techo en el máximo real del par.

**Verificación, y es la fase más importante de todo el plan:**

- Backtest de la envolvente sobre las bases de la Fase 4, con la fricción de la Fase 2.
- Reportar la **distribución completa** de resultados, no la media: mediana, percentil 5,
  percentil 95, y **probabilidad de ruina**. Un sistema que da 3.000 % de media con 40 % de
  probabilidad de perderlo todo hay que decirlo así.
- **Si ninguna base alcanza el objetivo, se reporta la cifra real alcanzada.** Ajustar costes,
  datos o gates para llegar al número es violación grave de la doctrina.

## OBJETIVO DE RENTABILIDAD — SELLADO (Emilio, 2026-08-31)

El plan v4 heredó "miles de %" como **prosa sin umbral verificable**: la cifra concreta vivía
sólo en la decisión #5 de `DOCTRINA_ORQUESTADOR.md:81` y se perdió al reescribir el plan. Con
ello, ninguna comprobación automática podía decir si una estrategia cumple el objetivo — el
criterio 1.1 mide robustez (≥200 trades OOS, PF ≥1,25, OOS/IS ≥0,5, 11 gates, DSR,
persistencia) pero **no mide rentabilidad**. Tal cual, el sistema podía certificar como buena
una estrategia robusta que rindiera un 4 % anual. Queda restaurado y sellado:

**ULTRA debe alcanzar ~100 % mensual (miles % anuales), decisión #5.**

**Cómo se verifica (obligatorio):**

1. Sobre la **mediana** de la distribución de la envolvente, jamás sobre la media: en
   distribuciones con cola derecha gorda —que es exactamente lo que produce el motor de
   balas— la media la fija un puñado de trayectorias afortunadas y no representa el resultado
   esperable.
2. Acompañado SIEMPRE de **p5, p95 y probabilidad de ruina**. Un sistema con 3.000 % de
   mediana y 40 % de probabilidad de ruina se reporta así, con las dos cifras juntas.
3. Este umbral es un filtro **POSTERIOR** al criterio 1.1, no lo sustituye ni lo relaja: una
   estrategia debe pasar 1.1 (que sigue SELLADO) **y además** llegar al objetivo con la
   envolvente aplicada.
4. **Si ninguna base alcanza el objetivo, se reporta la cifra real.** Ajustar costes, datos o
   gates para llegar al número es violación grave de la doctrina.

**Ojo al orden causal:** el objetivo NO se le exige a la señal desnuda. Una base con PF 1,3 y
30 % anual es materia prima legítima; el ~100 % mensual se le exige al conjunto
`base × envolvente de balas`. Confundir ambos llevaría a descartar bases buenas por no ser
espectaculares por sí solas, que es justo el error que la tesis del plan quiere evitar.

Antecedente (hallazgo 01, 2026-08-31): la envolvente NO puede salvar un edge inexistente — el
catálogo actual pierde a cualquier apalancamiento fuera de muestra. Esta fase queda sin materia
prima hasta que F03 produzca bases que superen el criterio 1.1.
