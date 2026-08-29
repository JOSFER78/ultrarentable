# orchestration/ — Orquestador (Auditor) + Antigravity (Ejecutor)

El ciclo completo es: **pendiente → ejecutado → revisado**.

1. El estado vive en `state/status.json` (`phase_number` + `status`).
2. `state/current_phase.md` contiene la tarea activa, detallada hasta el mínimo paso.
3. `status = pending` (o `needs_user_input` aprobado por ti) ⇒ la tarea está lista para Agy.
4. Tú abres Antigravity en tu PC, le pegas la tarea, y Agy ejecuta (guía: `scripts/run_agy.sh`).
5. Agy deja su informe en `results/fase_NN.log`; cambia `status` a `done`.
6. Ejecutas `scripts/run_orchestrator_review.sh`: empaqueta el contexto en `reviews/fase_NN_context.md`.
7. El orquestador (Hermes) revisa y escribe el veredicto en `reviews/fase_NN_review.md`
   (última línea JSON: `avanza` | `repite` | `needs_user_input`).
8. `avanza` ⇒ fase +1 y nueva current_phase.md; `repite` ⇒ misma fase corregida; `needs_user_input` ⇒ todo parado hasta que tú actúes.
9. **Sin git commit automático**: la auditoría es este árbol (results/ + reviews/ + history en status.json).
10. El plan completo con objetivos, criterios y dependencias está en `state/plan_maestro.md`.
