#!/usr/bin/env bash
# scripts/orq/agy_lanzar.sh <ID> "<titulo>" <fichero_spec>
# Receta verificada para lanzar agentes agy limpios y supervisados en Orca.
#
# PROHIBICION: codex esta TERMINANTEMENTE PROHIBIDO (orden de Emilio del 2026-09-02).
# Solo se permiten agentes agy puros con gemini-3.7-flash-high.
set -euo pipefail

ID="${1:-}"
TITULO="${2:-}"
SPEC_FILE="${3:-}"

if [ -z "$ID" ] || [ -z "$TITULO" ] || [ -z "$SPEC_FILE" ]; then
  echo "Uso: $0 <ID> \"<titulo>\" <fichero_spec>"
  echo "Ejemplo: $0 B15 \"Higiene sostenible de agentes agy\" orchestration/agy/GO_B15.md"
  exit 1
fi

# Guardarrail anti-codex
if echo "$ID $TITULO $SPEC_FILE" | grep -qi "codex"; then
  echo "ERROR: codex esta PROHIBIDO por Emilio (2026-09-02). Use unicamente agy."
  exit 1
fi

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
if [ ! -d "$WTPATH" ]; then
  orca worktree create --name "agy/$ID" --base-branch "$BASE" --setup skip --comment "GO_$ID: $TITULO" --json > /tmp/wt_$ID.json 2>&1 || true
fi

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

# 4. Crear terminal con comando PURO
log "Paso 4: Creando terminal en Orca con comando puro..."
CMD="agy --model gemini-3.7-flash-high --dangerously-skip-permissions"
H=$(orca terminal create --worktree "$WT" --title "agy-$ID" --command "$CMD" --json 2>&1 | grep -o 'term_[a-f0-9-]*' | head -1 || true)
if [ -z "$H" ]; then
  sleep 10
  H=$(orca terminal list --json 2>&1 | node -e 'let s="";process.stdin.on("data",d=>s+=d).on("end",()=>{const j=JSON.parse(s);const wt=process.argv[1];const c=(j.result.terminals||[]).filter(t=>(t.worktreePath||"")===wt&&!/^PS C:/.test((t.preview||"").trim())).map(t=>t.handle);console.log(c[c.length-1]||"");});' "$WTPATH" || true)
fi

if [ -z "$H" ]; then
  log "ERROR: No se pudo crear ni recuperar el terminal para $ID"
  exit 1
fi
log "Terminal creado: $H"

# 5. Esperar banner de Antigravity CLI
log "Paso 5: Esperando arranque de Antigravity CLI..."
contestado=0
for i in $(seq 1 45); do
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
  sleep 4
done

# 6. Esperar a que la interfaz TUI este lista
log "Paso 6: Esperando tui-idle..."
ok=$(orca terminal wait --terminal "$H" --for tui-idle --timeout-ms 240000 --json 2>&1 | grep -o '"satisfied": *true' || true)
if [ -z "$ok" ]; then
  log "ERROR: tui-idle no alcanzado"
  orca terminal read --terminal "$H" 2>&1 | tail -6 || true
  exit 1
fi

# 7. Crear tarea y arrancar worker supervisado
log "Paso 7: Creando tarea y vinculando worker..."
if [ ! -f "$SPEC_FILE" ]; then
  log "ERROR: Fichero de especificacion $SPEC_FILE no existe"
  exit 1
fi
SPEC_CONTENT="$(cat "$SPEC_FILE")"
T=$(orca orchestration task-create --task-title "$ID $TITULO" --display-name "$ID $TITULO" --spec "$SPEC_CONTENT" --run "$RUN" --json 2>&1 | grep -o 'task_[a-f0-9]*' | head -1 || true)
if [ -z "$T" ]; then
  log "ERROR: task-create fallo"
  exit 1
fi

R=$(orca orchestration worker-start --task "$T" --worktree "$WT" --terminal "$H" --run "$RUN" --json 2>&1)
D=$(echo "$R" | grep -o 'ctx_[a-f0-9]*' | head -1 || true)
ST=$(echo "$R" | grep -o '"state": *"[a-z_]*"' | head -1 || true)
log "Worker arrancado: task=$T dispatch=$D $ST terminal=$H"

# 8. Medicion a los 45s: verificar que los descendientes sean solo shells
log "Paso 8: Esperando 45s para auditar higiene de procesos descendientes..."
sleep 45

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

if [ "$PARASITO_DETECTADO" -gt 0 ]; then
  log "ERROR: Se detectaron procesos parasitos no-shell ($PARASITO_DETECTADO). Matando arbol PID $AGY_PID..."
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$SCRIPT_DIR/agy_matar.ps1" -Pid "$AGY_PID" -Forzar
  exit 1
fi

log "Higiene verificada: PID=$AGY_PID Hijos=$NUM_HIJOS MB=$MB_TOTAL (0 parasitos)"

# 9. Registrar en orchestration/state/agentes.jsonl
STATE_DIR="$(cd "$SCRIPT_DIR/../../orchestration/state" 2>/dev/null && pwd || echo "")"
if [ -n "$STATE_DIR" ]; then
  mkdir -p "$STATE_DIR"
  HORA="$(date +'%Y-%m-%d %H:%M:%S')"
  echo "{\"id\": \"$ID\", \"hora\": \"$HORA\", \"pid\": $AGY_PID, \"worktree\": \"$WTPATH\", \"hijos\": $NUM_HIJOS, \"mb\": $MB_TOTAL, \"task\": \"$T\", \"dispatch\": \"$D\"}" >> "$STATE_DIR/agentes.jsonl"
  log "Registrado en $STATE_DIR/agentes.jsonl"
fi

log "Agente $ID despachado y verificado exitosamente."
