# Cómo funciona el ciclo, y qué pasa cuando nadie mira

Emilio, 2026-09-03: *"¿estás pendiente? ¿tienes un sistema de estar esperando trabajos de AGY para
revisar? Tiene que tener una organización."*

Esto es esa organización, escrita para que no dependa de que yo la recuerde.

## Las cuatro piezas

| Pieza | Dónde vive | Qué hace |
| :--- | :--- | :--- |
| **El tablero** | `orchestration/tablero/<ID>.md`, uno por tarea | La única fuente de verdad. Nada se coordina por chat |
| **El buzón** | `orchestration/tablero/BUZON.md` | Mensajes del orquestador a AGY, lo nuevo al final |
| **El vigilante** | Proceso del orquestador | Avisa en segundos de cualquier cambio de `estado:` |
| **La web** | `/plan`, pestaña "Tareas AGY" | Lo mismo, para que Emilio lo vea sin abrir ficheros |

## El ciclo, paso a paso

1. **El orquestador escribe la tarea.** Un fichero con: por qué existe (con las mediciones que la
   justifican), qué hacer, el bloque de aceptación (comandos exactos), qué está prohibido, y el
   ámbito de ficheros que puede tocar. Estado `PENDIENTE`. Además deja un aviso en el buzón.
2. **AGY la coge.** Pone `EN_CURSO` y guarda. **Guardar es el aviso**: no hay que mandar nada.
3. **AGY entrega.** Rellena el parte con la salida cruda de cada comando y pone `ENTREGADO`.
4. **El vigilante despierta al orquestador** con el cambio de estado, en segundos.
5. **El orquestador verifica re-ejecutando él mismo** los comandos de la aceptación. No se cree el
   parte: lo comprueba. Si cuadra, `VERIFICADO` y se commitea. Si no, `DEVUELTO` con la lista
   concreta de correcciones y la evidencia de por qué.
6. **Vuelta al 2.** Las devueltas van antes que las nuevas.

## Qué NO es una espera

El orquestador **nunca se queda parado** esperando a AGY, ni AGY esperando al orquestador. Mientras
AGY programa, el orquestador trabaja en los servidores, escribe las siguientes tareas y verifica lo
que va llegando. Ese fue el error del 02-09, cuando AGY se quedó diez minutos esperando una auditoría
que dependía del servidor: por eso el trabajo de servidor es del orquestador y el de código y web es
de AGY, y ninguna tarea puede depender de que el otro conteste.

## Estados, y qué significa cada uno

| Estado | Quién lo pone | Qué quiere decir |
| :--- | :--- | :--- |
| `BORRADOR` | Orquestador | Se está escribiendo. Para AGY no existe |
| `PENDIENTE` | Orquestador | Lista para coger |
| `EN_CURSO` | AGY | La está haciendo |
| `ENTREGADO` | AGY | Esperando verificación |
| `VERIFICADO` | Orquestador | Cerrada y commiteada |
| `DEVUELTO` | Orquestador | Vuelve con correcciones concretas. **Prioridad sobre las nuevas** |
| `BLOQUEADO` | AGY | Falta una decisión o un dato que AGY no puede conseguir |

## El punto débil, dicho claramente

**El vigilante vive dentro de la sesión del orquestador.** Si esa sesión se cierra, deja de avisar.
No se pierde nada (el tablero está en disco y en el repositorio), pero **nadie verifica hasta que la
sesión vuelve**. Cuando eso pasa, lo primero que hace el orquestador al arrancar es mirar qué hay en
`ENTREGADO` y ponerse con ello.

Lo que **sí** sobrevive a todo, porque son servicios del sistema con reinicio automático:

| Servicio | Máquina | Qué mantiene vivo |
| :--- | :--- | :--- |
| `sqx-headless` | Hetzner | StrategyQuant |
| `m1-runner` | Hetzner | El bucle de las 40 celdas |
| `m1-estado` | Hetzner | Publica el estado de la rejilla |
| `ultrarentable-supervisor` | Hetzner | Vigila las tres de arriba y las levanta |
| `ultrarentable-backfill-40` | Oracle | La descarga de los activos que faltan |

Es decir: **la fábrica no para aunque no haya nadie delante**. Lo que se detiene sin orquestador es
la revisión del trabajo de AGY, no la generación de estrategias.

## Qué hace Emilio cuando ve el tablero parado

1. Si hay tareas en `PENDIENTE` o `DEVUELTO` y AGY no las coge, pegarle el prompt de
   `PROMPT_AGY.md`. AGY solo trabaja mientras esté arrancado.
2. Si hay algo en `ENTREGADO` durante mucho rato, es que el orquestador no está: decírselo al
   arrancar la sesión y lo verifica.
3. Si algo no cuadra, escribirlo en `/plan`, pestaña Comentarios. Va a
   `COMENTARIOS_EMILIO.md`, que leen los dos.
