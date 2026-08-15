# Búsqueda y evolución

## Pipeline

```text
Seed population
 -> compile DSL
 -> fast backtest
 -> retain top-K survivors
 -> canonical backtest
 -> rank canonical survivors
 -> mutate/crossover
 -> inject novel/random candidates
 -> next generation
```

## Selección Kamikaze

```python
valid = reproducible and not simulation_error
survivor = valid and not liquidated and final_equity > 0
rank_key = terminal_multiple
```

## Mantener diversidad sin filtrar riesgo

La diversidad evita que toda la población se convierta en copias del mismo ganador. No penaliza drawdown. Se mantienen nichos por:

- familia de señal;
- dirección long/short;
- frecuencia de operación;
- árbol DSL;
- ventana donde produce el máximo;
- estilo de salida;
- rango de apalancamiento.

## Operadores evolutivos

- Mutación de constante.
- Sustitución de indicador.
- Inserción/eliminación de condición.
- Cambio AND/OR.
- Mutación de salida.
- Mutación de leverage/allocation.
- Mutación de piramidación.
- Cruce por subárbol.
- Cruce entre entrada y gestión de otra estrategia.

## Búsqueda por capas

1. señal sin gestión compleja;
2. salidas;
3. leverage y allocation;
4. compound y piramidación;
5. activadores de régimen.

Esta separación permite saber dónde aparece el multiplicador extremo.
