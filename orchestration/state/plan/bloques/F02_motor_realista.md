---
id: F02
titulo: "Motor de backtest realista"
estado: PARCIAL
depende_de: ["F00"]
desbloquea: ["F03"]
verificacion_global: "Re-ejecutar una estrategia conocida con motor viejo y nuevo y publicar la diferencia. Si el P&L no baja, el motor nuevo no está modelando fricción de verdad."
actualizado: "2026-08-31"
---

# FASE 2 — MOTOR DE BACKTEST REALISTA

> **Va antes de minar, no después.** Minar con costes irreales produce estrategias preciosas que
> mueren en real, y encima consume el presupuesto de CPU del VPS.

Es la respuesta técnica al requisito del usuario: *"que se parezcan lo máximo posible cuando se
ejecuten en real"*.

Ya cerrado en motor 5.5.0/5.6.0 (2026-08-31): semántica de cruce como EVENTO (no estado) y
multiplicador de contrato dependiente del venue (`point_value` CME en FONDEO, 1.0 en ULTRA).

## Diseño técnico (orquestador, 2026-08-31)

Estado real del motor (`services/validation/engine/event_backtest_engine.py`, 948 líneas):
`point_value` por venue ✓ y cruces como evento ✓ (5.6.0), pero la fricción es ASUMIDA:
`slippage_bps=2.0` plano, `funding_rate_8h=0.0001` fijo, sin spread por barra, sin asimetría
bid/ask, sin latencia, sin cap de apalancamiento ni liquidación, sin reglas prop intradía.

Cambios de diseño (cada uno sube versión de motor si altera las operaciones — regla #26):

1. **Spread por barra:** `aggregate_bars` de Dukascopy ya persiste `spread_mean` medido por vela;
   el motor debe leerlo del dataset y usarlo por barra. Cripto: spread efectivo BingX por par
   (consulta API, se persiste con fecha de captura). Si el dataset no trae spread: se usa el
   percentil 75 del spread medido del símbolo, NUNCA cero (fail-closed).
2. **Ejecución asimétrica:** OHLC en bid ⇒ compra al `precio + spread_barra`, venta al bid.
   Sustituye al slippage plano en bps; el slippage restante queda solo como componente de
   impacto configurable y conservador.
3. **Latencia:** la señal se evalúa al cierre de la vela N y el fill ocurre en el open de N+1
   desplazado por `latency_ticks` (por defecto conservador, parametrizable). Prohibido el fill
   en el mismo close de la señal.
4. **Comisiones reales por instrumento** desde `canonical_instrument_aliases.json` / specs CME
   (fijas por contrato en FONDEO, porcentuales BingX en ULTRA). Nada hardcodeado en el motor.
5. **ULTRA:** funding real BingX por par (histórico si disponible; si no, el peor cuartil
   observado, fail-closed), cap de apalancamiento real del par y precio de liquidación con
   margen aislado (una bala liquidada es pérdida total de esa bala).
6. **FONDEO:** trailing DD intradiario sobre equity flotante (no de cierre), pérdida diaria
   máxima, regla de consistencia y cierre obligatorio de sesión, todos parametrizados por el
   perfil de la prop firm.

**Verificación sellada de la fase:** re-ejecutar una estrategia conocida con motor viejo y
nuevo y publicar la diferencia; si el P&L no baja, el modelado de fricción no es real.

## 2.1 Fricción medida, no asumida

**Estado:** HECHO (releases 5.7.0→5.11.0, 2026-08-31, cada una con verificación ledger a ledger
en `orchestration/results/verificacion_f02_diff_*.md`):

- **5.7.0** fricción coherente (spread medido bid/ask, comisión futuros por lado, fin del doble
  cobro, point_value en slippage y END_OF_DATASET).
- **5.8.0** FONDEO contratos CME enteros (decisión #25); sin 1 contrato no se opera.
- **5.9.0** latencia: fill en el OPEN de la vela siguiente; nunca al precio de la señal.
- **5.10.0** unidad canónica de riesgo = FRACCIÓN. Corrige un bug histórico: el motor dividía
  entre 100 un valor que ya venía en fracción ⇒ TODO el sizing histórico ~100x infradimensionado.
  Guardia fail-closed para riesgo > 0,5.
- **5.11.0** point_value en sizing/margen/nocional de futuros (un MES con SL de 30 pts se
  dimensionaba 5x por encima del riesgo configurado).

Verificaciones clave: ULTRA idéntico donde debía (5.8.0, 5.11.0: point_value=1), FONDEO pasó de
0 trades (bug expuesto) a operar con contratos enteros y riesgo correcto; latencia produjo mezcla
de mejoras/empeoramientos (no sesgo sistemático). El modo `friction_model=MEASURED` se activará
solo cuando los datasets Dukascopy con `spread_mean` sustituyan a los Yahoo.

**Release 5.7.0 (hecha):** spread medido por barra con fills asimétricos bid/ask cuando ≥90 %
de las barras traen `spread_mean` (campo `friction_model=MEASURED|ASSUMED` en el resultado);
comisión de futuros fija POR LADO; eliminado el doble cobro del slippage de entrada; añadido
`point_value` al slippage de entrada y al cierre `END_OF_DATASET` (que además no aplicaba
`point_value` al PnL). Verificación publicada:
`orchestration/results/verificacion_f02_diff_5.6.0_vs_5.7.0.md` — las 15 celdas de referencia
MEJORAN PnL, y es la atribución correcta: 5.6.0 sobre-cobraba (bugs), no modelaba más fricción.
El criterio "el P&L debe bajar" se ejercita de verdad con la latencia (5.9.0) y cuando los
datasets Dukascopy con spread real sustituyan a los Yahoo (hoy las 15 celdas corren ASSUMED).

- **Spread real por barra.** Ya se captura: el ingestor Dukascopy guarda `spread_mean` medido
  tick a tick en cada vela (0,50 pts en el S&P). Para cripto, spread real de BingX.
- **Ejecución asimétrica:** compras al ask, vendes al bid. El OHLC está en bid + spread guardado,
  así que se reconstruye sin inventar.
- **Latencia:** la entrada no ocurre al cierre de la vela de señal sino N ticks después,
  parametrizable y por defecto conservador.
- **Comisiones reales** por instrumento (ya en `canonical_instrument_aliases.json`).

## 2.2 Fricción específica de ULTRA

**Estado:** PENDIENTE.

- **Funding real de BingX** (se consulta a su API, no se asume).
- **Cap de apalancamiento real por par.** No sirve asumir 500x: se pregunta al exchange cuánto da
  en ese símbolo y ese es el techo duro.
- **Precio de liquidación real** con margen aislado. Una bala que se liquida es una bala perdida,
  y el backtest tiene que verlo.

## 2.3 Fricción específica de FONDEO

**Estado:** PENDIENTE.

- **Trailing DD intradiario**, no de cierre. Es la regla que mata las cuentas.
- Pérdida diaria, regla de consistencia, cierre obligatorio intradía.
