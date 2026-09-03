# OBJETIVO ACTUAL — M1: exprimir StrategyQuant X

> Fijado por Emilio el 2026-09-03 02:35 UTC. Manda sobre cualquier otra prioridad que no sea
> seguridad. Mientras esto esté aquí, **solo se trabaja en M1**: generar. M2 y M3 vienen después.

## Lo que ha pedido, en sus palabras

> "Tu objetivo es usar SQX lo mejor posible. Recuerda: todos los activos de fondeo en 1m, 5m, 15m,
> 1h y 4h. Aprovecha la potencia. Y no te pongas tan exquisito con los filtros en SQX, piensa que
> luego vamos a depurar las estrategias, optimizándolas inteligentemente para fondeo. De momento
> solo trabajamos en el proceso M1. Cuando esté listo, pasamos las estrategias a M2 y de ahí a M3, y
> luego ya el bucle de las que no pasen a M2 de nuevo. Pero todo inteligentemente y usa el plan
> completo."

## Qué significa eso en decisiones concretas

**1. El embudo cambia de sitio.** Hasta ahora se le pedía a SQX que entregara estrategias casi
perfectas, y por eso no entregaba ninguna. A partir de ahora SQX **genera ancho** y el cribado duro
lo hace nuestro motor en M2 con el criterio 1.1, que es donde debe estar y donde hay evidencia
auditable. Filtros de SQX permisivos; nuestro criterio, intacto. Esto **no relaja el criterio 1.1**:
lo mueve al sitio correcto del embudo.

**2. La rejilla es de 25 celdas, no de dos.** Todos los activos de fondeo por los cinco marcos
temporales:

| Activo (ejecución en micro) | 1m | 5m | 15m | 1h | 4h |
| :--- | :-: | :-: | :-: | :-: | :-: |
| ES → MES (S&P 500) | ✓ | ✓ | ✓ | ✓ | ✓ |
| NQ → MNQ (Nasdaq) | ✓ | ✓ | ✓ | ✓ | ✓ |
| YM → MYM (Dow) | ✓ | ✓ | ✓ | ✓ | ✓ |
| GC → MGC (oro) | ✓ | ✓ | ✓ | ✓ | ✓ |
| CL → MCL (petróleo) | ✓ | ✓ | ✓ | ✓ | ✓ |

RTY/M2K queda fuera hasta tener datos: no hay proxy en Dukascopy, y así está decidido por escrito en
`PLAN_LOCAL_FONDEO.md` (W1.5). Antes de generar hay que saber qué celdas tienen datos reales: eso es
lo primero que se mide, no se supone.

**3. La potencia se usa.** El servidor dedicado tiene 8 hilos y 62 GB de memoria, y ahora mismo está
al 0,4 de carga usando 5 GB. La instalación de Oracle estaba estrangulada a 1,2 núcleos y 4 GB. Hay
margen para subir memoria y paralelismo mucho, y hay que medir cuánto de verdad rinde antes de dar
una cifra por buena.

**4. Nada se toca a ciegas.** Antes de cambiar una configuración de SQX se mide qué hay: qué permite
la licencia, qué filtros están puestos hoy, cuántas estrategias acepta por cada mil generadas. Hay
una sospecha documentada en el repositorio de que la configuración actual es **estéril por
construcción** (un mínimo de 20 operaciones por serie combinado con un máximo de 1 operación al día,
que juntos no pueden cumplirse). Si se confirma, explica tres días sin resultados mejor que
cualquier teoría sobre el mercado.

## El recorrido completo, para que nadie se pierda

```
M1  GENERAR         SQX produce estrategias en bruto, ancho, sobre las 25 celdas
      |             filtros permisivos; el objetivo es CAUDAL, no pureza
      v
M2  MEJORAR         nuestro motor las prueba con el criterio 1.1 y descarta con motivo
      |             las que casi pasan vuelven a M1/M2 con hipótesis, no con fuerza bruta
      v
M3  VALORAR         examen contra las reglas reales de una prop firm
      |
      v
M4  META            combinar las que sobrevivan para bajar la varianza
```

**Ahora mismo solo se trabaja en M1.** Nada de tocar M2, M3 ni M4 hasta que M1 entregue caudal.

## De dónde sale el detalle

- `PLAN_INVESTIGACION_PROFUNDA.md`, apartado **I1 "StrategyQuant X al 100 %"**: las nueve preguntas
  que hay que responder sobre SQX, escritas antes de esta sesión y nunca ejecutadas. Es el guion.
- `PLAN_LOCAL_FONDEO.md`, bloques **W1** (datos) y **W3.1-W3.3** (SQX en local, arreglar el Builder,
  puente SQX → motor propio).
- `orchestration/state/plan/bloques/F03_campana_descubrimiento.md`: la fase viva.
- `ARQUITECTURA_RECURSOS.md`: qué máquina hace qué.

## Criterio de "M1 listo"

M1 estará listo cuando, para cada celda con datos, exista un banco de estrategias generadas con
procedencia registrada (proyecto, banco, fecha, huella) y sepamos **cuántas** salen por hora y a qué
coste de máquina. No cuando sean buenas: eso lo dirá M2.
