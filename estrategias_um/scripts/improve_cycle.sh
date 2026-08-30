#!/usr/bin/env bash
# =============================================================================
# improve_cycle.sh - Ciclo de mejora por fases para Ultra_Matrix (SQX headless)
# ---------------------------------------------------------------------------
# Restricciones verificadas en vivo (2026-08-29):
#   - NO se puede copiar entre databanks con el proyecto corriendo.
#   - NO se puede lanzar el task Improve (startOnlyTask task=2) con el
#     proyecto corriendo ("Project is already running").
#   - Los databanks viven en memoria: el copy debe hacerse con el proyecto
#     parado, usando el snapshot del banco Last generation / LastGeneration.
#   - Se usa transporte -run file= para soportar nombres con espacios.
# Por tanto el ciclo es FASES:
#   1. Si Build corre y Semillero (Last generation + LastGeneration) >= THRESHOLD: parar proyecto.
#   2. Copiar Last generation / LastGeneration -> ToImprove (snapshot para investigacion).
#   3. Lanzar SOLO task 2 (Improve): consume ToImprove, escribe variantes
#      optimizadas en Results_robust_20260809.
#   4. Al terminar Improve: exportar Results_robust a CSV y re-arrancar Build.
# Candado: si state=improving, cualquier invocacion posterior sale sin tocar
# nada (seguro ante disparos concurrentes del cron de 15 min).
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

call_cli() {
    local cmd="$1"
    local tf
    tf=$(mktemp /tmp/sqx_cmd_XXXXXX.txt)
    echo "$cmd" > "$tf"
    api "-run%20file=${tf}"
    rm -f "$tf"
}

count_of() { # count_of <databank> -> entero desde action=list
    local target="$1"
    local dblist
    dblist=$(api "-databank%20action=list%20project=${PROJECT}")
    echo "$dblist" | grep -F "${target}," | grep -oE 'Records:[[:space:]]*[0-9]+' | grep -oE '[0-9]+' | head -n1
}

project_running() {
    local s1 s2
    s1=$(api "-project%20action=status%20name=${PROJECT}" | grep 'Estrategias generadas' | grep -oE '[0-9]+')
    sleep 2
    s2=$(api "-project%20action=status%20name=${PROJECT}" | grep 'Estrategias generadas' | grep -oE '[0-9]+')
    if [ -n "$s1" ] && [ -n "$s2" ] && [ "$s1" -ne "$s2" ]; then
        return 0
    else
        return 1
    fi
}
stop_project() {
    api "-project%20action=stop%20name=${PROJECT}" >/dev/null
    for i in {1..30}; do
        if ! project_running; then return 0; fi
        sleep 1
    done
}

STATE=$(cat "$STATE_FILE" 2>/dev/null || echo idle_build)
log "=== tick state=${STATE} threshold=${THRESHOLD}"

if [ "$STATE" = "improving" ]; then
    # Fase 4 vigilada por otro proceso: aqui solo comprobamos si quedo colgado
    if project_running; then
        log "improve en curso; no interfiere"
    else
        log "improve termino; exportando y re-arrancando Build"
        mkdir -p "$EXPORT_DIR"
        call_cli "-databank action=export project=${PROJECT} name=\"Results_robust_20260809\" file=\"${EXPORT_DIR}/improved_$(date -u +%Y%m%d_%H%M).csv\"" >> "$LOGF" 2>&1
        echo idle_build > "$STATE_FILE"
        api "-project%20action=start%20name=${PROJECT}" >/dev/null
        log "Build re-arrancado; ciclo completado"
    fi
    exit 0
fi

# state=idle_build
LG1=$(count_of "Last generation")
LG2=$(count_of "LastGeneration")
LG=$(( ${LG1:-0} + ${LG2:-0} ))
log "Semillero total=${LG} (Last generation=${LG1:-0}, LastGeneration=${LG2:-0})"

if ! project_running; then
    log "Build NO corre (motor parado o proyecto idle); no hago nada"
    exit 0
fi
if [ "${LG:-0}" -lt "$THRESHOLD" ]; then
    log "Semillero (${LG}) < threshold (${THRESHOLD}); espero"
    exit 0
fi

# --- FASES CRITICAS: parar -> copiar -> mejorar ---
log "FASE 1: parando proyecto"
stop_project
if project_running; then log "ERROR: el proyecto no se paro; aborto"; exit 1; fi

log "FASE 2: copiando semillero -> ToImprove"
if [ "${LG1:-0}" -gt 0 ]; then
    call_cli "-databank action=copy project=${PROJECT} name=\"Last generation\" destproject=${PROJECT} destdatabank=ToImprove" >> "$LOGF" 2>&1
fi
if [ "${LG2:-0}" -gt 0 ]; then
    call_cli "-databank action=copy project=${PROJECT} name=\"LastGeneration\" destproject=${PROJECT} destdatabank=ToImprove" >> "$LOGF" 2>&1
fi

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
