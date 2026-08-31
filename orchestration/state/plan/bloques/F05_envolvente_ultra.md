---
id: F05
titulo: "Envolvente ULTRA: el motor de balas"
estado: PENDIENTE
depende_de: ["F04"]
desbloquea: ["F06"]
verificacion_global: "Distribución completa de resultados (mediana, p5, p95, probabilidad de ruina), nunca la media sola. Si ninguna base alcanza el objetivo, se reporta la cifra real."
actualizado: "2026-08-31"
---

# FASE 5 — ENVOLVENTE ULTRA: EL MOTOR DE BALAS

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

Antecedente (hallazgo 01, 2026-08-31): la envolvente NO puede salvar un edge inexistente — el
catálogo actual pierde a cualquier apalancamiento fuera de muestra. Esta fase queda sin materia
prima hasta que F03 produzca bases que superen el criterio 1.1.
