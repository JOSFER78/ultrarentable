# Barreras contra resultados falsos

No son filtros de riesgo; son requisitos de verdad experimental.

- Prohibir look-ahead y accesos a índices futuros.
- Lagar máximos/mínimos de breakout cuando corresponda.
- Warmup separado del periodo evaluado.
- Timestamps UTC y calendario uniforme.
- Comisiones y funding debitados en el momento correcto.
- Redondeo de tamaño/precio como el exchange.
- No rellenar órdenes limit si la vela solo toca sin volumen/modelo suficiente.
- Separar mark, index y last price cuando existan datos.
- Pruebas de invariantes contables.
- Golden tests con pequeños escenarios manuales.
- Comparación diferencial fast-engine vs canonical-engine.
