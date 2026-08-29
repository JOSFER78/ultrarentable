#!/usr/bin/env bash
# =============================================================================
# improve_cycle.sh - Ciclo de mejora por fases para Ultra_Matrix (SQX headless)
# ---------------------------------------------------------------------------
# Restricciones verificadas en vivo (2026-08-29):
#   - NO se puede copiar entre databanks con el proyecto corriendo.
#   - NO se puede lanzar el task Improve (startOnlyTask task=2) con el
#     proyecto corriendo ("Project is already running").
#   - Los databanks viven en memoria: el copy debe hacerse con el proyecto
#     parado, usando el snapshot del banco LastGeneration (salida del Build).
# Por tanto el ciclo es FASES:
#   1. Si Build corre y LastGeneration >= THRESHOLD: parar proyecto.
#   2. Copiar LastGeneration -> ToImprove (snapshot para investigacion).
#   3. Lanzar SOLO task 2 (Improve): consume ToImprove, escribe variantes
#      optimizadas en Results_robust_20260809.
#   4. Al terminar Improve: exportar Results_robust a CSV y re-arrancar Build.
# Candado: si state=improving, cualquier invocacion posterior sale sin tocar
# nada (seguro ante disparos concurrentes del cron de 30 min).
# Uso: ./improve_cycle.sh [THRESHOLD]   (default 30)
# =============================================================================
set -u

API="http://localhost:5050/call"
PROJECT="Ultra_Matrix"
STATE_FILE="/home/ubuntu/.improve_cycle_state"
LOGF="/home/ubuntu/improve_cycle.log"
EXPORT_DIR="/home/ubuntu/ORDENAR"
THRESHOLD="${1:-30}"
TS() { date -u '+%F %T'; }
log() { echo "[$(TS)] $*" >> "$LOGF"; }

api() { curl -sS --max-time 60 "${API}?cmd=$1" 2>/dev/null; }
count_of() { # count_of <databank> -> entero
    api "-databank%20action=count%20project=${PROJECT}%20name=$1" \
      | grep -oE 'Records:[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -n1
}
project_running() {
    api "-project%20action=status%20name=${PROJECT}" | grep -q 'Tiempo de funcionamiento'
}
stop_project() { api "-project%20action=stop%20name=${PROJECT}" >/dev/null; sleep 5; }

STATE=$(cat "$STATE_FILE" 2>/dev/null || echo idle_build)
log "=== tick state=${STATE} threshold=${THRESHOLD}"

if [ "$STATE" = "improving" ]; then
    # Fase 4 vigilada por otro proceso: aqui solo comprobamos si quedo colgado
    if project_running; then
        log "improve en curso; no interfiere"
    else
        log "improve termino; exportando y re-arrancando Build"
        mkdir -p "$EXPORT_DIR"
        api "-databank%20action=export%20project=${PROJECT}%20name=Results_robust_20260809%20file=${EXPORT_DIR}/improved_$(date -u +%Y%m%d_%H%M).csv" >> "$LOGF"
        echo idle_build > "$STATE_FILE"
        api "-project%20action=start%20name=${PROJECT}" >/dev/null
        log "Build re-arrancado; ciclo completado"
    fi
    exit 0
fi

# state=idle_build
LG=$(count_of LastGeneration)
log "LastGeneration=${LG}"
if ! project_running; then
    log "Build NO corre (motor parado o proyecto idle); no hago nada"
    exit 0
fi
if [ "${LG:-0}" -lt "$THRESHOLD" ]; then
    log "LastGeneration (${LG}) < threshold (${THRESHOLD}); espero"
    exit 0
fi

# --- FASES CRITICAS: parar -> copiar -> mejorar ---
log "FASE 1: parando proyecto"
stop_project
if project_running; then log "ERROR: el proyecto no se paro; aborto"; exit 1; fi

log "FASE 2: copiando LastGeneration -> ToImprove"
api "-databank%20action=copy%20project=${PROJECT}%20name=LastGeneration%20destproject=${PROJECT}%20destdatabank=ToImprove" >> "$LOGF" 2>&1
TO=$(count_of ToImprove)
log "ToImprove tras copy=${TO}"
if [ "${TO:-0}" -eq 0 ]; then
    log "ERROR: copy no trajo estrategias; re-arranco Build y salgo"
    api "-project%20action=start%20name=${PROJECT}" >/dev/null
    exit 1
fi

log "FASE 3: lanzando Improve (solo task 2)"
echo improving > "$STATE_FILE"
api "-project%20action=startOnlyTask%20name=${PROJECT}%20task=2" >> "$LOGF" 2>&1
sleep 8
if ! project_running; then
    log "ERROR: Improve no arranco; restauro Build"
    echo idle_build > "$STATE_FILE"
    api "-project%20action=start%20name=${PROJECT}" >/dev/null
    exit 1
fi
log "Improve en marcha (estado=improving). El proximo tick exportara y re-arrancara."
