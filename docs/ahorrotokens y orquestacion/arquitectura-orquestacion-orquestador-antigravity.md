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
│   │   ├── fase_01.json             # salida de agy (--output json) para esa fase
│   │   ├── fase_02.json
│   │   └── ...
│   ├── reviews/
│   │   ├── fase_01_review.md        # veredicto del orquestador sobre esa fase
│   │   └── ...
│   ├── scripts/
│   │   ├── run_agy.sh               # despacha una tarea a Antigravity vía CLI
│   │   └── run_orchestrator_review.sh  # (solo Modo B) dispara la revisión automática
│   └── logs/
│       └── orchestrator.log         # log técnico si usás cron
└── (resto del repo ultrarentable normal)
```

Todo esto vive dentro del repo y se commitea en cada paso. El historial de git ES el registro de auditoría.

---

## 3. Fase 0 — Setup inicial (una sola vez, no es loop)

Esto lo hacés conversando con el orquestador directo (en Claude Code, con Opus 5 seleccionado). No se automatiza porque necesita tu input.

1. Le pegás al orquestador el estado real del repo: `git log`, estructura de carpetas, resultado de los 11 gates, qué está roto (ej. thresholds de FONDEO, el script de populate).
2. El orquestador hace un análisis profundo y te devuelve una lista de preguntas / puntos a confirmar — nada se asume, todo lo ambiguo se pregunta.
3. Con tus respuestas, el orquestador escribe `orchestration/state/plan_maestro.md`: fases numeradas, cada una con objetivo, criterio de éxito verificable (qué gate debe pasar, qué test debe correr), y dependencias entre fases.
4. El orquestador escribe la primera tarea concreta en `current_phase.md` (ver plantilla en sección 9).

A partir de acá arranca el despacho de tareas a Antigravity.

---

## 4. Cómo se comunican en la práctica: el orquestador manda tareas vía la CLI de Antigravity

Antigravity 2.0 tiene una CLI oficial (binario `agy`, instalado normalmente en `~/.local/bin/agy`) pensada justo para esto: ejecución headless/scripteable, sin abrir la app de escritorio.

Piezas clave que necesitás saber:

- **Modo headless de un solo prompt:** `agy -p "texto"` manda el prompt, imprime la respuesta en stdout y sale. Los diagnósticos (auth, progreso, permisos) van a stderr — así la salida que capturás queda limpia.
- **Prompts largos (tu `current_phase.md` completo):** usá `--prompt-file` en vez de pegar todo en el argumento: `agy -p --prompt-file orchestration/state/current_phase.md`
- **`--yes`:** confirma automáticamente los permisos que normalmente te preguntaría en la UI. Sin esto, si Antigravity corre sin nadie mirando (cron, o vos atendiendo otra cosa), se puede quedar colgado esperando una confirmación que nunca llega.
- **`--output json`:** te devuelve algo parseable con `jq` en vez de texto libre — mucho más fácil de auditar programáticamente.
- **Credenciales:** nunca las pases como argumento de línea de comandos (quedan en el historial de shell y en `ps`); usá variable de entorno.
- El CLI se actualiza seguido (es el reemplazo reciente de Gemini CLI), así que confirmá los flags exactos con `agy --help` en tu instalación antes de scriptear en serio.

Comando típico de despacho:

```bash
agy -p --prompt-file orchestration/state/current_phase.md \
    --yes --output json \
    > orchestration/results/fase_$(printf '%02d' "$PHASE").json
```

Con esto ya tenés la pieza que faltaba: el orquestador (vos hablándole a Opus 5) genera el contenido de `current_phase.md`, y ese comando es el que efectivamente "le manda la tarea" a Antigravity.

---

## 5. La máquina de estados (el loop)

```
pending → (Antigravity ejecuta) → done → (el orquestador revisa) → pending (avanza)
                                                                  → pending (repite fase actual con corrección)
                                                                  → needs_user_input (para todo, te avisa)
```

Hay dos formas de correr este loop. Empezá por el Modo A — es el más fácil de armar y de debuggear porque lo ves todo en vivo.

---

## 6. Modo A — El loop dentro de Claude Code (recomendado para arrancar)

Acá no hay cron ni scripts Python separados: **Claude Code, con Opus 5 como modelo, es literalmente el orquestador**, y usa su propia herramienta de bash para despachar y leer resultados de Antigravity dentro de la misma sesión.

**1. Ponés esto en el `CLAUDE.md` del proyecto** (o en el prompt de la conversación si preferís no fijarlo):

```markdown
Rol: sos el orquestador de este proyecto. Nunca edites código vos mismo.

Cuando haga falta ejecutar una fase:
1. Escribí la tarea en orchestration/state/current_phase.md siguiendo la
   plantilla de orchestration/state/plan_maestro.md.
2. Despachala con bash:
   agy -p --prompt-file orchestration/state/current_phase.md --yes --output json
3. Leé el JSON de salida + corré `git diff` para ver lo que Antigravity
   realmente cambió.
4. Verificá contra los 11 gates (real, no confíes en el resumen de Antigravity).
5. Escribí tu veredicto en orchestration/reviews/fase_N_review.md y decime
   si avanzás, repetís, o necesitás que yo confirme algo.
```

**2. (Opcional) creás un comando corto** `.claude/commands/despachar.md` con ese mismo flujo, para no repetirlo cada vez — lo invocás con `/despachar`.

**3. Corrés la sesión de Claude Code normal.** Opus 5 escribe la tarea, corre `agy` por bash, lee el resultado, audita, y decide el siguiente paso — todo en la misma conversación. Vos ves cada paso y podés frenar o corregir en cualquier momento.

Esto te da el ciclo completo (planear → despachar → auditar → decidir → repetir) sin infraestructura extra. Es el punto de partida correcto: probalo a mano varias fases antes de pensar en automatizarlo sin supervisión.

---

## 7. Modo B — Loop 100% automático por cron (para cuando ya esté probado)

Una vez que viste el Modo A funcionar bien varias veces, podés sacar a Claude Code del medio y automatizar con dos crons que hacen exactamente lo mismo sin que vos estés mirando.

### Cron A — despacha a Antigravity (cada X min, ej. cada 15 min)

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

agy -p --prompt-file "$STATE/current_phase.md" --yes --output json \
  > "orchestration/results/fase_$(printf '%02d' "$PHASE").json" 2> "orchestration/logs/fase_$(printf '%02d' "$PHASE")_stderr.log"

jq '.status = "done"' "$STATE/status.json" > tmp && mv tmp "$STATE/status.json"
git add -A && git commit -m "agy: ejecución fase $PHASE" -q
```

### Cron B — el orquestador revisa (cada X min, ej. cada 20 min, desfasado del Cron A)

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
RESULT="orchestration/results/fase_$(printf '%02d' "$PHASE").json"
DIFF=$(git diff HEAD~1 HEAD)

# Llamada a la API del orquestador (el proveedor que uses) con el contexto de la fase + el diff + los gates
python3 orchestration/scripts/orchestrator_review.py \
  --phase "$PHASE" --result "$RESULT" --diff "$DIFF" \
  --plan "$STATE/plan_maestro.md" \
  --out "orchestration/reviews/fase_$(printf '%02d' "$PHASE")_review.md"

# orchestrator_review.py debe parsear el veredicto que el orquestador devuelve en JSON al final:
# {"veredicto": "avanza|repite|needs_user_input", "siguiente_fase_md": "...", "razon": "..."}
```

`orchestrator_review.py` es un script chico que llama al endpoint de mensajes del orquestador, le pasás el veredicto estructurado (pedile que termine su respuesta con un bloque JSON), y según el campo `veredicto`:

- **avanza:** escribe la nueva `current_phase.md`, incrementa `phase_number`, `status = pending`.
- **repite:** reescribe `current_phase.md` con la corrección indicada, mismo `phase_number`, `status = pending`.
- **needs_user_input:** `status = needs_user_input`, ningún cron vuelve a tocar nada hasta que vos cambies el estado manualmente (ver sección 10 para el aviso).

---

## 8. Formato de `status.json`

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

## 9. Plantilla de `current_phase.md` (lo que el orquestador le deja a Antigravity)

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

## 10. Notificaciones cuando el loop se frena

Cuando `status = needs_user_input` (solo aplica en Modo B, en Modo A ya lo estás viendo en vivo), conviene que te enteres sin tener que estar chequeando. Con tu setup de Hermes ya tenés la pieza para esto: un hook simple que, al detectar ese estado, te mande un mensaje (Telegram, etc.) con el resumen de `fase_N_review.md`.

---

## 11. Costo y estabilidad

- El orquestador solo se invoca en los checkpoints de revisión, no en cada paso de código — así el gasto de API queda acotado y predecible.
- Cachea el `plan_maestro.md` en el prompt del orquestador (prompt caching) ya que se repite en cada revisión sin cambiar.
- Si un `current_phase.md` falla 2-3 veces seguidas con `repite`, forzá `needs_user_input` automáticamente en vez de dejar que el loop gire indefinidamente — evita quemar tokens en un ciclo roto.
- En Modo B, no confíes solo en el exit code de `agy`: puede devolver 0 aunque el objetivo real no se haya cumplido. Revisá siempre el JSON de resultado Y el diff real.

---

## 12. Checklist de implementación

- [ ] Instalar `agy` (CLI de Antigravity) en la máquina/VPS donde corre Claude Code
- [ ] Crear estructura de carpetas `orchestration/`
- [ ] Correr Fase 0 a mano con el orquestador (conversación directa en Claude Code)
- [ ] Escribir `plan_maestro.md` y primer `current_phase.md`
- [ ] Probar el Modo A (sección 6) varias veces a mano — ver que el ciclo completo funcione en vivo
- [ ] Recién cuando el Modo A esté estable, considerar automatizarlo con el Modo B (cron)
- [ ] Si vas a Modo B: probar `run_agy.sh` y `orchestrator_review.py` sueltos antes de meterlos en cron
- [ ] Agregar el hook de notificación para `needs_user_input`
