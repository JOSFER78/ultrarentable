# DSL de estrategias v0.1

## Objetivo

Permitir generación automática segura y reproducible. Ningún agente puede inyectar Python arbitrario.

## Secciones

```yaml
meta: {}
market: {}
features: []
entries: {}
exits: {}
position: {}
execution: {}
```

## Gramática conceptual

```text
EXPR := AND(EXPR...) | OR(EXPR...) | NOT(EXPR)
      | GT(VALUE, VALUE) | LT(VALUE, VALUE)
      | CROSS_ABOVE(VALUE, VALUE) | CROSS_BELOW(VALUE, VALUE)

VALUE := PRICE(field)
       | CONST(number)
       | INDICATOR(name, params)
       | ROLLING(op, source, period)
       | FEATURE(name)
```

## Operadores MVP

- SMA, EMA, RSI, ATR, ROC, Bollinger, highest, lowest.
- Retorno, rango, volumen relativo y volatilidad realizada.
- Cross, comparación, AND, OR y NOT.
- Entradas market/limit simplificada.
- Stop, target, trailing, time exit y señal opuesta.
- Apalancamiento fijo o por regla.
- Allocation, compound y piramidación.

## Límites técnicos, no financieros

- profundidad máxima del AST;
- tipos válidos;
- ausencia de ciclos;
- indicadores con warmup definido;
- parámetros dentro de rangos computables;
- determinismo.

Estos límites evitan estrategias inválidas, no reducen riesgo económico.
