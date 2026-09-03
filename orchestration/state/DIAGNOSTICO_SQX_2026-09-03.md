# POR QUÉ TRES DÍAS Y MILES DE ESTRATEGIAS NO HAN DADO NINGUNA RENTABLE

> Diagnóstico del 2026-09-03, ordenado por el orquestador y ejecutado por seis agentes de solo
> lectura: tres investigadores y tres escépticos que intentaron tumbar sus conclusiones abriendo los
> ficheros citados. **16 de 17 hallazgos del bloque principal quedaron confirmados**; el único
> refutado era menor y está anotado abajo. Todo lo que sigue lleva su fichero y su línea.
>
> La pregunta de Emilio era: *"Si le pido a una IA una estrategia para el Nasdaq, en diez minutos me
> da una. Llevamos tres días con la mejor plataforma del mercado y cuatro o cinco mil estrategias, y
> ninguna sirve. Es imposible."* Tenía razón en que es imposible. La causa no es el mercado.

---

## La respuesta en una frase

**StrategyQuant nunca ha estado enchufado.** Ni una sola estrategia generada por SQX ha llegado
jamás a nuestro motor de validación, porque **el código que las conectaría no existe**. Lo que
llevamos tres días mirando no es un mercado difícil: es una fábrica que produce piezas y las apila
en un almacén que no tiene puerta al taller de al lado.

## Las cinco pruebas

**1. El puente SQX → motor propio no existe en el código.**
`grep` de `StrategyModel`, `strategy_lab` y `sqx_extracted` sobre
`services/validation/engine/event_backtest_engine.py` y sobre `scripts/mine.py` devuelve **cero
resultados** en los dos. `scripts/mine.py:47-52` importa únicamente sus propios generadores
(`UltraDiscoveryEngine`, `FundingDiscoveryEngine`) y escribe en la tabla `candidates`. Las
estrategias de SQX viven en otra tabla, `strategies`, que nadie cruza con aquélla. Son dos mundos que
no se tocan en ningún punto: ni en el código ni en la base de datos.

**2. Las 267 estrategias extraídas de SQX siguen todas en la casilla de salida.**
Consulta de solo lectura sobre la base canónica: **267 filas** con identificador `sqx:%`, y las 267
en estado `EXTRACTED_UNVERIFIED`. Cero en cualquier otro estado. Nunca ha avanzado ninguna.

**3. Aunque quisiéramos, hoy no podemos leer las reglas de una estrategia de SQX.**
`services/sqx_bridge/sqx_client.py:165-172`: la función que debería devolver el código de la
estrategia devuelve siempre, escrito a mano y sin preguntarle a SQX,
`SOURCE_RULES_UNAVAILABLE`, con el motivo *"sqcli HTTP API does not expose strategy source export"*.
El botón de la web que usa eso no puede tener éxito nunca. La tabla que vincularía una estrategia con
sus datos, `strategy_dataset_bindings`, tiene **0 filas**: ese camino no se ha recorrido jamás.

**4. El generador llevaba semanas apuntando al sitio equivocado y aceptando cero.**
`orchestration/ops/systemd/sqx.service.d-override.conf:5-9`, escrito el 01-09:
*"sqcli sostiene 113-116 % de CPU y 4,3 GB de RAM de forma continua, y el 2026-09-01 llevaba 37
ciclos de build con «Aceptado: 0» — es decir, consumía la mitad de la máquina sin producir una sola
estrategia utilizable, porque su configuración apunta a un único símbolo (AUDUSD_H1) con un OOS del
0,3 %."* **AUDUSD**: un par de divisas. No es ninguno de los activos de fondeo. Y con un fuera de
muestra del 0,3 %, que es decorativo.

**5. Hay 59 estrategias marcadas como verificadas que no tienen ni un backtest detrás.**
59 filas de familia `sqx_extracted` en estado `BACKTEST_VERIFIED` (58) y `CERTIFIED_CURRENT` (1). La
tabla `backtests` de toda la base de datos tiene **0 filas**. Una de ellas trae
`"dataset_hash": "ds_SI_1h"`, que no es una huella real, y `"trades_is": 0`. Son etiquetas puestas
sin evidencia: exactamente lo que la doctrina del proyecto prohíbe.

## Lo que sí funciona

No todo está roto, y conviene decirlo:

- El puente **habla de verdad** con SQX: `sqx_client.py` manda comandos reales por HTTP y la
  extracción de estrategias funciona (de ahí las 267 filas). No es una simulación.
- La página de Generación de la web está enchufada a rutas reales, no a datos de adorno.
- `improve_cycle.sh` es una máquina de estados de cuatro fases bien construida, con candado
  anti-solapamiento. El problema no es el script: es a qué mercado apunta y qué se hace después.

## Lo que esto significa para la pregunta de Emilio

Las cifras que veíamos no medían lo que creíamos:

| Lo que parecía | Lo que era |
| :--- | :--- |
| "Miles de estrategias y ninguna rentable" | Miles de estrategias que **nunca se han probado** con nuestro criterio |
| "SQX lleva tres días trabajando" | SQX llevaba semanas minando **AUDUSD en una hora**, no los activos de fondeo |
| "El mercado está muy competido" | El mercado no ha llegado a opinar todavía |
| "Tenemos 59 estrategias verificadas" | 59 etiquetas sin un solo backtest detrás |

La única campaña que sí midió algo de verdad fue la nuestra, la del motor propio: 840
configuraciones en ES 5m y 15m, todas muertas en la primera criba. Y ahí encontramos el bug de la
comisión (se cobraba a los micros la tarifa del contrato completo, 3,80 USD de más por operación),
que sigue sin corregir y que hundía a veinte configuraciones que tenían ventaja real antes de costes.

## Dos decisiones que no puede tomar un agente

**1. La licencia caduca en dos días.** `orchestration/results/I1_sqx_hallazgos.md:52-65`: la del PC es
*"Trial license - valid until 05.09.2026"*. La de Oracle expiró el 18-08. En el Hetzner se acaba de
instalar. **No hay ninguna licencia de pago confirmada en ninguna de las tres máquinas.** Todo el
carril de generación depende de eso, y la ventana se cierra el 5 de septiembre.

**2. Qué camino se toma para conectar SQX con la validación.** Hay dos, y son muy distintos:

- **Camino A, exportar y revalidar**: sacar las estrategias de SQX en un formato que podamos leer
  (fichero `.sqx`, XML o CSV de reglas), traducirlas a nuestro formato y pasarlas por nuestro motor y
  los once controles. Es el camino honesto y el que estaba planeado (tarea W3.3 del plan de fondeo),
  pero hoy está bloqueado porque la interfaz automática de SQX no expone las reglas. Habría que usar
  la exportación de la aplicación gráfica.
- **Camino B, confiar el filtro a SQX**: usar las pruebas de robustez del propio SQX (Monte Carlo,
  walk-forward, permutación de parámetros, contraste en otros mercados) como criba, y que nuestro
  motor solo certifique lo que sobreviva. Más rápido, pero nos apoyamos en el modelo de costes de SQX,
  que hay que configurar bien para micros CME.

Lo sensato es **B primero para tener caudal, y A en paralelo** para no depender de una caja negra. La
investigación externa sobre cómo se usa bien SQX está en marcha y aportará los ajustes concretos.

## Lo que se refutó

Un único hallazgo cayó: se afirmaba que cinco scripts de `services/sqx_bridge/` no los importa nadie
y solo aparecen en tests. El escéptico comprobó que **es falso para cuatro de los cinco**. Queda
anotado para no repetirlo.

## De dónde sale esto

Investigación de solo lectura del 2026-09-03, con tres lectores y tres escépticos independientes
sobre el repositorio y la base canónica. Ningún fichero fue modificado. Las consultas a la base de
datos fueron `SELECT` y `PRAGMA`. El detalle completo, con las citas literales, está en el registro
del flujo de trabajo `wf_1a27cdfb-e0c`.
