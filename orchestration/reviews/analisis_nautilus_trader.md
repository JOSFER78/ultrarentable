# ¿Hace falta NautilusTrader? — Análisis con evidencia física

**Hermes · 2026-08-31 · Pregunta del usuario: "antes utilizaba nautilus trader de backtest, ¿es necesario? ¿es lo mejor?"**

## Primer hecho: NautilusTrader NO está instalado

```
$ python3 -c "import nautilus_trader"
ModuleNotFoundError
```

Y sin embargo el repo tiene `gate_11_nautilus_event.py`, `nautilus_gate_engine.py`,
`cross_engine_reconciler.py`, una página `/nautilus` y referencias en 9 ficheros.

`nautilus_gate_engine.py` **solo importa numpy**. Es una reimplementación propia en Python puro
—simulación de márgenes, distancia a liquidación, funding— que lleva el nombre de Nautilus sin
serlo. Es código real y hace un trabajo real, pero **el nombre miente**: es el mismo patrón que
`/api/v2/validation` anunciando gates que no se ejecutan.

## Segundo hecho: el motor actual es POR BARRAS

`event_backtest_engine.py` resuelve las salidas con `bar_high >= take_profit_price`. Es OHLC puro,
no ticks. **Punto a su favor:** comprueba el stop ANTES que el take profit (`elif`), o sea que ante
la ambigüedad intrabarra asume lo peor. Eso es honesto y es la práctica correcta.

## Qué aporta NautilusTrader de verdad

Motor Rust-nativo, determinista y orientado a eventos. Su característica diferencial es la
**paridad research-to-live**: el `NautilusKernel` es el mismo en `BacktestEngine` y en `LiveNode`,
compartiendo mensajería, orden de eventos, manejo del tiempo, riesgo y ejecución. La misma
estrategia corre en backtest y en real con la misma semántica.

Eso ataca directamente el requisito del usuario: *"que se parezcan lo máximo posible cuando se
ejecuten en real"*.

## Veredicto: no ahora, imprescindible después

### No ahora
- El cuello de botella no es la fidelidad del backtest: es **tener candidatas**. Hoy hay 6
  certificadas 11/11, conseguidas hace minutos tras arreglar 4 bugs del pipeline.
- Migrar implica reescribir todas las estrategias a la API de Nautilus más cadena de Rust en un
  VPS de 4 cores. Semanas de trabajo que no producen ni una estrategia más.
- El motor actual, siendo por barras, es **conservador** en la ambigüedad intrabarra.

### Imprescindible para ULTRA en la Fase 5, y esto no es negociable
**Un backtest por barras con apalancamiento alto no es defendible.** A 100x o más el precio de
liquidación queda pegadísimo a la entrada, y dentro de una sola vela pueden tocarse tanto la
liquidación como el take profit. Un motor OHLC **no puede saber cuál ocurrió primero**. La
diferencia entre "+5R" y "bala liquidada" se decide justo ahí.

Comprobar el stop antes que el TP mitiga, pero no modela liquidación intravela ni funding a
apalancamiento alto.

### La vía intermedia, que es la que recomiendo
En vez de migrar todo a Nautilus, **añadir una etapa de confirmación a nivel de tick** solo para
las candidatas ULTRA que superen los 11 gates. Motivos:
1. **Ya tengo los ticks.** El ingestor Dukascopy baja bid/ask reales tick a tick — es exactamente
   la materia prima que hace falta.
2. Se aplica a un puñado de finalistas, no a las decenas de miles de configuraciones de la
   campaña. El coste computacional es asumible en 4 cores.
3. No obliga a reescribir la generación de estrategias.

Si esa etapa revela divergencias grandes frente al backtest por barras, **entonces** sí se
justifica migrar a Nautilus, con un dato que lo respalde en vez de por intuición.

## Acción inmediata (no ejecutada)
Renombrar `gate_11_nautilus_event` y `nautilus_gate_engine` a algo que describa lo que hacen
(p. ej. `gate_11_microestructura_margen`), o instalar Nautilus de verdad y usarlo. Mantener el
nombre actual es afirmar una validación cruzada contra un motor externo que no existe.

## Fuentes
- https://nautilustrader.io/docs/latest/concepts/backtesting/
- https://github.com/nautechsystems/nautilus_trader
