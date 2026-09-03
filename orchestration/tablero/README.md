# EL TABLERO — sistema de orquestación entre el orquestador y los agentes

> Esta carpeta **es** el sistema. Un fichero por tarea, con un estado en la cabecera. La web lo lee
> en vivo (`/api/tablero`, sin caché) y lo pinta en `/plan` → pestaña **Tareas AGY**. No hay una
> segunda lista en ningún sitio: si algo no está aquí, no existe; si aquí dice `PENDIENTE`, está
> pendiente. Emilio ve el estado real sin abrir una terminal, y los dos agentes ven lo mismo.

## Por qué existe

Trabajan a la vez el **orquestador** (sesión Claude Code, en el PC: investiga, mide, escribe las
tareas y verifica) y **AGY** (los agentes de Antigravity, en otra ventana: ejecutan). No se ven
entre sí y van a velocidades distintas: AGY es muy rápido con tareas **pequeñas y clarísimas**, y
se pierde con encargos grandes o vagos. Sin un sitio común, el orquestador no sabe si algo se hizo,
AGY no sabe qué sigue, y Emilio tiene que ir preguntando. Este tablero cierra ese bucle.

## El ciclo, en una línea

**El orquestador escribe la tarea → AGY la coge y la ejecuta → AGY escribe su parte de entrega →
el orquestador re-ejecuta la aceptación y la verifica o la devuelve → si queda algo, sale tarea nueva.**

## Los estados (uno solo por tarea, en el frontmatter `estado:`)

| Estado | Qué significa | Quién lo pone |
| :--- | :--- | :--- |
| `PENDIENTE` | Escrita y lista para que alguien la coja | orquestador |
| `EN_CURSO` | AGY la está haciendo ahora mismo | AGY, al empezar |
| `ENTREGADO` | AGY terminó y dejó su parte con la salida cruda | AGY, al terminar |
| `VERIFICADO` | El orquestador re-ejecutó la aceptación y cuadra | orquestador |
| `DEVUELTO` | No cuadra: el orquestador escribe qué falta y vuelve a `PENDIENTE` | orquestador |
| `BLOQUEADO` | No se puede seguir sin algo de fuera (una decisión de Emilio, una clave, otra tarea) | cualquiera, diciendo por qué |

## Reglas que hacen que esto funcione

1. **Una tarea, un dueño.** El campo `agente:` dice quién la hace. Nadie toca la tarea de otro.
2. **Tareas pequeñas.** Si una tarea no cabe en 15-20 minutos y en un puñado de comandos, se parte
   en dos. Es preferible A07 + A08 que un A07 gigante.
3. **Ámbito cerrado.** El campo `ambito:` lista las únicas rutas o máquinas donde esa tarea puede
   escribir. Lo que se vea roto fuera de ahí se anota como `HALLAZGO` en el parte y **no se toca**.
4. **Evidencia o no existe.** Toda afirmación va con el comando que la produce y su salida **cruda**,
   pegada sin resumir. Un parte sin salida cruda se devuelve sin leerlo.
5. **Ante la duda, `NO DATA`.** Nunca un dato inventado, ni un valor por defecto para tapar un hueco.
6. **Sin prisa.** No hay plazo. Entre entregar ya o comprobarlo otra vez, se comprueba otra vez.
7. **Tres intentos.** Si un comando falla tres veces igual, se para y se cuenta en el parte.
8. **Nunca `rm`.** Lo que sobra se aparta a `cuarentena/` con manifiesto SHA-256.

## Cómo se escribe una tarea (plantilla)

Fichero `orchestration/tablero/A07.md` (el ID manda: corto y estable, para poder decir "haz la A07"):

```markdown
---
id: A07
titulo: "Una frase que diga qué será verdad al terminar"
agente: AGY
estado: PENDIENTE
prioridad: ALTA
maquina: hetzner
ambito: ["/etc/nginx/", "orchestration/tablero/A07.md"]
depende_de: []
estimado: "10 min"
creado: "2026-09-03 01:20 UTC"
actualizado: "2026-09-03 01:20 UTC"
---

## Por qué
Dos o tres frases con el dato medido que justifica la tarea.

## Qué hacer
Pasos numerados con los comandos exactos, copiables, y cómo deshacer cada uno.

## Aceptación
Comandos que el orquestador va a re-ejecutar, con la salida esperada.

## Prohibido
Lo que no se toca, explícito.

## Parte de entrega
(lo rellena AGY)

## Verificación del orquestador
(lo rellena el orquestador)
```

## Qué hace AGY exactamente

1. Mira el tablero en `/plan` → **Tareas AGY**, o los ficheros de esta carpeta.
2. Coge la tarea `PENDIENTE` de mayor prioridad cuyo `agente:` sea `AGY`. Pone `estado: EN_CURSO` y
   actualiza `actualizado:`. Guardar el fichero ya avisa: el orquestador vigila esta carpeta.
3. Ejecuta **solo** lo que dice la tarea.
4. Rellena `## Parte de entrega` con este formato y pone `estado: ENTREGADO`:

```markdown
## Parte de entrega
**Agente:** AGY · **Fecha:** 2026-09-03 01:45 UTC
**Resultado en una frase:** qué es verdad ahora que antes no lo era.

**Comandos y salida CRUDA:**
$ comando
salida tal cual, sin recortar

**Lo que no pude hacer:** ... (o "nada")
**HALLAZGOS fuera de mi ámbito (no los toqué):** ... (o "ninguno")
```

5. No hace `git commit` salvo que la tarea lo pida. Con guardar el fichero basta.

## Qué hace el orquestador

1. Se entera al instante: hay un vigilante sobre esta carpeta.
2. Re-ejecuta él mismo los comandos de `## Aceptación`. **No se cree el parte.**
3. Escribe `## Verificación del orquestador` con lo que él midió y pone `VERIFICADO` o `DEVUELTO`
   con una lista concreta y corta de correcciones.
4. Si el trabajo abre trabajo nuevo, escribe la tarea siguiente en el tablero. Así AGY siempre tiene
   claro qué sigue sin preguntar.
