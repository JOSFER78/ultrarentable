#!/bin/bash
# orchestration/scripts/run_orchestrator_review.sh — Loop B (ADAPTADO: sin commit)
#
# Prepara el paquete de revisión de la fase actual y lo deja listo para que el
# orquestador (Hermes) audite. NO llama a APIs, NO hace git commit — el registro de
# auditoría son los archivos de orchestration/ (results/, reviews/, history).
#
# Comportamiento:
#   - Si status != 'done': no hace nada (exit 0).
#   - Si status == 'done': monta el contexto (plan + tarea + informe) en
#     orchestration/reviews/fase_NN_context.md para que el orquestador lo revise y
#     escriba su veredicto en orchestration/reviews/fase_NN_review.md.

set -euo pipefail
ORCH="$(cd "$(dirname "$0")/.." && pwd)"
STATE="$ORCH/state"
STATUS_FILE="$STATE/status.json"

STATUS=$(jq -r '.status' "$STATUS_FILE")
if [ "$STATUS" != "done" ]; then
  exit 0
fi

PHASE=$(jq -r '.phase_number' "$STATUS_FILE")
NN=$(printf '%02d' "$PHASE")
LOG="$ORCH/results/fase_${NN}.log"
REVIEW="$ORCH/reviews/fase_${NN}_review.md"

if [ ! -s "$LOG" ]; then
  echo "ERROR: informe vacío o inexistente: $LOG" >&2
  echo "Antigravity aún no dejó resultados para la fase $PHASE." >&2
  exit 1
fi

# Empaquetar contexto de revisión para el orquestador (Hermes)
CONTEXT="$ORCH/reviews/fase_${NN}_context.md"
{
  echo "# Contexto de revisión — Fase $PHASE ($(date -u +%Y-%m-%dT%H:%M:%SZ))"
  echo
  echo "## state/status.json"
  echo '```json'; cat "$STATUS_FILE"; echo '```'
  echo
  echo "## state/current_phase.md (tarea entregada)"
  echo '```markdown'; cat "$STATE/current_phase.md"; echo '```'
  echo
  echo "## results/fase_${NN}.log (informe de Antigravity)"
  echo '```'; cat "$LOG"; echo '```'
  echo
  echo "## Instrucción al orquestador"
  echo "Escribe tu veredicto en reviews/fase_${NN}_review.md terminando con un bloque JSON:"
  echo '{"veredicto": "avanza|repite|needs_user_input", "razon": "..."}'
  echo "Tras escribirlo, actualiza state/status.json según el veredicto (avanza => fase+1"
  echo "y nueva current_phase.md; repite => misma fase con corrección; needs_user_input =>"
  echo "parar el loop). NO hagas git commit."
} > "$CONTEXT"

echo "Contexto de revisión listo: $CONTEXT"
echo "Veredicto esperado en: $REVIEW"
