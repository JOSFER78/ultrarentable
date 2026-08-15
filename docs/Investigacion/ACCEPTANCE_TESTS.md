# Pruebas de aceptación

## Backtester

- Mismo input produce mismos outputs byte a byte en summaries.
- Equity contable coincide con cash + unrealized PnL - costes.
- Una liquidación manual conocida ocurre en el timestamp esperado.
- Funding positivo/negativo se aplica correctamente.
- Stop y target simultáneos respetan política intrabar.
- No existe acceso futuro en indicadores.

## DSL

- Rechaza referencias desconocidas.
- Detecta ciclos.
- Produce hash estable.
- Compila la misma estrategia en ambos motores.

## Orquestación

- Un job repetido no duplica resultados.
- Un worker caído reanuda desde checkpoint.
- La campaña puede pausar/reanudar.
- El ranking solo usa resultados canónicos cuando se solicita ranking final.

## Producto

- Crear campaña completa desde UI.
- Ver líder nuevo en tiempo real.
- Exportar paquete reproducible.
