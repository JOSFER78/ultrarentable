#!/usr/bin/env bash
# supervisor.sh — Guardarraíles para operación 24/7 autónoma.
#
# Lo lanza el cron cada 10 minutos. Su trabajo NO es hacer el trabajo, es vigilar que se haga:
#   1. Si la campaña se cayó, la relanza (y la campaña se reanuda donde estaba, no desde cero).
#   2. Si la máquina está ahogada, NO la relanza. Espera al siguiente latido.
#   3. Si queda poco disco, PARA todo y avisa. Llenar el disco corrompe SQLite.
#   4. Nunca permite dos instancias a la vez.
#
# Todo lo que decide queda en el log con su motivo. Sin decisiones silenciosas.

set -uo pipefail

REPO="/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
LOGS="$REPO/orchestration/logs"
LOG="$LOGS/supervisor.log"
LOCK="$LOGS/supervisor.lock"
CAMPANA="$REPO/scripts/campana.py"

CARGA_MAX=5.0         # load average de 1 min. En 4 nucleos, por encima de ~5 la maquina ya
                      # va ahogada. Estaba en 12 y el 2026-08-31 se llego a 60 (15x sobre-
                      # suscripcion) con dos campañas y restos de pruebas compitiendo.
DISCO_MIN_GB=5        # por debajo de esto se para todo
MEM_MIN_MB=800        # memoria disponible minima

mkdir -p "$LOGS"
ts() { date -u +"%Y-%m-%dT%H:%M:%SZ"; }
say() { echo "$(ts) $*" >> "$LOG"; }

exec 9>"$LOCK"
if ! flock -n 9; then
  say "SKIP  latido anterior aun corriendo"
  exit 0
fi

# --- Guardarrail 1: disco -----------------------------------------------------
DISCO_GB=$(df -BG --output=avail / | tail -1 | tr -dc '0-9')
if [ "${DISCO_GB:-0}" -lt "$DISCO_MIN_GB" ]; then
  say "ALTO  disco disponible ${DISCO_GB}GB < ${DISCO_MIN_GB}GB. Se detiene la campana."
  pkill -f "python3 scripts/campana.py" 2>/dev/null
  exit 1
fi

# --- Guardarrail 2: memoria ---------------------------------------------------
MEM_MB=$(free -m | awk '/^Mem:/{print $7}')
if [ "${MEM_MB:-0}" -lt "$MEM_MIN_MB" ]; then
  say "ESPERA memoria disponible ${MEM_MB}MB < ${MEM_MIN_MB}MB. No se arranca nada este latido."
  exit 0
fi

# --- Guardarrail 3: una sola instancia ---------------------------------------
# pgrep -fc devuelve el conteo Y sale con codigo 1 si no hay coincidencias, asi que el
# "|| echo 0" anadia un segundo "0" y rompia la comparacion numerica. Se cuenta con wc -l.
VIVAS=$(pgrep -f "python3 scripts/campana.py" 2>/dev/null | wc -l)
if [ "$VIVAS" -gt 1 ]; then
  say "AVISO $VIVAS instancias de la campana. Se dejan las mas antigua y se matan las demas."
  pgrep -f "python3 scripts/campana.py" | tail -n +2 | xargs -r kill
  exit 0
fi
if [ "$VIVAS" -eq 1 ]; then
  say "OK    campana viva, nada que hacer"
  exit 0
fi

# --- Guardarrail 4: carga de la maquina --------------------------------------
CARGA=$(awk '{print $1}' /proc/loadavg)
if awk "BEGIN{exit !($CARGA > $CARGA_MAX)}"; then
  say "ESPERA carga $CARGA > $CARGA_MAX. La campana no se relanza este latido."
  exit 0
fi

# --- Relanzar -----------------------------------------------------------------
if [ ! -f "$CAMPANA" ]; then
  say "ERROR no existe $CAMPANA"
  exit 1
fi
cd "$REPO" || exit 1
# Un hilo de BLAS por proceso: numpy abre uno por nucleo en CADA proceso y eso multiplica
# la carga sin acelerar nada, porque el trabajo por celda es secuencial.
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 \
  nohup nice -n 10 ionice -c 2 -n 7 python3 scripts/campana.py \
  >> "$LOGS/campana_03.log" 2>&1 &
say "ARRANQUE campana relanzada (carga $CARGA, disco ${DISCO_GB}GB, mem ${MEM_MB}MB) PID $!"
exit 0
