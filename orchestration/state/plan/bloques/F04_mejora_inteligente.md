---
id: F04
titulo: "Motor de mejora inteligente"
estado: PENDIENTE
depende_de: ["F03"]
desbloquea: ["F05"]
verificacion_global: "Si ninguna mejora sobrevive al holdout ciego + DSR + walk-forward, se reporta SIN MEJORA. No se fuerza."
actualizado: "2026-08-31"
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
