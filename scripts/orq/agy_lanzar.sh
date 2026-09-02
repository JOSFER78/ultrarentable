#!/usr/bin/env bash
# scripts/orq/agy_lanzar.sh <ID> "<titulo>" <fichero_spec>
# Receta endurecida v2 para lanzar agentes agy limpios y supervisados en Orca.
#
# PROHIBICION: codex esta TERMINANTEMENTE PROHIBIDO (orden de Emilio del 2026-09-02).
# Solo se permiten agentes agy puros con gemini-3.7-flash-high.
set -euo pipefail

# Funciones reutilizables y comprobables

esperar_worktree() {
  local wt="$1"
  local max_espera="${AGY_LANZAR_MAX_ESPERA:-90}"
  local pasos=$((max_espera / 2))
  [ "$pasos" -lt 1 ] && pasos=1
  for i in $(seq 1 "$pasos"); do
    if [ -d "$wt/.git" ] || [ -f "$wt/.git" ]; then
      return 0
    fi
    sleep 2
  done
  if [ -d "$wt/.git" ] || [ -f "$wt/.git" ]; then
    return 0
  fi
  return 1
}

contestar_encuesta() {
  local h="$1"
  local scr
  scr=$(orca terminal read --terminal "$h" 2>/dev/null || true)
  if echo "$scr" | grep -qi "How's the CLI experience"; then
    echo "[$ID $(date +%H:%M:%S)] Encuesta CLI detectada en terminal $h: contestando 0 (Skip)..."
    orca terminal send --terminal "$h" --text "0" --json >/dev/null 2>&1 || true
    sleep 1
    orca terminal send --terminal "$h" --text $'\r' --json >/dev/null 2>&1 || true
    return 0
  fi
  return 1
}

registrar_agente_json() {
  local outfile="$1"
  local id="$2"
  local hora="$3"
  local pid="$4"
  local wt="$5"
  local t_wt="$6"
  local t_term="$7"
  local t_ban="$8"
  local t_idl="$9"
  local t_sta="${10}"
  local t_tot="${11}"
  local hij="${12}"
  local mb="${13}"
  local reint="${14}" # true | false
  local tsk="${15}"
  local disp="${16}"
  local term="${17}"
  local no_shell="${18:-0}"

  local wt_clean
  wt_clean=$(echo "$wt" | sed 's/\\/\//g')

  printf '{"id":"%s","hora":"%s","pid":%d,"worktree":"%s","t_worktree":%d,"t_terminal":%d,"t_banner":%d,"t_idle":%d,"t_start":%d,"t_total":%d,"hijos":%d,"mb":%d,"reintento_prompt":%s,"task":"%s","dispatch":"%s","terminal":"%s","hijos_no_shell":%d}\n' \
    "$id" "$hora" "$pid" "$wt_clean" \
    "$t_wt" "$t_term" "$t_ban" "$t_idl" "$t_sta" "$t_tot" \
    "$hij" "$mb" "$reint" \
    "$tsk" "$disp" "$term" "$no_shell" >> "$outfile"
}

# Modos de prueba / utilitarios
if [ "${1:-}" = "--source-only" ]; then
  return 0 2>/dev/null || exit 0
fi

if [ "${1:-}" = "--test-esperar-worktree" ]; then
  esperar_worktree "${2:-}"
  exit $?
fi

if [ "${1:-}" = "--test-registrar-json" ]; then
  shift
  registrar_agente_json "$@"
  exit $?
fi

ID="${1:-}"
TITULO="${2:-}"
SPEC_FILE="${3:-}"

if [ -z "$ID" ] || [ -z "$TITULO" ] || [ -z "$SPEC_FILE" ]; then
  echo "Uso: $0 <ID> \"<titulo>\" <fichero_spec>"
  echo "Ejemplo: $0 B19 \"Despacho endurecido\" orchestration/agy/GO_B19.md"
  exit 1
fi

# Guardarrail anti-codex
if echo "$ID $TITULO $SPEC_FILE" | grep -qi "codex"; then
  echo "ERROR: codex esta PROHIBIDO por Emilio (2026-09-02). Use unicamente agy."
  exit 1
fi

t_inicio=$(date +%s)

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO="fd201816-f015-4412-8e3a-c277d3284a04"
BASE="JOSFER78/orquesta-antigravity-max-10"
RUN="run_19da24acd52a"
DEV="C:/Users/yo/orca/workspaces/ultrarentable/devilray"
MAIN="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable"
WTPATH="C:/Users/yo/orca/workspaces/ultrarentable/agy-$ID"
WT="id:${REPO}::${WTPATH}"

log(){ echo "[$ID $(date +%H:%M:%S)] $*"; }

log "Iniciando lanzamiento de agente $ID: $TITULO"

# 1. Vaciar MCP antes de arrancar para evitar carga parasita (D17)
log "Paso 1: Vaciando ficheros de configuracion MCP..."
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/mcp_vacio.ps1"

# 2. Crear worktree propio con --setup skip (sin npm install pesado)
log "Paso 2: Verificando/creando worktree en $WTPATH..."
t0_wt=$(date +%s)
if [ ! -d "$WTPATH" ] || [ ! -e "$WTPATH/.git" ]; then
  if [ ! -d "$WTPATH" ]; then
    orca worktree create --name "agy/$ID" --base-branch "$BASE" --setup skip --comment "GO_$ID: $TITULO" --json > /tmp/wt_$ID.json 2>&1 || true
  fi
  if ! esperar_worktree "$WTPATH"; then
    log "ERROR: worktree en $WTPATH no contiene .git tras esperar timeout"
    exit 1
  fi
  log "worktree listo en $WTPATH tras espera"
fi
t1_wt=$(date +%s)
t_worktree=$((t1_wt - t0_wt))

# Restaurar package-lock.json si hubo drift
git -C "$WTPATH" diff --quiet -- package-lock.json 2>/dev/null || git -C "$WTPATH" checkout -- package-lock.json 2>/dev/null || true

# Junctions necesarias para acelerar segun el tipo de agente
if [ "$ID" = "A12" ] || [ "$ID" = "B10" ] || [ "$ID" = "B16" ] || [ "$ID" = "B17" ]; then
  for pair in "node_modules" "apps/web/node_modules"; do
    [ -e "$WTPATH/$pair" ] || { powershell.exe -NoProfile -Command "New-Item -ItemType Junction -Path '$WTPATH/$pair' -Target '$DEV/$pair' | Out-Null" && log "junction $pair creada"; }
  done
fi

if [ "$ID" = "A08" ] || [ "$ID" = "A09" ] || [ "$ID" = "B02" ] || [ "$ID" = "B03" ] || [ "$ID" = "B05" ] || [ "$ID" = "B11" ]; then
  if [ ! -L "$WTPATH/data/normalized" ] && [ -d "$WTPATH/data/normalized" ] && [ ! -e "$WTPATH/data/normalized.wt" ]; then
    mv "$WTPATH/data/normalized" "$WTPATH/data/normalized.wt"
    powershell.exe -NoProfile -Command "New-Item -ItemType Junction -Path '$WTPATH/data/normalized' -Target '$MAIN/data/normalized' | Out-Null" && echo "data/normalized.wt/" >> "$(git -C "$WTPATH" rev-parse --git-path info/exclude)" && log "junction data/normalized creada"
  fi
fi

# 3. Sembrar confianza en trustedWorkspaces ANTES de arrancar agy
log "Paso 3: Sembrando confianza de workspace..."
"$MAIN/.venv/Scripts/python.exe" - "$WTPATH" <<'PYEOF'
import json, pathlib, sys
p = pathlib.Path.home() / ".gemini" / "antigravity-cli" / "settings.json"
if p.exists():
    j = json.loads(p.read_text(encoding="utf-8"))
else:
    j = {}
tw = j.setdefault("trustedWorkspaces", [])
w = sys.argv[1].replace("/", "\\")
if w not in tw:
    tw.append(w)
    p.write_text(json.dumps(j, indent=2), encoding="utf-8")
    print("Confianza sembrada para:", w)
PYEOF

# Comprobar fichero de especificacion
if [ ! -f "$SPEC_FILE" ]; then
  log "ERROR: Fichero de especificacion $SPEC_FILE no existe"
  exit 1
fi
SPEC_CONTENT="$(cat "$SPEC_FILE")"

# Variables para métricas de fases
H=""
D=""
T=""
t_terminal=0
t_banner=0
t_idle=0
t_start=0

iniciar_terminal_y_worker() {
  local task_id="$1"

  # 4. Crear terminal con comando PURO
  log "Paso 4: Creando terminal en Orca con comando puro..."
  local t0_t=$(date +%s)
  local cmd="agy --model gemini-3.7-flash-high --dangerously-skip-permissions"
  local h
  h=$(orca terminal create --worktree "$WT" --title "agy-$ID" --command "$cmd" --json 2>&1 | grep -o 'term_[a-f0-9-]*' | head -1 || true)
  if [ -z "$h" ]; then
    sleep 10
    h=$(orca terminal list --json 2>&1 | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);const wt=process.argv[1];const c=(j.result.terminals||[]).filter(t=>(t.worktreePath||"")===wt&&!/^PS C:/.test((t.preview||"").trim())).map(t=>t.handle);console.log(c[c.length-1]||"");});' "$WTPATH" || true)
  fi

  if [ -z "$h" ]; then
    log "ERROR: No se pudo crear ni recuperar el terminal para $ID"
    return 1
  fi
  local t1_t=$(date +%s)
  t_terminal=$((t1_t - t0_t))
  H="$h"
  log "Terminal creado: $H (${t_terminal}s)"

  # 5. Esperar banner de Antigravity CLI
  log "Paso 5: Esperando arranque de Antigravity CLI..."
  local t0_b=$(date +%s)
  local contestado=0
  for i in $(seq 1 45); do
    local scr
    scr=$(orca terminal read --terminal "$H" 2>&1 || true)
    if echo "$scr" | grep -qiE "Antigravity CLI [0-9]|gemini-3\.7-flash"; then
      log "Antigravity CLI detectado correctamente"
      break
    fi
    if [ "$contestado" = 0 ] && echo "$scr" | grep -qiE "trust the contents|trust this|Do you trust"; then
      orca terminal send --terminal "$H" --text $'\r' --json >/dev/null 2>&1 || true
      contestado=1
      log "Prompt de confianza contestado"
    fi
    contestar_encuesta "$H" || true
    sleep 4
  done
  local t1_b=$(date +%s)
  t_banner=$((t1_b - t0_b))

  # 6. Esperar a que la interfaz TUI este lista
  log "Paso 6: Esperando tui-idle..."
  local t0_i=$(date +%s)
  local ok
  ok=$(orca terminal wait --terminal "$H" --for tui-idle --timeout-ms 240000 --json 2>&1 | grep -o '"satisfied": *true' || true)
  if [ -z "$ok" ]; then
    log "ERROR: tui-idle no alcanzado"
    orca terminal read --terminal "$H" 2>&1 | tail -6 || true
    return 1
  fi
  local t1_i=$(date +%s)
  t_idle=$((t1_i - t0_i))
  log "tui-idle alcanzado (${t_idle}s)"

  # 7. Vincular worker supervisado
  log "Paso 7: Vinculando worker a tarea $task_id..."
  local t0_s=$(date +%s)
  local r
  r=$(orca orchestration worker-start --task "$task_id" --worktree "$WT" --terminal "$H" --run "$RUN" --json 2>&1)
  local d
  d=$(echo "$r" | grep -o 'ctx_[a-f0-9]*' | head -1 || true)
  local st
  st=$(echo "$r" | grep -o '"state": *"[a-z_]*"' | head -1 || true)
  if [ -z "$d" ]; then
    log "ERROR: worker-start no devolvio dispatchId: $r"
    return 1
  fi
  local t1_s=$(date +%s)
  t_start=$((t1_s - t0_s))
  D="$d"
  log "Worker arrancado: task=$task_id dispatch=$D $st terminal=$H (${t_start}s)"
  return 0
}

# 7. Crear tarea en Orca
log "Paso 7a: Creando tarea en Orca..."
T=$(orca orchestration task-create --task-title "$ID $TITULO" --display-name "$ID $TITULO" --spec "$SPEC_CONTENT" --run "$RUN" --json 2>&1 | grep -o 'task_[a-f0-9]*' | head -1 || true)
if [ -z "$T" ]; then
  log "ERROR: task-create fallo"
  exit 1
fi
log "Tarea creada: $T"

# Despacho inicial
if ! iniciar_terminal_y_worker "$T"; then
  log "ERROR: No se pudo completar el inicio del worker para $T"
  exit 1
fi

# Verificación durante 60s de que el prompt se envió y no falló
log "Verificando envio de prompt durante 60s..."
fallo_prompt=0
for check_step in $(seq 1 6); do
  sleep 10
  contestar_encuesta "$H" || true

  # Comprobar worker-list
  wlist=$(orca orchestration worker-list --json 2>&1 || true)
  disp_status=$(echo "$wlist" | node -e '
    let s="";
    process.stdin.on("data",d=>s+=d).on("end",()=>{
      try {
        const j=JSON.parse(s);
        const w=(j.result.workers||[]).find(x=>x.dispatchId===process.argv[1]);
        console.log(w ? w.dispatchStatus : "");
      } catch(e){ console.log(""); }
    });
  ' "$D" 2>/dev/null || true)

  if [ "$disp_status" = "failed" ]; then
    log "Fallo detectado: dispatchStatus=failed en worker-list para $D"
    fallo_prompt=1
    break
  fi

  # Comprobar si la pantalla sigue mostrando el texto del spec en el cuadro de entrada
  scr=$(orca terminal read --terminal "$H" 2>&1 || true)
  first_spec_line=$(head -n 2 "$SPEC_FILE" | tail -n 1 | tr -d '\r\n')
  if [ -n "$first_spec_line" ] && echo "$scr" | grep -Fq "$first_spec_line" && echo "$scr" | grep -qiE "input|prompt|> " && [ "$check_step" -ge 4 ]; then
    log "Prompt aparentemente atascado en pantalla en paso $check_step"
    fallo_prompt=1
    break
  fi
done

reintento_prompt="false"
if [ "$fallo_prompt" = 1 ]; then
  log "Fallo de prompt detectado. Realizando re-despacho unico..."
  reintento_prompt="true"
  orca terminal stop --worktree "path:$WTPATH" --json >/dev/null 2>&1 || true
  sleep 2
  orca orchestration task-update --id "$T" --status ready --json >/dev/null 2>&1 || true
  log "Tarea $T reseteada a status=ready. Re-iniciando terminal y worker..."
  if ! iniciar_terminal_y_worker "$T"; then
    log "ERROR: Re-despacho fallo al iniciar terminal/worker"
    exit 1
  fi
  log "Re-despacho completado: nuevo dispatch=$D en terminal=$H"
fi

# 8. Medicion a los 45s: vigilar encuesta cada 10s y auditar procesos descendientes
log "Paso 8: Esperando 45s para auditar higiene de procesos descendientes (vigilando encuesta cada 10s)..."
for step in $(seq 1 4); do
  sleep 10
  contestar_encuesta "$H" || true
done
sleep 5
contestar_encuesta "$H" || true

# Evaluar mediante script Python
EVAL_OUT=$("$MAIN/.venv/Scripts/python.exe" - "$WTPATH" "$SCRIPT_DIR" <<'PYEOF'
import json, sys, subprocess

wt_target = sys.argv[1].replace("/", "\\").lower()
script_dir = sys.argv[2]

ps_cmd = f"powershell.exe -NoProfile -ExecutionPolicy Bypass -File {script_dir}/agy_censo.ps1 -Json"
try:
    res = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    data = json.loads(res.stdout) if res.stdout.strip() else []
except Exception as e:
    data = []

matching = None
for item in data:
    wt = (item.get("worktree") or "").replace("/", "\\").lower()
    if wt == wt_target:
        matching = item
        break

if not matching and data:
    matching = data[-1]

if matching:
    agy_pid = matching.get("pid", 0)
    mb = matching.get("mb", 0)
    
    ps_inspect = f"Get-CimInstance Win32_Process | Where-Object {{ $_.ParentProcessId -eq {agy_pid} }} | Select-Object ProcessId, Name, CommandLine"
    res_h = subprocess.run(f"powershell.exe -NoProfile -Command \"{ps_inspect}\"", shell=True, capture_output=True, text=True)
    
    shells = {"powershell.exe", "cmd.exe", "bash.exe", "conhost.exe", "powershell", "cmd", "bash", "conhost"}
    
    parasitos = []
    import re
    lines = res_h.stdout.splitlines()
    for l in lines:
        for s in re.findall(r'(\w+\.exe)', l, re.IGNORECASE):
            if s.lower() not in shells:
                parasitos.append(s)
                
    print(f"PID={agy_pid}")
    print(f"HIJOS={matching.get('descendientes', 0)}")
    print(f"MB={mb}")
    print(f"PARASITOS={len(parasitos)}")
else:
    print("PID=0\nHIJOS=0\nMB=0\nPARASITOS=0")
PYEOF
)

AGY_PID=$(echo "$EVAL_OUT" | grep "^PID=" | cut -d'=' -f2 || echo "0")
NUM_HIJOS=$(echo "$EVAL_OUT" | grep "^HIJOS=" | cut -d'=' -f2 || echo "0")
MB_TOTAL=$(echo "$EVAL_OUT" | grep "^MB=" | cut -d'=' -f2 || echo "0")
PARASITO_DETECTADO=$(echo "$EVAL_OUT" | grep "^PARASITOS=" | cut -d'=' -f2 || echo "0")

t_final=$(date +%s)
t_total=$((t_final - t_inicio))
log "Metricas de arranque: t_total=${t_total}s (wt=${t_worktree}s term=${t_terminal}s banner=${t_banner}s idle=${t_idle}s start=${t_start}s reintento=$reintento_prompt)"

# 9. Registrar en orchestration/state/agentes.jsonl
STATE_DIR="$(cd "$SCRIPT_DIR/../../orchestration/state" 2>/dev/null && pwd || echo "")"
if [ -n "$STATE_DIR" ]; then
  mkdir -p "$STATE_DIR"
  HORA="$(date +'%Y-%m-%d %H:%M:%S')"
  registrar_agente_json "$STATE_DIR/agentes.jsonl" "$ID" "$HORA" "$AGY_PID" "$WTPATH" \
    "$t_worktree" "$t_terminal" "$t_banner" "$t_idle" "$t_start" "$t_total" \
    "$NUM_HIJOS" "$MB_TOTAL" "$reintento_prompt" \
    "$T" "$D" "$H" "$PARASITO_DETECTADO"
  log "Registrado en $STATE_DIR/agentes.jsonl"
fi

if [ "$PARASITO_DETECTADO" -gt 0 ]; then
  log "ERROR: Se detectaron procesos parasitos no-shell ($PARASITO_DETECTADO). Matando arbol PID $AGY_PID..."
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/agy_matar.ps1" -Pid "$AGY_PID" -Forzar
  exit 1
fi

if [ "$t_total" -gt 180 ]; then
  log "ERROR: t_total (${t_total}s) supero el limite maximo de 180s"
  exit 1
fi

log "Higiene y tiempos verificados: PID=$AGY_PID Hijos=$NUM_HIJOS MB=$MB_TOTAL (0 parasitos, t_total=${t_total}s <= 180s)"
log "Agente $ID despachado y verificado exitosamente."
exit 0
