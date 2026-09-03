---
titulo: "Cómo funcionan las fases: del plan a la minitarea y de vuelta"
actualizado: "2026-09-03"
---

# Cómo funcionan las fases

Escrito el 2026-09-03 por orden de Emilio, con sus palabras: *"plan, fases, encargos de fases por
minitareas a AGY, comprobación, análisis y finalizar fase; todo en código bien organizado y en el
front, y todo actualizado constantemente o de alguna manera automática en la página de plan"*. Y
antes: *"debes organizarte para tener un plan por fases… cuando acaba, verifica si ha acabado con
todo, si no lo rectifica; cuando ha acabado con todo, ya das por cerrada esa fase y empiezas la
siguiente"*.

## La cadena, de arriba abajo

```
PLAN  ──▶  FASE (F00…F10)  ──▶  MINITAREAS (A??.md, una por encargo)  ──▶  cierre de fase
             │                      │                                        │
             │                      ├─ AGY la ejecuta y pone ENTREGADO       │
             │                      └─ el orquestador la comprueba y firma   │
             │                         VERIFICADO (o la devuelve)            │
             └──────────── cuando TODAS están VERIFICADO ────────────────────┘
                              se audita la fase entera y se cierra
```

1. **El plan** son las once fases de `bloques/F00…F10`, con sus dependencias
   (`depende_de`, `desbloquea`) y su criterio de cierre (`verificacion_global`).
2. **Cada minitarea vive en una tarjeta** de `orchestration/tablero/A??.md` y **declara su fase** en
   la cabecera: `fase: F03`. Esa es la única fuente de la verdad; las fases **no** repiten la lista
   de sus tareas, porque dos listas de lo mismo acaban contradiciéndose.
3. **Minitarea quiere decir pequeña**: un ámbito de ficheros de un solo módulo y un criterio de
   aceptación que se comprueba con comandos. Si un encargo obliga a tocar tres zonas sin relación,
   está mal partido y se divide antes de mandarlo.
4. **El estado de la fase se calcula, no se escribe a mano.** Sale de sus tarjetas: si alguna está
   `DEVUELTO`, la fase no está "bien"; si todas están `VERIFICADO`, la fase está *lista para
   auditar*, que no es lo mismo que cerrada.
5. **La auditoría de cierre la hace el orquestador** contra el `verificacion_global` de la fase, no
   tarea por tarea: ¿está de verdad hecho lo que la fase prometía? Lo que falte se rectifica
   abriendo tarjetas nuevas **dentro de esa misma fase**.
6. **Solo entonces se cierra** y empieza la siguiente, siguiendo las dependencias.

## Dónde está cada cosa (para no duplicar nada)

| Qué | Dónde | Quién lo escribe |
| :--- | :--- | :--- |
| Las fases, su criterio de cierre y sus dependencias | `orchestration/state/plan/bloques/F??.md` | Orquestador |
| Las minitareas, con su `fase:` y su parte de entrega | `orchestration/tablero/A??.md` | Orquestador (la tarea) y AGY (el parte) |
| El estado de cada fase | **se calcula** de las tarjetas | Nadie: se deduce |
| Lo que ve Emilio | `/plan` | La web, leyendo los dos de arriba |

## El reparto de hoy (2026-09-03)

| Fase | Qué es | Minitareas |
| :--- | :--- | :--- |
| **F02** | Motor de backtest realista | 2 de 2 verificadas |
| **F03** | **Campaña de descubrimiento — FASE ACTIVA** | 8 de 13 verificadas |
| **F09** | Front limpio | 14 de 15 verificadas |
| **F10** | Operaciones, máquinas y despliegue | 8 de 9 verificadas |

**La fase activa es F03**, la fábrica de estrategias: es el cuello de botella de todo lo demás,
porque sin candidatos medidos no hay nada que mejorar, ni valorar, ni con lo que pasar un examen de
fondeo. Lo que le falta para cerrarse:

- **A36** — las 40.000 estrategias de los bancos solo existen en la memoria de StrategyQuant. Es la
  clave de la fase: sin el artefacto de cada estrategia guardado y con huella reproducible, el
  criterio 1.1 no se puede aplicar y la fase **no puede cerrarse**.
- **A35** — comprobar que el intradía produce con los filtros ya aflojados.
- **A39** — que la rejilla diga por qué una celda da cero.
- **A33** — el sello del censo, cuando A36 lo haga posible.
- **E01** — decisión de Emilio sobre la licencia de StrategyQuant (caduca el 17 de septiembre).

**F10 es un carril de apoyo permanente**, no una fase del camino: no depende de nadie y nadie depende
de ella, pero sin máquinas y sin despliegue las demás no corren. Puede tener trabajo abierto a la
vez que la fase activa. Hoy le queda **A37**, publicar la web en su URL con el código de hoy.

**Cuando F03 cierre**, la siguiente por dependencias es **F04** (motor de mejora inteligente) y en
paralelo **F07** (pasar exámenes de fondeo), que es lo que Emilio persigue.
