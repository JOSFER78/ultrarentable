# AGY: EMPIEZA AQUÍ

> Este es tu punto de entrada. Emilio te dice "lee `orchestration/tablero/AGY_EMPIEZA_AQUI.md` y
> ponte", y tú haces exactamente lo que pone debajo. No hace falta que nadie te avise de nada más:
> el tablero es tu lista de trabajo y siempre está al día.

## Los cuatro ceros (lo primero de todo)

Emilio lo resumió mirando cómo trabajas, el 2026-09-03, y queda como regla de cabecera porque es
mejor formulación que cualquier lista larga:

**Cero inventar · cero simular · cero forzar · cero prisas.**

- **Cero inventar**: ninguna cifra, ruta, salida ni nombre que no hayas visto con tus ojos en la
  salida de un comando. Si no lo sabes: `NO DATA`.
- **Cero simular**: nada de datos de ejemplo, de relleno ni "provisionales". Si algo no se puede
  hacer de verdad, se dice que no se puede.
- **Cero forzar**: si una comprobación no da lo esperado, no la retuerzas hasta que dé. Puede que la
  comprobación esté mal escrita (ya ha pasado, y era culpa del orquestador). Lo anotas y sigues.
- **Cero prisas**: no hay plazo. Entre entregar ya o comprobarlo otra vez, comprueba otra vez.

Y una quinta que va con ellas: **tareas pequeñas**. Si una tarea se te hace larga o vaga, párala y
dilo en el buzón; se parte en dos. Vas rápido y bien cuando el encargo es pequeño y clarísimo.

## Nunca te quedes esperando

Tu tiempo vale, y mientras esperas no programas. Emilio lo dijo viéndote parado diez minutos delante
de una auditoría en un servidor: *"no podemos hacer esperar al proceso de programación por este tipo
de cosas"*.

- **Nada de `sleep`, ni de esperas de minutos, ni de comprobar en bucle** si algo cambió. Si una
  tarea te lo pide, es que la tarea está mal escrita: dilo en el buzón y sigue con otra.
- Un comando contra un servidor **se lanza y se lee la respuesta**. Si no responde en el momento, se
  anota que no respondió y se sigue. No se insiste.
- Lo que hay que comprobar más tarde lo comprueba el orquestador, que tiene vigilantes para eso.
- **Tu terreno natural es el código y la web**: ahí eres rápido y no dependes de nadie. Las tareas de
  servidor son la excepción, van sueltas y siempre sin esperas.

Si una tarea te va a tener parado más de un par de minutos sin hacer nada, **párala, ponla en
`BLOQUEADO` con el motivo y coge la siguiente**. No es abandonar: es no malgastar el turno.

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


## Lecciones que ya hemos aprendido (esto crece)

Se apunta aquí lo que ha salido trabajando, para no repetirlo. Lo añade el orquestador cuando cierra
una tarea.

- **2026-09-03, A06**: una comprobación pedía contar apariciones de un texto dentro del propio
  fichero de la tarea, y el texto aparecía también en el enunciado, así que no podía dar el número
  esperado. El fallo era del orquestador. Desde entonces, esas comprobaciones usan un patrón que no
  aparezca en el enunciado. **Si ves una comprobación imposible, no la fuerces: dilo.**
- **2026-09-03, A08**: la tarea decía "no toques `AuthContext.tsx`, ahí el correo está bien", y para
  cuando AGY la cogió ya no era cierto porque otro editor lo había cambiado. **Si un fichero no se
  parece a lo que describe la tarea, para y dilo en el buzón** en vez de adaptarte a lo que ves. El
  orquestador reescribe la tarea con lo que hay.
- **2026-09-03, A09**: el mapa de documentos de la web no admitía la carpeta `archive`, así que había
  que ampliarlo. Se hizo sin inventar rutas. Ese es el patrón: cuando falta una pieza, se añade la
  pieza, no se apaña el camino.
- **2026-09-03, A04**: cinco componentes que la página `/plan` importa existían en el disco pero no
  estaban en git, así que la página funcionaba en esta máquina y habría fallado en un servidor recién
  clonado. **Cuando crees un fichero nuevo que otro importa, dilo en el parte con su ruta.** Tú no
  commiteas, pero el orquestador necesita saberlo para dejar el repositorio coherente.
