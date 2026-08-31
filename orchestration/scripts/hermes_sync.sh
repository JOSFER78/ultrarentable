#!/usr/bin/env bash
# hermes_sync.sh — Latido del Orquestador (cada 5 min, decision #19 DOCTRINA §14).
#
# Barato por diseno: en cada latido solo LEE ficheros. Solo invoca a Claude (coste real de
# tokens) cuando hay trabajo de verdad:
#   1. Antigravity ha dejado DONE  -> hay que auditar y despachar la siguiente fase.
#   2. status=in_progress congelado -> AGY se ha colgado; hay que intervenir.
#   3. status=pending con GO viejo  -> AGY no ha arrancado; hay que reactivarlo.
# En cualquier otro caso escribe una linea de latido y sale sin gastar nada.
#
# SEGURIDAD: la invocacion NO usa bypass de permisos. Usa una allowlist explicita de
# herramientas (--allowedTools). Los hooks de ~/.claude/settings.json siguen activos
# (bloqueo de comandos destructivos). git commit/push y rm quedan fuera de la allowlist.

set -uo pipefail

REPO="/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
STATE="$REPO/orchestration/state"
LOGS="$REPO/orchestration/logs"
LOCK="$LOGS/hermes_sync.lock"
LOG="$LOGS/hermes_sync.log"
CLAUDE_BIN="/home/ubuntu/.npm-global/bin/claude"

STALE_INPROGRESS_MIN=45   # AGY trabajando mas de esto sin DONE = colgado
STALE_PENDING_MIN=20      # GO publicado y AGY sin arrancar = reactivar

mkdir -p "$LOGS"
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
say() { echo "$(ts) $*" >> "$LOG"; }

# --- Cerrojo: nunca dos latidos a la vez -------------------------------------
exec 9>"$LOCK"
if ! flock -n 9; then
  say "SKIP  latido anterior aun corriendo"
  exit 0
fi

[ -x "$CLAUDE_BIN" ] || { say "ERROR claude CLI no encontrado en $CLAUDE_BIN"; exit 1; }
[ -f "$STATE/status.json" ] || { say "ERROR status.json no existe"; exit 1; }

STATUS=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('status','?'))" "$STATE/status.json" 2>/dev/null || echo "PARSE_ERROR")
PHASE=$(python3 -c "import json,sys;print(json.load(open(sys.argv[1])).get('phase_number','?'))" "$STATE/status.json" 2>/dev/null || echo "?")

age_min() {  # edad de un fichero en minutos; 999999 si no existe
  if [ -f "$1" ]; then echo $(( ( $(date +%s) - $(stat -c %Y "$1") ) / 60 )); else echo 999999; fi
}

REASON=""
if   [ -f "$STATE/DONE" ]; then
  REASON="DONE presente: Antigravity dice haber terminado la fase $PHASE. Audita su informe."
elif [ "$STATUS" = "in_progress" ] && [ "$(age_min "$STATE/status.json")" -gt "$STALE_INPROGRESS_MIN" ]; then
  REASON="status=in_progress congelado mas de $STALE_INPROGRESS_MIN min en la fase $PHASE. Antigravity puede estar colgado: comprueba si hay progreso real."
elif [ "$STATUS" = "pending" ] && [ -f "$STATE/GO" ] && [ "$(age_min "$STATE/GO")" -gt "$STALE_PENDING_MIN" ]; then
  REASON="GO de la fase $PHASE publicado hace mas de $STALE_PENDING_MIN min y Antigravity no ha arrancado (sigue pending)."
elif [ "$STATUS" = "PARSE_ERROR" ]; then
  REASON="status.json ilegible o corrupto. Repara el estado del loop."
fi

if [ -z "$REASON" ]; then
  say "OK    status=$STATUS phase=$PHASE (sin trabajo, 0 tokens)"
  exit 0
fi

say "WAKE  status=$STATUS phase=$PHASE -> $REASON"

PROMPT="Eres HERMES, el Orquestador de Ultrarentable. Latido automatico del cron (no hay usuario delante).

MOTIVO DE ESTE DESPERTAR: $REASON

Lee en este orden y actua:
1. orchestration/DOCTRINA_ORQUESTADOR.md (sobre todo la seccion 14: las 20 decisiones selladas por el usuario)
2. orchestration/state/plan_maestro.md (plan v3 'EL MOTOR PRIMERO')
3. orchestration/state/status.json y orchestration/state/current_phase.md
4. El informe de Antigravity en orchestration/results/fase_<NN>.log si existe

REGLAS INNEGOCIABLES:
- AUDITA CON TUS PROPIOS COMANDOS. Nunca te fies del informe de Antigravity: tiende a ir rapido y a
  inventarse lo que no sabe. Re-ejecuta tu mismo los comandos clave y compara con lo que dice el informe.
- Si el informe afirma algo sin evidencia cruda reproducible: veredicto 'repite'.
- El usuario te dio AUTONOMIA TOTAL (decision 20): despacha tu mismo la siguiente fase escribiendo
  orchestration/state/current_phase.md y publicando orchestration/state/GO con phase=<N> y
  task_sha256=<sha256 de current_phase.md>. No esperes al usuario.
- Tu veredicto se escribe en orchestration/reviews/. La carpeta results/ es solo de Antigravity.
- PROHIBIDO: git commit, git push, rm. Cero datos inventados.
- 2-3 veredictos 'repite' seguidos sobre la misma fase => status='needs_user_input' y paras.
- Si terminaste de auditar: borra el fichero DONE antes de publicar el siguiente GO.

Se breve en la salida. Actua, no narres."

cd "$REPO" || exit 1
timeout 1800 "$CLAUDE_BIN" -p "$PROMPT" \
  --allowedTools "Read" "Write" "Edit" "Glob" "Grep" \
                 "Bash(git status:*)" "Bash(git diff:*)" "Bash(git log:*)" "Bash(git show:*)" \
                 "Bash(grep:*)" "Bash(ls:*)" "Bash(cat:*)" "Bash(head:*)" "Bash(tail:*)" \
                 "Bash(wc:*)" "Bash(find:*)" "Bash(sha256sum:*)" "Bash(stat:*)" "Bash(du:*)" \
                 "Bash(python3:*)" "Bash(pytest:*)" "Bash(curl:*)" "Bash(sqlite3:*)" \
                 "Bash(systemctl status:*)" "Bash(ps:*)" "Bash(ss:*)" \
  >> "$LOGS/hermes_sync_claude.log" 2>&1
RC=$?
say "DONE  invocacion de Hermes terminada rc=$RC"
exit 0
