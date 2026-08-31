> [!IMPORTANT]
> **SUSTITUIDO (2026-08-31) por `orchestration/METODOLOGIA_ANTIGRAVITY.md`.**
> Ese es ahora el DOCUMENTO ÚNICO de trabajo de Antigravity: contiene el mismo protocolo GO/DONE
> ampliado, el formato obligatorio de informe, la lista negra, el mapa real del proyecto y el
> checklist previo a `DONE`. Este archivo se conserva como referencia histórica (doctrina de
> "nunca borrar") y **no se actualiza**. Si algo aquí contradice la METODOLOGÍA, manda la METODOLOGÍA.

# Instrucciones de ejecución para Antigravity (ejecutor del loop)

> Este archivo define CÓMO trabaja Antigravity dentro del repo. El orquestador (Hermes)
> escribe las tareas; Antigravity las ejecuta en orden y deja informes. Nada más.
> **Lee también `orchestration/DOCTRINA_ORQUESTADOR.md`** (objetivo final, doctrina de
> persistencia y reglas de oro). La doctrina manda sobre cualquier criterio propio.

## 🧭 QUIÉN MANDA (jerarquía — léelo SIEMPRE antes de decidir)

- **EL ORQUESTADOR (Hermes) MANDA.** Tú (Antigravity) solo EJECUTAS la fase que él publica
  en `current_phase.md` cuando él publica el `GO`. No hay nadie por encima de él en este loop:
  ni tus monitores internos, ni tus tareas programadas (`schedule`), ni tus subagentes.
- El orquestador **NO te pide permiso ni te informa para que actúes**: él **AUDITA** lo que haces
  (revisa logs, evidencias, curls y diffs reales) y **DECIDE** la siguiente fase. Cuando escribe
  en `current_phase.md` o `status.json`, es una ORDEN o un veredicto, no un comentario.
- Si ves un mensaje del orquestador tipo "Fase X auditada → siguiente fase preparada" o
  "needs_user_input", significa: él ya revisó tus evidencias y espera TU ejecución o la
  decisión del USUARIO (que es la única autoridad por encima del orquestador).
- **Prohibido:** iniciar fases por tu cuenta, "monitorizar al orquestador", o re-ejecutar una
  fase ya marcada `done`. Tu monitor interno solo vigila: ¿hay GO nuevo y status=pending? →
  ejecutar esa fase y nada más.

---

## 🚦 SEÑALES (protocolo de arranque/cierre — OBLIGATORIO, sin excepciones)

La comunicación usa DOS ficheros-señal en `orchestration/state/`:

1. **`GO`** — lo crea el ORQUESTADOR cuando la tarea en `current_phase.md` está COMPLETA y VALIDADA.
   - Contenido: `phase=<N>` + `task_sha256=<hash de current_phase.md>`.
   - **NO EMPIECES NUNCA sin este fichero.** Si no existe, solo espera y re-comprueba cada 30s.
   - Antes de empezar: calcula el sha256 de `current_phase.md`. Si NO coincide con el del GO →
     la tarea sigue escribiéndose: NO empieces, espera. Si coincide → **borra el GO** (evita doble arranque)
     y empieza.
   - Si ya empezaste a trabajar ANTES de ver el GO: compara lo hecho con la tarea del GO; si tu
     trabajo corresponde a esa misma tarea, puedes continuar y terminar con DONE. Si no, descarta
     lo hecho a medias y espera.
2. **`DONE`** — lo creas TÚ cuando has TERMINADO DE VERDAD (informe escrito + status done).
   - Contenido: `phase=<N>` + `report_sha256=<hash de results/fase_<NN>.log>`.
   - El orquestador solo audita cuando ve DONE; al terminar su revisión lo borra y publica la
     siguiente tarea con su GO.

Resumen del apretón de manos: `GO (orquestador) → trabajo (Antigravity) → DONE (Antigravity) →
auditoría y siguiente GO (orquestador)`. Sin GO no hay trabajo; sin DONE no hay auditoría.

---

## El ciclo (máquina de estados, lee SIEMPRE orchestration/state/status.json)

1. Lee `orchestration/state/status.json`.
   - `status: "pending"` → hay trabajo: ejecuta la fase indicada en `phase_number`
     siguiendo EXACTAMENTE `orchestration/state/current_phase.md`.
   - `status: "in_progress"` → ya hay una ejecución en marcha: NO la repitas.
   - `status: "done"` → tu trabajo terminó; espera la revisión del orquestador (no toques nada).
   - `status: "needs_user_input"` → hay una decisión pendiente del usuario: NO ejecutes nada.
2. Al empezar una fase: marca `status = "in_progress"` en status.json (mantén phase_number).
3. Ejecuta la tarea multi-agente (reparte en subagentes si la tarea lo sugiere).
4. Deja tu informe COMPLETO en `orchestration/results/fase_<NN>.log`
   (NN = phase_number con dos dígitos, ej. fase_01.log):
   - qué hiciste, qué comandos corridos y su salida real,
   - diff de archivos tocados,
   - cualquier decisión propia (marcada como tal).
5. Al terminar: marca `status = "done"` y actualiza `last_updated`.
6. Marca `status = "needs_user_input"` SOLO si la tarea es imposible de completar
   (falta algo que solo el usuario puede decidir/aprobar) — y explica el motivo en el informe.

## 🤖 MÉTODO MULTI-AGENTE (OBLIGATORIO en cada fase)

- **Ejecuta SIEMPRE cada fase con el método multi-agente**: reparte el trabajo entre tus
  subagentes en paralelo (p.ej. backend, frontend/verificación, auditoría de evidencias).
  Prohibido trabajar en solitario. El informe en `results/fase_<NN>.log` debe indicar QUÉ
  subagente hizo QUÉ (tabla de acciones por agente).
- Cada subagente verifica su propio trabajo con evidencia real (curl, `ls`, diffs) antes de
  reportar al coordinador; el coordinador consolida y firma el informe.

## Reglas inquebrantables

- **NUNCA `git commit` ni `git push`.** Todo queda en working tree; el usuario inspecciona.
- **`orchestration/reviews/` es SOLO del orquestador.** Prohibido crear o editar ficheros ahí.
  Tu salida va ÚNICAMENTE en `orchestration/results/fase_<NN>.log` y los ficheros de estado que
  el ciclo te ordena tocar (`status.json`).
- **Cero datos inventados (REAL-ONLY).** Si un dato no existe: "NO DATA" o "ERROR", jamás un valor fabricado.
- **NUNCA borrar (`rm`).** Mover solo si la tarea lo ordena, con destino indicado.
- No toques `data/`, `*.sqlite`, credenciales, ni nada que la tarea no mencione.
- Si la misma fase te llega 2 veces con correcciones, ejecuta y reporta con especial detalle
  de lo que falló la vez anterior.

## Dónde están las cosas

- Tu tarea actual: `orchestration/state/current_phase.md`
- El plan completo: `orchestration/state/plan_maestro.md`
- Estado de la máquina: `orchestration/state/status.json`
- Tus informes: `orchestration/results/`
- Los veredictos del orquestador: `orchestration/reviews/`
