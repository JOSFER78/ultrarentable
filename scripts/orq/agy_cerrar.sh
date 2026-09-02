#!/usr/bin/env bash
# scripts/orq/agy_cerrar.sh <ID> [<dispatchId>] [--sin-worktree] [--issue N] [--etiqueta integrado|repite]
# Cierre completo y seguro de un agente agy en Orca:
# 1. orca orchestration worker-release --dispatch <ctx> (con timeout 25)
# 2. orca terminal stop --worktree path:<ruta>
# 3. censo: ningún agy.exe del worktree vivo y ningún MCP huérfano
# 4. junctions: eliminación segura con [IO.DirectoryInfo]::Delete() y verificación de destino
# 5. git -C <checkout principal> worktree remove --force <ruta> + worktree prune
# 6. gh issue edit N --add-label <etiqueta> --remove-label en-vuelo (+ close si integrado)
# 7. resumen final y registro JSON en orchestration/state/agentes.jsonl
set -euo pipefail

ID=""
DISPATCH_ID=""
SIN_WORKTREE=0
ISSUE_NUM=""
ETIQUETA="integrado"

if [ $# -lt 1 ]; then
  echo "Uso: $0 <ID> [<dispatchId>] [--sin-worktree] [--issue N] [--etiqueta integrado|repite]"
  echo "Ejemplo: $0 B15 ctx_675fbc52ee66 --sin-worktree --issue 42 --etiqueta integrado"
  exit 1
fi

ID="$1"
shift

while [ $# -gt 0 ]; do
  case "$1" in
    --sin-worktree)
      SIN_WORKTREE=1
      shift
      ;;
    --issue)
      if [ $# -lt 2 ]; then
        echo "[cerrar $ID] paso 0: FALLO falta valor para --issue"
        exit 1
      fi
      ISSUE_NUM="$2"
      shift 2
      ;;
    --etiqueta)
      if [ $# -lt 2 ]; then
        echo "[cerrar $ID] paso 0: FALLO falta valor para --etiqueta"
        exit 1
      fi
      ETIQUETA="$2"
      if [ "$ETIQUETA" != "integrado" ] && [ "$ETIQUETA" != "repite" ]; then
        echo "[cerrar $ID] paso 0: FALLO etiqueta invalida '$ETIQUETA' (debe ser 'integrado' o 'repite')"
        exit 1
      fi
      shift 2
      ;;
    ctx_*|wtr_*|*)
      if [ -z "$DISPATCH_ID" ] && [[ "$1" != --* ]]; then
        DISPATCH_ID="$1"
        shift
      else
        echo "[cerrar $ID] paso 0: FALLO parametro desconocido '$1'"
        exit 1
      fi
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable"
WTPATH="C:/Users/yo/orca/workspaces/ultrarentable/agy-$ID"
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"

# ==============================================================================
# PASO 1: worker-release (con timeout 25; si falta ctx, buscar por agentTerminalHandle)
# ==============================================================================
if [ -z "$DISPATCH_ID" ]; then
  # Buscar dispatch en worker-list por terminalHandle / worktree
  DISPATCH_ID=$("$PY" - "$ID" <<'PYEOF'
import json, subprocess, sys
target_id = sys.argv[1].lower()
wt_target = f"agy-{target_id}"

try:
    res = subprocess.run(["orca", "orchestration", "worker-list", "--json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    data = json.loads(res.stdout) if res.stdout.strip() else {}
except Exception:
    data = {}

workers = data.get("result", {}).get("workers", [])

try:
    res_t = subprocess.run(["orca", "terminal", "list", "--json"], capture_output=True, text=True, encoding="utf-8", errors="replace")
    data_t = json.loads(res_t.stdout) if res_t.stdout.strip() else {}
except Exception:
    data_t = {}

terminals = {t.get("handle"): (t.get("worktreePath") or "").lower() for t in data_t.get("result", {}).get("terminals", [])}

matched = ""
for w in reversed(workers):
    wt_id = (w.get("resource", {}).get("worktreeId") or "").lower()
    if wt_target in wt_id:
        matched = w.get("dispatchId", "")
        break
    handle = w.get("agentTerminalHandle")
    if handle and handle in terminals:
        if wt_target in terminals[handle]:
            matched = w.get("dispatchId", "")
            break

print(matched)
PYEOF
  )
fi

if [ -n "$DISPATCH_ID" ]; then
  # Ejecutar orca orchestration worker-release con timeout 25s
  RELEASE_OUT=""
  set +e
  if command -v timeout >/dev/null 2>&1; then
    RELEASE_OUT=$(timeout 25 orca orchestration worker-release --dispatch "$DISPATCH_ID" --json 2>&1)
    RC_RELEASE=$?
  elif [ -x "/usr/bin/timeout" ]; then
    RELEASE_OUT=$(/usr/bin/timeout 25 orca orchestration worker-release --dispatch "$DISPATCH_ID" --json 2>&1)
    RC_RELEASE=$?
  else
    RELEASE_OUT=$(orca orchestration worker-release --dispatch "$DISPATCH_ID" --json 2>&1)
    RC_RELEASE=$?
  fi
  set -e

  if [ $RC_RELEASE -ne 0 ]; then
    echo "[cerrar $ID] paso 1: FALLO worker-release fallo para $DISPATCH_ID (rc=$RC_RELEASE): $RELEASE_OUT"
    exit 1
  fi
  echo "[cerrar $ID] paso 1: OK worker-release completado ($DISPATCH_ID)"
else
  echo "[cerrar $ID] paso 1: OK (sin worker dispatch registrado)"
fi

# ==============================================================================
# PASO 2: orca terminal stop --worktree path:<ruta>
# ==============================================================================
set +e
STOP_OUT=$(orca terminal stop --worktree "path:$WTPATH" --json 2>&1)
RC_STOP=$?
set -e

if [ $RC_STOP -ne 0 ]; then
  echo "[cerrar $ID] paso 2: FALLO terminal stop fallo para path:$WTPATH (rc=$RC_STOP): $STOP_OUT"
  exit 1
fi
echo "[cerrar $ID] paso 2: OK terminal detenido (path:$WTPATH)"

# ==============================================================================
# PASO 3: Censo (ningún agy.exe del worktree vivo; agy_matar.ps1 sin -Forzar; purga MCP huérfanos)
# ==============================================================================
CENSO_RES=$("$PY" - "$WTPATH" "$SCRIPT_DIR" <<'PYEOF'
import json, os, subprocess, sys

wt_target = sys.argv[1].replace("/", "\\").lower()
script_dir = sys.argv[2]

# 1. Obtener censo actual de agy.exe
ps_censo = f"powershell.exe -NoProfile -ExecutionPolicy Bypass -File {script_dir}/agy_censo.ps1 -Json"
try:
    res = subprocess.run(ps_censo, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    data = json.loads(res.stdout) if res.stdout.strip() else []
except Exception:
    data = []

# Buscar PIDs de agy correspondientes a este worktree
pids_to_kill = []
for item in data:
    wt = (item.get("worktree") or "").replace("/", "\\").lower()
    if wt == wt_target or (wt_target and wt_target in wt):
        pids_to_kill.append(item.get("pid"))

# Matar cada uno sin -Forzar
for pid in pids_to_kill:
    if pid:
        cmd_matar = f"powershell.exe -NoProfile -ExecutionPolicy Bypass -File {script_dir}/agy_matar.ps1 -ProcesoId {pid}"
        subprocess.run(cmd_matar, shell=True, capture_output=True, text=True)

# 2. Purgar procesos MCP huérfanos
ps_mcp = """
$allProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
$runningPids = New-Object 'System.Collections.Generic.HashSet[int]'
foreach ($p in $allProcs) { [void]$runningPids.Add([int]$p.ProcessId) }
$mcpPattern = '\\.gemini|mcp|gbrain|tradingview|notebooklm|obsidian'
$protPattern = 'gobernanza_recursos|mine\\.py|cola_mineria|sqcli|next build'
foreach ($p in $allProcs) {
    $cmd = if ($p.CommandLine) { $p.CommandLine } else { "" }
    if ($cmd -match $mcpPattern -and $cmd -notmatch $protPattern) {
        $parentPidInt = [int]$p.ParentProcessId
        if ($parentPidInt -eq 0 -or (-not $runningPids.Contains($parentPidInt))) {
            try { Stop-Process -Id $p.ProcessId -Force -ErrorAction Stop } catch {}
        }
    }
}
"""
subprocess.run(f"powershell.exe -NoProfile -Command \"{ps_mcp}\"", shell=True, capture_output=True, text=True)

# 3. Re-verificar censo
try:
    res_after = subprocess.run(ps_censo, shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
    data_after = json.loads(res_after.stdout) if res_after.stdout.strip() else []
except Exception:
    data_after = []

alive_for_wt = []
for item in data_after:
    wt = (item.get("worktree") or "").replace("/", "\\").lower()
    if wt == wt_target or (wt_target and wt_target in wt):
        alive_for_wt.append(item.get("pid"))

if alive_for_wt:
    print(f"ERROR: PIDs de agy aún vivos para worktree: {alive_for_wt}")
    sys.exit(1)

print("OK")
PYEOF
)

if [ "$CENSO_RES" != "OK" ]; then
  echo "[cerrar $ID] paso 3: FALLO censo residual: $CENSO_RES"
  exit 1
fi
echo "[cerrar $ID] paso 3: OK censo limpio (0 agy para worktree, 0 MCP huerfanos)"

# ==============================================================================
# PASO 4: Junctions (eliminación con [IO.DirectoryInfo]::Delete(), verificación de destino)
# ==============================================================================
JUNC_OUT=$(powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "& {
  `$ErrorActionPreference = 'Stop'
  `$wt = '$WTPATH'
  if (-not (Test-Path `$wt)) {
    Write-Host 'OK (worktree no existe)'
    exit 0
  }

  function Find-ReparsePoints(`$dir) {
    `$points = @()
    if (-not (Test-Path `$dir)) { return `$points }
    `$items = Get-ChildItem -Path `$dir -Force -ErrorAction SilentlyContinue
    foreach (`$item in `$items) {
      if (`$item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
        `$points += `$item
      } elseif (`$item.PSIsContainer) {
        `$points += Find-ReparsePoints `$item.FullName
      }
    }
    return `$points
  }

  `$junctions = Find-ReparsePoints `$wt

  # 1. Verificación fail-closed de todos los destinos antes de borrar
  `$targetsToVerify = @()
  foreach (`$j in `$junctions) {
    `$targets = `$j.Target
    `$tPath = if (`$targets -and `$targets.Count -gt 0) { `$targets[0] } else { `$null }
    if ([string]::IsNullOrWhiteSpace(`$tPath) -or (-not (Test-Path `$tPath))) {
      Write-Error ('FAIL-CLOSED: Destino de junction inalcanzable: ' + `$j.FullName + ' -> ' + `$tPath)
      exit 1
    }
    `$cnt = (Get-ChildItem -Path `$tPath -Force).Count
    `$targetsToVerify += [PSCustomObject]@{
      JunctionPath = `$j.FullName
      TargetPath   = `$tPath
      EntryCount   = `$cnt
    }
  }

  # 2. Eliminación segura y comprobación de integridad
  foreach (`$t in `$targetsToVerify) {
    `$jPath = `$t.JunctionPath
    `$tPath = `$t.TargetPath
    `$expCount = `$t.EntryCount

    (New-Object IO.DirectoryInfo `$jPath).Delete()
    if (Test-Path `$jPath) {
      Write-Error ('No se pudo eliminar junction: ' + `$jPath)
      exit 1
    }
    if (-not (Test-Path `$tPath)) {
      Write-Error ('FATAL: Destino desaparecio: ' + `$tPath)
      exit 1
    }
    `$afterCount = (Get-ChildItem -Path `$tPath -Force).Count
    if (`$afterCount -ne `$expCount) {
      Write-Error ('FATAL: Discrepancia en entradas destino (' + `$expCount + ' vs ' + `$afterCount + ')')
      exit 1
    }
  }
  Write-Host ('OK (' + `$targetsToVerify.Count + ' junctions eliminadas con destino integro)')
}" 2>&1)

if echo "$JUNC_OUT" | grep -qi "error"; then
  echo "[cerrar $ID] paso 4: FALLO eliminacion de junctions: $JUNC_OUT"
  exit 1
fi
echo "[cerrar $ID] paso 4: OK junctions verificadas y eliminadas ($JUNC_OUT)"

# ==============================================================================
# PASO 5: worktree remove + prune (omitido si --sin-worktree)
# ==============================================================================
if [ "$SIN_WORKTREE" -eq 1 ]; then
  echo "[cerrar $ID] paso 5: OMITIDO (--sin-worktree)"
else
  set +e
  WT_REM_OUT=""
  if [ -d "$WTPATH" ]; then
    WT_REM_OUT=$(git -C "$MAIN" worktree remove --force "$WTPATH" 2>&1)
    RC_REM=$?
  else
    RC_REM=0
  fi
  WT_PRUNE_OUT=$(git -C "$MAIN" worktree prune 2>&1)
  RC_PRUNE=$?
  set -e

  if [ $RC_REM -ne 0 ] || [ $RC_PRUNE -ne 0 ]; then
    echo "[cerrar $ID] paso 5: FALLO git worktree remove/prune fallo: $WT_REM_OUT $WT_PRUNE_OUT"
    exit 1
  fi
  echo "[cerrar $ID] paso 5: OK worktree eliminado y podado ($WTPATH)"
fi

# ==============================================================================
# PASO 6: gh issue edit / close
# ==============================================================================
if [ -n "$ISSUE_NUM" ]; then
  set +e
  GH_EDIT_OUT=$(gh issue edit "$ISSUE_NUM" --add-label "$ETIQUETA" --remove-label "en-vuelo" 2>&1)
  RC_GH_EDIT=$?
  RC_GH_CLOSE=0
  GH_CLOSE_OUT=""
  if [ "$ETIQUETA" = "integrado" ]; then
    GH_CLOSE_OUT=$(gh issue close "$ISSUE_NUM" 2>&1)
    RC_GH_CLOSE=$?
  fi
  set -e

  if [ $RC_GH_EDIT -ne 0 ] || [ $RC_GH_CLOSE -ne 0 ]; then
    echo "[cerrar $ID] paso 6: FALLO gh issue edit/close fallo para #$ISSUE_NUM: $GH_EDIT_OUT $GH_CLOSE_OUT"
    exit 1
  fi
  echo "[cerrar $ID] paso 6: OK issue #$ISSUE_NUM actualizado con etiqueta '$ETIQUETA' y cerrado si integrado"
else
  echo "[cerrar $ID] paso 6: OMITIDO (sin --issue)"
fi

# ==============================================================================
# PASO 7: Resumen final en una línea y registro JSON en orchestration/state/agentes.jsonl
# ==============================================================================
STATE_DIR="$(cd "$SCRIPT_DIR/../../orchestration/state" 2>/dev/null && pwd || echo "")"
if [ -n "$STATE_DIR" ]; then
  mkdir -p "$STATE_DIR"
  HORA="$(date +'%Y-%m-%d %H:%M:%S')"
  echo "{\"evento\": \"cierre\", \"id\": \"$ID\", \"hora\": \"$HORA\", \"worktree\": \"$WTPATH\", \"dispatch\": \"$DISPATCH_ID\", \"sin_worktree\": $SIN_WORKTREE, \"issue\": \"$ISSUE_NUM\", \"etiqueta\": \"$ETIQUETA\"}" >> "$STATE_DIR/agentes.jsonl"
  echo "[cerrar $ID] paso 7: OK registrado en orchestration/state/agentes.jsonl"
fi

echo "[cerrar $ID] Cierre completado con exito para agente $ID"
