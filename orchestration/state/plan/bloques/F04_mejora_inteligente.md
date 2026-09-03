---
id: F04
titulo: "Motor de mejora inteligente"
estado: PENDIENTE
depende_de: ["F03"]
desbloquea: ["F05"]
verificacion_global: "Si ninguna mejora sobrevive al holdout ciego + DSR + walk-forward, se reporta SIN MEJORA. No se fuerza."
actualizado: "2026-09-03"
---

# FASE 4 — MOTOR DE MEJORA INTELIGENTE

> Requisito literal del usuario: mejora *dinámica, semántica y programática*, **sin hardcodear**
> "ATR +2" ni "subir el SL un 2 %".

## 4.1 Capa semántica — el *por qué*

El sistema no mira los parámetros: mira **las operaciones**. Agrupa las perdedoras y busca qué
comparten (hora, régimen de volatilidad, spread del momento, duración, rachas previas...).
Produce una **hipótesis sobre el mecanismo**, en lenguaje natural:
*"pierde sistemáticamente cuando entra con el spread por encima de su mediana"*.
Aquí la IA aporta hipótesis, **nunca números**.

## 4.2 Capa programática — el *qué*

Cada hipótesis se compila en un **experimento parametrizado**, jamás en una regla fija.
"Bloquea Asia" está prohibido; lo correcto es *una máscara de sesión cuyos límites se buscan*.

> **La regla de oro: la inteligencia elige la DIMENSIÓN, la búsqueda encuentra el VALOR.**

## 4.3 Capa de prueba — el *¿es real?*

Una IA dopando estrategias es una máquina de sobreajustar: si propone 200 mejoras, ~10 funcionarán
por azar. Defensas obligatorias:

- **Blind holdout intocable** durante toda la fase de hipótesis. Ni para mirar.
- **Penalización por multiplicidad** (DSR): cuantas más hipótesis, más alto el listón.
- **Walk-forward:** la mejora aguanta en varias ventanas o no existe.
- Si ninguna mejora sobrevive, se reporta `SIN MEJORA`. No se fuerza.

*(Las killzones son **una** de las dimensiones que esta capa puede proponer. El usuario pide
tenerlas en cuenta más adelante, no como fase propia.)*

## Actualización 2026-09-03 — el sistema de aprendizaje SÍ existe, y este bloque no lo recogía

Emilio lo dijo mirando el plan: *"había también un sistema de aprendizaje de construcción y edición
de estrategias, y no lo veo en el plan maestro"*. Tenía razón. Una auditoría de solo lectura con seis
agentes (tres lectores y tres escépticos) recorrió el repositorio entero el 03-09 y encontró **tres
sistemas distintos** para esto, ninguno citado en este bloque, que seguía fechado el 31-08.

Lo que hay, verificado por el orquestador con sus propios comandos:

**1. El diseño, que es bueno y está completo.** `ARQUITECTURA_MODULAR_ESTRATEGIAS.md` define M2 como
un bucle de mejora con hipótesis → experimento → nueva evaluación, con el tramo ciego intocable y
penalización por multiplicidad, y su máquina de estados CRUDA → EVALUADA → EN_MEJORA(n) → CERTIFICADA
o AGOTADA. Es exactamente lo que Emilio recuerda. **Este bloque no lo citaba.**

**2. Un esqueleto limpio y vacío.** `services/improvement/` (`loop.py`, `contratos.py`), escrito el
02-09, respeta las reglas duras: nunca toca el holdout ciego y acumula la multiplicidad antes del
control correspondiente. Pasa sus siete pruebas. Pero **no lo llama nadie en producción**: solo su
propio test. Es el M2 bien hecho y sin enchufar, porque le falta la pieza que propone mejoras.

**3. Un mejorador antiguo que viola la doctrina.** `services/optimization/expert_refinement_loop.py`
usa el tramo ciego **dentro** del bucle de iteraciones (línea 242), que es justo lo que esta fase
prohíbe, y aplica multiplicadores fijos (×0,88, ×1,20) en vez de buscar el valor. Instancia cinco
"agentes" que **nunca se llaman**, y que además no hablan con ninguna inteligencia artificial: no hay
una sola referencia a un proveedor de modelos en su código. Hoy tampoco lo llama producción.

**4. Un sistema semántico montado en la API pero hueco.** `services/semantic_ai/` está colgado en
`/api/v2/semantic` y promete generar, mutar, criticar y "debatir" candidatas contra una base de
fallos. Dos agujeros medidos:
   - el endpoint que graba las autopsias de fallo (`record_failure_autopsy`) **tiene el cuerpo
     vacío**: solo la descripción, sin código;
   - su base de conocimiento (`learning_store.sqlite`) tiene **once tablas y cero filas en todas**.
     Comprobado por el orquestador el 03-09: cero fallos, cero debates, cero mutaciones.

**5. Y lo peor**: la página `/estrategias/mejora` presentaba ese comité como si estuviera funcionando
y afirmaba cruzar cada candidata contra *"5.000+ estrategias fallidas"*. No hay ninguna. Corregido
en la tarea A18 del tablero.

### Qué queda decidido y qué no

- **Decidido** (Emilio, 03-09): el sistema **tiene que aprender de lo hecho, bueno y malo**, para las
  siguientes búsquedas, y antes de construirlo hay que **investigar cómo se hace bien**. Es la
  decisión D2 de `ESPECIFICACION_WEB.md`.
- **Camino natural, sin inventar nada nuevo**: conectar el esqueleto limpio de `services/improvement/`
  con una fuente de propuestas real, y llenar la base de aprendizaje **desde la telemetría que ya
  producimos** (cada campaña deja escrito por qué murió cada configuración; hoy eso se tira).
- **A cuarentena, cuando se decida**: el mejorador antiguo, por usar el tramo ciego dentro del bucle.
  No se borra: se aparta con manifiesto, como todo aquí.
- **Pendiente de la investigación**: qué propone las mejoras (búsqueda de parámetros, mutación
  semántica, o el propio StrategyQuant), y cómo se mide que el aprendizaje sirve de algo.

Este bloque deja de estar solo en `PENDIENTE`: está **parcialmente construido y mal contado**, que es
peor, porque la web lo presentaba como vivo.
