# AGY: EMPIEZA AQUÍ

> Este es tu punto de entrada. Emilio te dice "lee `orchestration/tablero/AGY_EMPIEZA_AQUI.md` y
> ponte", y tú haces exactamente lo que pone debajo. No hace falta que nadie te avise de nada más:
> el tablero es tu lista de trabajo y siempre está al día.

## Regla número uno: leer no es empezar

Vas a leer tareas que **no** son para ti todavía. Leer el tablero nunca autoriza a trabajar. Solo
puedes tocar una tarea si cumple **las tres** condiciones a la vez:

1. `agente: AGY`
2. `estado: PENDIENTE`
3. sus `depende_de` están todas en `VERIFICADO`

Si una tarea pone `estado: BORRADOR`, el orquestador la está escribiendo: **no existe para ti**,
aunque la veas entera y parezca lista. Si pone `EN_CURSO`, ya la ha cogido alguien. Si pone
`ENTREGADO`, está esperando a que el orquestador la verifique: **no la vuelvas a tocar** aunque
creas que falta algo; si crees que falta algo, escríbelo en el buzón.

## Tus cinco pasos, siempre los mismos

1. **Mira el buzón**: `orchestration/tablero/BUZON.md`. Ahí el orquestador te deja mensajes cortos
   (correcciones, cambios de prioridad, avisos). Lee de abajo arriba lo que no hayas leído.
2. **Elige tarea**: abre `orchestration/tablero/` y coge la de mayor prioridad
   (`URGENTE` > `ALTA` > `MEDIA` > `BAJA`) que cumpla las tres condiciones de arriba. Si empatan,
   la de ID más bajo. **Una sola a la vez.**
3. **Cógela**: en su fichero, cambia `estado: PENDIENTE` por `estado: EN_CURSO` y pon la hora en
   `actualizado:`. Guarda. Con guardar basta: el orquestador vigila la carpeta y lo ve al momento.
4. **Hazla**: solo lo que dice la tarea, solo dentro de su `ambito:`. Los comandos, tal cual están
   escritos. Si algo falla tres veces igual, paras.
5. **Entrégala**: rellena `## Parte de entrega` con el formato de abajo, pon `estado: ENTREGADO`,
   guarda, y **vuelve al paso 1**. No sigas con otra tarea hasta haber entregado la que tenías.

## El formato del parte (obligatorio, sin adornos)

```markdown
## Parte de entrega
**Agente:** AGY · **Fecha:** 2026-09-03 02:10 UTC
**Resultado en una frase:** qué es verdad ahora que antes no lo era.

**Comandos y salida CRUDA:**
$ el comando exacto que ejecutaste
la salida tal cual, entera, sin resumir ni recortar

**Lo que no pude hacer:** ... (o "nada")
**HALLAZGOS fuera de mi ámbito (no los toqué):** ... (o "ninguno")
```

Un parte sin salida cruda pegada se devuelve sin leerlo. No es desconfianza personal: en este
proyecto una afirmación sin el comando que la produce no cuenta, y eso vale igual para el
orquestador, que pega la suya cuando verifica.

## Lo que nunca haces

- Trabajar en una tarea `BORRADOR`, `EN_CURSO`, `ENTREGADO` o `VERIFICADO`.
- Salirte del `ambito:` de la tarea. Lo que veas roto fuera va como `HALLAZGO` en el parte, y sigues.
- Inventar una cifra, una ruta o una salida. Si no lo sabes: `NO DATA`.
- `rm` en cualquier forma. Lo que sobra se aparta a `cuarentena/` con manifiesto SHA-256.
- `git commit`, `git push`, `git checkout`, `git reset` salvo que la tarea lo pida expresamente.
- Ir rápido. No hay plazo. Entre entregar ya o comprobarlo otra vez, comprueba otra vez.
- Arreglar de paso "una cosita más". Si hace falta, se escribe una tarea nueva.

## Si te bloqueas

Pon `estado: BLOQUEADO` en la tarea, explica en el parte **qué** te falta exactamente (una decisión,
una contraseña, otra tarea) y escribe una línea en el buzón. Luego vuelve al paso 1 con otra tarea.
Bloquearse y decirlo está bien; adivinar para salir del paso, no.

## Dónde está todo

| Qué | Dónde |
| :--- | :--- |
| Tus tareas | `orchestration/tablero/` (un fichero por tarea: `A01.md`, `A02.md`…) |
| Mensajes del orquestador | `orchestration/tablero/BUZON.md` |
| Las reglas completas | `orchestration/tablero/README.md` |
| Cómo se ve todo esto | `http://localhost:3100/plan` → pestaña **Tareas AGY** |
| El plan del proyecto | `orchestration/state/plan/bloques/F*.md` |
| Las reglas del proyecto | `CLAUDE.md` en la raíz |
