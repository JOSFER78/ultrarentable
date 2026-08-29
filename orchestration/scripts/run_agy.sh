#!/bin/bash
# orchestration/scripts/run_agy.sh — Loop A (ADAPTADO: guía manual, NO ejecuta nada)
#
# ADAPTACIÓN IMPORTANTE: Antigravity corre en el PC DEL USUARIO, no en este VPS.
# Este script NO lanza 'antigravity run' automáticamente: es una GUÍA comentada
# del paso manual del ciclo. El flujo real es:
#
#   1. El usuario abre Antigravity en su PC.
#   2. Le pega (o se lo hace leer) la tarea de orchestration/state/current_phase.md.
#   3. Agy ejecuta la tarea (modo multi-agente) contra el repo y deja su informe en
#      orchestration/results/fase_NN.log (NN = phase_number de status.json, con 2 dígitos).
#   4. El usuario ejecuta ./orchestration/scripts/run_orchestrator_review.sh (o avisa al
#      orquestador Hermes) para que se revise el informe.
#
# NADA de git commit automático: el registro de auditoría son los propios archivos de
# orchestration/ (results/, reviews/, history en status.json).

set -euo pipefail
STATE="$(cd "$(dirname "$0")/.." && pwd)/state"
STATUS_FILE="$STATE/status.json"

PHASE=$(jq -r '.phase_number' "$STATUS_FILE")
STATUS=$(jq -r '.status' "$STATUS_FILE")
LOG="$(cd "$(dirname "$0")/.." && pwd)/results/fase_$(printf '%02d' "$PHASE").log"

echo "== Loop A (guía manual) — fase $PHASE, estado: $STATUS =="

case "$STATUS" in
  needs_user_input)
    echo "Estado needs_user_input: la fase actual requiere visto bueno del usuario."
    echo "Cuando apruebes, cambia status a 'pending' en $STATUS_FILE."
    ;;
  pending)
    echo "Tarea activa: $STATE/current_phase.md"
    echo "1) Abre Antigravity en tu PC y pégale esta tarea."
    echo "2) Cuando Agy termine, guarda su informe en: $LOG"
    echo "3) Ejecuta run_orchestrator_review.sh para que el orquestador la revise."
    ;;
  in_progress)
    echo "Fase $PHASE en curso. Agy debe dejar el informe en: $LOG"
    ;;
  done)
    echo "Fase $PHASE marcada done. Ejecuta run_orchestrator_review.sh."
    ;;
  *)
    echo "Estado desconocido: $STATUS — no se hace nada."
    ;;
esac

# Placeholder del comando original del doc de arquitectura (NO descomentar aquí:
# antigravity vive en el PC del usuario; esto solo documenta el comando que ALLÍ se usa):
#   antigravity run --workspace . "$(cat orchestration/state/current_phase.md)" \
#     > orchestration/results/fase_$(printf '%02d' $PHASE).log 2>&1
#
# Y el cambio de estado que ese flujo provocaría (manual aquí):
#   jq '.status = "done"' "$STATUS_FILE" > tmp && mv tmp "$STATUS_FILE"
