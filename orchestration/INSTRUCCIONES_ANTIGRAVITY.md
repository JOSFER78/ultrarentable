# Instrucciones de ejecución para Antigravity (ejecutor del loop)

> Este archivo define CÓMO trabaja Antigravity dentro del repo. El orquestador (Hermes)
> escribe las tareas; Antigravity las ejecuta en orden y deja informes. Nada más.

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

## Reglas inquebrantables

- **NUNCA `git commit` ni `git push`.** Todo queda en working tree; el usuario inspecciona.
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
