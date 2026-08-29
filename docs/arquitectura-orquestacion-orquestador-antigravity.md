# Arquitectura de Orquestación: Orquestador (Auditor) + Antigravity 2.0 (Ejecutor Multi-Agente)

## 1. Filosofía del sistema

Dos roles, nunca mezclados:

- **El orquestador (auditor):** no escribe código. Analiza el estado real del repo, pregunta lo que no esté claro, escribe planes y tareas detalladísimas, y audita los resultados que produce el ejecutor. Decide: avanzar, repetir, o parar y preguntarte.
- **Antigravity 2.0 (ejecutor):** no decide qué hacer. Recibe una tarea clarísima, la reparte entre sus subagentes (siempre en modo multi-agente), la ejecuta con toda su potencia y velocidad, y deja un informe verificable (diff + log) de lo que hizo.

La comunicación entre ambos **nunca es API-a-API en vivo**. Es asíncrona, vía archivos versionados en git. Esto es clave para tu doctrina REAL-ONLY/ZERO-MOCKS: cada decisión y cada ejecución queda como evidencia auditable, no como un resumen que alguien puede inflar (como pasó con el script de populate que bypaseaba los 11 gates).

---

## 2. Estructura de carpetas

```
ultrarentable/
├── orchestration/
│   ├── state/
│   │   ├── status.json              # estado actual de la máquina
│   │   ├── current_phase.md         # tarea activa para Antigravity
│   │   └── plan_maestro.md          # plan completo, fases 1..N (lo escribe el orquestador en Fase 0)
│   ├── results/
│   │   ├── fase_01.log              # informe que deja Antigravity al terminar
│   │   ├── fase_02.log
│   │   └── ...
│   ├── reviews/
│   │   ├── fase_01_review.md        # veredicto del orquestador sobre esa fase
│   │   └── ...
│   ├── scripts/
│   │   ├── run_agy.sh               # Loop A: dispara Antigravity
│   │   └── run_orchestrator_review.sh       # Loop B: dispara la revisión del orquestador
│   └── logs/
│       └── orchestrator.log         # log técnico de los dos crons
└── (resto del repo ultrarentable normal)
```

Todo esto vive dentro del repo y se commitea en cada paso. El historial de git ES el registro de auditoría.

---

## 3. Fase 0 — Setup inicial (una sola vez, no es loop)

Esto lo hacés conversando conmigo directo (o vía Claude Code, no vía cron). No se automatiza porque necesita tu input.

1. Le pegás al orquestador el estado real del repo: `git log`, estructura de carpetas, resultado de los 11 gates, qué está roto (ej. thresholds de FONDEO, el script de populate).
2. El orquestador hace un análisis profundo y te devuelve una lista de preguntas / puntos a confirmar — nada se asume, todo lo ambiguo se pregunta.
3. Con tus respuestas, el orquestador escribe `orchestration/state/plan_maestro.md`: fases numeradas, cada una con objetivo, criterio de éxito verificable (qué gate debe pasar, qué test debe correr), y dependencias entre fases.
4. El orquestador escribe la primera tarea concreta en `current_phase.md` (ver plantilla en sección 6).
5. Seteás `status.json` en `pending`.

A partir de acá arranca el loop automático.

---

## 4. El loop (máquina de estados)

Dos crons independientes, cada uno revisa `status.json` y actúa solo si le toca.

```
pending → (Loop A: Agy ejecuta) → done → (Loop B: el orquestador revisa) → pending (avanza)
                                                                 → pending (repite fase actual con corrección)
                                                                 → needs_user_input (para todo, te avisa)
```

### Loop A — Antigravity ejecuta (cron, cada X min, ej. cada 15 min)

```bash
#!/bin/bash
# orchestration/scripts/run_agy.sh
STATE=orchestration/state
cd "$(dirname "$0")/../.."

STATUS=$(jq -r '.status' "$STATE/status.json")
if [ "$STATUS" != "pending" ]; then
  exit 0
fi

jq '.status = "in_progress"' "$STATE/status.json" > tmp && mv tmp "$STATE/status.json"
PHASE=$(jq -r '.phase_number' "$STATE/status.json")

antigravity run --workspace . "$(cat "$STATE/current_phase.md")" \
  > "orchestration/results/fase_$(printf '%02d' "$PHASE").log" 2>&1

jq '.status = "done"' "$STATE/status.json" > tmp && mv tmp "$STATE/status.json"

git add -A && git commit -m "agy: ejecución fase $PHASE" -q
```

### Loop B — El orquestador revisa (cron, cada X min, ej. cada 20 min, desfasado del Loop A)

```bash
#!/bin/bash
# orchestration/scripts/run_orchestrator_review.sh
STATE=orchestration/state
cd "$(dirname "$0")/../.."

STATUS=$(jq -r '.status' "$STATE/status.json")
if [ "$STATUS" != "done" ]; then
  exit 0
fi

PHASE=$(jq -r '.phase_number' "$STATE/status.json")
LOG="orchestration/results/fase_$(printf '%02d' "$PHASE").log"
DIFF=$(git diff HEAD~1 HEAD)

# Llamada a la API del orquestador (el proveedor que elijas) con el contexto de la fase + el diff + los gates
# El prompt debe incluir: plan_maestro.md, current_phase.md, el log, el diff, y los 11 gates
python3 orchestration/scripts/orchestrator_review.py \
  --phase "$PHASE" --log "$LOG" --diff "$DIFF" \
  --plan "$STATE/plan_maestro.md" \
  --out "orchestration/reviews/fase_$(printf '%02d' "$PHASE")_review.md"

# orchestrator_review.py debe parsear el veredicto que el orquestador devuelve en JSON al final:
# {"veredicto": "avanza|repite|needs_user_input", "siguiente_fase_md": "...", "razon": "..."}
```

`orchestrator_review.py` es un script chico que llama al endpoint de mensajes con el orquestador, le pasás el veredicto estructurado (pedile al orquestador que termine su respuesta con un bloque JSON), y según el campo `veredicto`:

- **avanza:** escribe la nueva `current_phase.md`, incrementa `phase_number`, `status = pending`.
- **repite:** reescribe `current_phase.md` con la corrección que indicó el orquestador, mismo `phase_number`, `status = pending`.
- **needs_user_input:** `status = needs_user_input`, ningún cron vuelve a tocar nada hasta que vos cambies el estado manualmente. Acá conviene un aviso (ver sección 7).

---

## 5. Formato de `status.json`

```json
{
  "phase_number": 3,
  "status": "pending",
  "last_updated": "2026-08-29T23:40:00Z",
  "history": [
    {"phase": 1, "veredicto": "avanza"},
    {"phase": 2, "veredicto": "repite", "razon": "gate 7 no pasó, threshold FONDEO mal calculado"}
  ]
}
```

## 6. Plantilla de `current_phase.md` (lo que el orquestador le deja a Agy)

Debe ser tan detallada que Antigravity no tenga que interpretar nada:

```markdown
# Fase N: [nombre corto]

## Objetivo
[una frase, verificable]

## Contexto necesario
[archivos relevantes, decisiones previas, qué NO tocar]

## Subagentes sugeridos
- Subagente 1: [tarea específica]
- Subagente 2: [tarea específica]
(Antigravity decide el reparto final, pero se le da la descomposición sugerida)

## Criterio de éxito (verificable, no subjetivo)
- [ ] Gate X pasa con datos reales (cero mocks)
- [ ] Test Y corre y da resultado Z
- [ ] No se tocan los archivos: [lista]

## Qué reportar al terminar
- Diff de los archivos modificados
- Resultado exacto de correr los gates/tests
- Cualquier decisión que tomó el subagente que no estaba explícita acá
```

---

## 7. Notificaciones cuando el loop se frena

Cuando `status = needs_user_input`, conviene que te enteres sin tener que estar chequeando. Con tu setup de Hermes ya tenés la pieza para esto: un hook simple que, al detectar ese estado, te mande un mensaje (Telegram, etc.) con el resumen de `fase_N_review.md`.

---

## 8. Costo y estabilidad

- El orquestador solo se invoca en los checkpoints de revisión (Loop B), no en cada paso de código — así el gasto de API queda acotado y predecible.
- Cachea el `plan_maestro.md` en el prompt del orquestador (prompt caching) ya que se repite en cada revisión sin cambiar.
- Si un `current_phase.md` falla 2-3 veces seguidas con `repite`, forzá `needs_user_input` automáticamente en vez de dejar que el loop gire indefinidamente — evita quemar tokens en un ciclo roto.

---

## 9. Checklist de implementación

- [ ] Crear estructura de carpetas `orchestration/`
- [ ] Correr Fase 0 a mano con el orquestador (conversación directa, no cron)
- [ ] Escribir `plan_maestro.md` y primer `current_phase.md`
- [ ] Probar `run_agy.sh` a mano una vez (sin cron) y confirmar que el log se genera bien
- [ ] Escribir `orchestrator_review.py` y probarlo a mano contra ese log
- [ ] Confirmar que el JSON de veredicto se parsea bien y actualiza `status.json` correcto
- [ ] Recién ahí, meter los dos scripts en cron con horarios desfasados
- [ ] Agregar el hook de notificación para `needs_user_input`
