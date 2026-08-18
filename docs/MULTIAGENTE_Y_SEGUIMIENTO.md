# 🧠 MODELO MULTIAGENTE + SISTEMA DE SEGUIMIENTO — Ultrarentable

> **LEE ESTE ARCHIVO PRIMERO.** Es la referencia canónica de cómo trabaja este
> proyecto: cómo se organiza el trabajo (orquestador + subagentes paralelos) y
> cómo se hace seguimiento/actualización de lo hecho e investigado.
> Cualquier agente (IA) o persona que empiece a trabajar aquí DEBE leer esto
> antes que nada.
>
> Ubicación: raíz del proyecto → `MULTIAGENTE_Y_SEGUIMIENTO.md`
> Complementos: `README.md` (guía de entrada: web/Obsidian/servicios),
> `ESTADO.md` (estado vivo), `plan_implementacion/bitacora/` (histórico).

---

## PARTE 1 — EL MODELO DE ORQUESTACIÓN MULTIAGENTE (cómo se trabaja)

### 1.1 Quién ejecuta y quién dirige

Este proyecto se trabaja con un **orquestador central + subagentes ejecutores en paralelo**. NO es un único agente que lo hace todo.

| Rol | Quién | Qué hace / Qué NO hace |
|-----|-------|------------------------|
| **🛡️ ORQUESTADOR (jefe de proyecto)** | Hermes | **SOLO analiza, organiza, decide, manda, supervisa, comprueba, vuelve a analizar y verifica.** NO ejecuta el trabajo técnico él mismo. |
| **⚙️ SUBAGENTES EJECUTORES (trabajadores)** | Subagentes lanzados en paralelo (delegate_task) | Ejecutan: investigan, implementan, editan código, crean documentos, lanzan comandos, y DEVUELVEN su resultado al orquestador. |
| **🧑 USUARIO (product owner)** | Persona | Define el objetivo y las correcciones de rumbo. Habla SOLO con el orquestador. |

### 1.2 El ciclo del orquestador (bucle continuo)

El orquestador trabaja en un **bucle de supervisión** — y este es el comportamiento EXACTO que se espera de él en cada sesión:

```
1. ANALIZAR
   → Lee el estado (ESTADO.md + bitácora + docs) y el objetivo del usuario.
   → Decide qué hay que hacer y en qué ORDEN (qué depende de qué).

2. PREPARAR / MANDAR
   → Redacta mandatos (task contracts) claros: objetivo, alcance, inputs,
     entregable, criterios de aceptación.
   → Los despacha a SUBAGENTES EN PARALELO (varias tareas independientes a la vez,
     para no desperdiciar tiempo).

3. (los subagentes trabajan en paralelo, cada uno en su tarea)

4. COMPROBAR / VERIFICAR
   → Cuando un subagente entrega, el orquestador NUNCA se fía de su auto-informe.
   → Comprueba la evidencia real: tests que pasan, archivos creados, endpoints que
     responden, datos reales (REAL-ONLY). Contraste empírico.

5. VOLVER A ANALIZAR
   → Con los resultados verificados, re-evalúa el estado, detecta desvíos o
     colisiones entre subagentes, reorienta si hace falta.

6. REPETIR
   → Sigue hasta el objetivo. Mantiene el hilo y NO acumula contexto inútil
     (no lanza tareas por inercia; espera/revisa entre entregas).
```

**Regla de oro del orquestador:** *"Yo no pico código ni ejecuto el trabajo; yo decido QUIÉN lo hace, MANDO que se haga, y VERIFICO que se hizo bien."*

### 1.3 Beneficios de este modelo
- **Aprovecha recursos**: los subagentes hacen el trabajo pesado (investigación, código) en paralelo.
- **Mantiene la calidad**: el orquestador verifica todo con evidencia real, no con autoinformes.
- **Mantiene el hilo**: el orquestador no se llena de código/temperatura, porque los subagentes le devuelven solo resúmenes; él conserva la visión global.
- **Corrección de rumbo**: cuando un subagente se desvía de la doctrina, el orquestador lo detecta y reorienta.

---

## PARTE 2 — EL SISTEMA DE SEGUIMIENTO Y ACTUALIZACIÓN (cómo se guarda y se recupera el estado)

### 2.1 Qué debe leer un agente AL EMPEZAR un chat (en este orden)

```
1. MULTIAGENTE_Y_SEGUIMIENTO.md   ← este archivo (cómo se trabaja + cómo se sigue)
2. README.md                      ← guía de entrada: servicios, web, Obsidian
3. ESTADO.md                      ← estado VIVO: qué está hecho ✅ / qué falta 🔴 / próximo paso
4. plan_implementacion/bitacora/  ← histórico cronológico por fecha (lo último hecho ayer/hoy)
5. docs / plan_implementacion/    ← detalle de cada investigación/plan (según lo que necesite)
```
Con esto, un agente que llega **nuevo** sabe exactamente: qué se busca, qué se ha hecho, qué falta, y cómo continuar.

### 2.2 Estructura de archivos de seguimiento (dónde va cada cosa)

| Archivo | Contenido | Cuándo se actualiza |
|---------|-----------|---------------------|
| `README.md` | Guía de entrada (servicios, web, Obsidian, doctrina) | Rara vez (solo cuando cambia algo estructural) |
| `ESTADO.md` | Resumen vivо: ✅ hecho / 🔴 pendiente / 🎯 próximo paso | **Al inicio Y al final de cada bloque de trabajo / cada sesión** |
| `plan_implementacion/bitacora/YYYY-MM-DD.md` | Entrada cronológica de la sesión: qué se hizo, qué se aprendió, decisiones, cómo continuar | **Un archivo por día**, se crea/amplía al final de cada sesión de trabajo |
| `plan_implementacion/*.md` | Investigaciones/planes en detalle (blueprint, guía, auditoría, etc.) | Cuando se crea/actualiza una investigación |

### 2.3 Convención de actualización (lo que TODO agente debe cumplir al terminar)

Cuando un agente (o el orquestador al cerrar un bloque) termina su trabajo, DEBE dejar registrado en el sistema:

1. **Actualizar `ESTADO.md`**: mover a ✅ lo que se completó (con su fecha), actualizar 🔴 pendientes y el 🎯 próximo paso concreto.
2. **Añadir/ampliar la entrada del día en `plan_implementacion/bitacora/`**: fecha + qué se hizo + qué se investigó/descubrió + decisiones + qué queda pendiente. (Si el archivo del día no existe, crearlo: `plan_implementacion/bitacora/<Hoy>.md`.)
3. **SI generó una investigación/plan nuevo**, dejarlo en `plan_implementacion/` (o `docs ayuda/`) con nombre descriptivo, y **referenciarlo** en ESTADO.md y en la bitácora.

> **Regla de continuidad (crítica):** el proyecto DEBE quedar "auto-continuable".
> Si mañana abre el chat otro agente SIN contexto previo, con leer README → ESTADO → bitácora
> ya debe saber exactamente en qué punto está y cuál es el siguiente paso. Si esto no se cumple,
> el trabajo se pierde. POR ESO SIEMPRE se actualiza ESTADO.md + bitácora al terminar.

### 2.4 Cómo decide un agente nuevo "qué tocar" (evitar pisarse)
- Antes de editar un archivo, comprobar si otro agente lo está modificando (locks en `data/artifacts/locks/` o en ESTADO.md/bitácora quién está activo).
- Respetar la **fuente única de verdad** (AGENTS.md): solo /home/ubuntu/workspace/pro/trading/01 Ultrarentable; nunca copias duplicadas.
- No reiniciar servicios 24/7 sin avisar (strategyquantx, ultrarentable-api, ultrarentable-web).

---

## PARTE 3 — DOCTRINA Y OBJETIVO (resumen, más detalle en ESTADO.md y README.md)

- **Objetivo central**: conseguir estrategias de **miles de % verificables en backtest** (modo kamikaze ULTRA) y estrategias para **aprobar exámenes de fondeo**.
- **ULTRA** (☠️): buscar multiplicador extremo aunque se queme la cuenta 8/10; **NO descartar por drawdown** (solo ruina real dd ≥ 100%). **FONDEO** (🏛️): conservador (DD bajo, consistencia).
- **REAL-ONLY**: prohibido inventar métricas; todo debe venir de ejecución real con evidencia (SQX/backtest).
- **Usar SQX como experto**: la IA debe **ENTRAR en StrategyQuant y usarlo** (sus muchas variables), NO lanzar scripts hardcodeados que repiten.
- **Rol del orquestador**: analiza, manda, comprueba, verifica. Siempre. Los subagentes ejecutan.
