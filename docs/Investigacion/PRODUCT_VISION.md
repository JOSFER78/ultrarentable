# Visión de producto

## Qué se construye

Un laboratorio autónomo que busca estrategias de rentabilidad extraordinaria en mercados perpetuos, aprende de cada prueba y conserva estrategias especializadas incluso si solo funcionan en ventanas o regímenes concretos.

No se busca una estrategia universal, suave o institucional. Se buscan distribuciones convexas: muchas estrategias mueren y unas pocas producen multiplicadores extremos.

## Regla innegociable del modo Kamikaze

No se descarta por:

- drawdown;
- volatilidad de equity;
- Sharpe o Sortino;
- número reducido de operaciones;
- concentración de beneficios;
- estabilidad entre ventanas;
- fragilidad paramétrica.

Solo se invalida por liquidación total, equity no positiva, error de simulación o falta de reproducibilidad.

## Distinción crítica

La ausencia de filtros financieros no autoriza un backtest falso. El sistema debe modelar correctamente:

- comisiones maker/taker;
- funding;
- spread y slippage;
- tamaño mínimo y precisión;
- margen inicial y de mantenimiento;
- liquidaciones;
- orden temporal de eventos;
- ambigüedad intrabar;
- latencia configurable.

## Resultado deseado

Una biblioteca de estrategias etiquetadas por:

- mercado y temporalidad;
- familia de señal;
- ventana/regímenes donde sobrevivió;
- multiplicador máximo, mediano y mínimo observado;
- linaje evolutivo;
- condiciones de activación potenciales;
- fidelidad del nivel de backtest alcanzado.
