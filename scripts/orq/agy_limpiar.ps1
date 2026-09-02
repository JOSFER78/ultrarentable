<#
.SYNOPSIS
  agy_limpiar.ps1 - Limpieza de agentes agy y servidores MCP huerfanos.
  Mata los arboles de procesos agy cuyo worktree NO este en la lista -Conservar
  y termina los procesos MCP huerfanos (padre inexistente). Imprime el censo antes y despues.

.PARAMETER Conservar
  Lista de rutas de worktree a conservar, separadas por coma.

.PARAMETER Forzar
  Si se especifica, fuerza la terminacion en agy_matar.ps1 para no-protegidos.

.EXAMPLE
  .\scripts\orq\agy_limpiar.ps1 -Conservar "C:\Users\yo\orca\workspaces\ultrarentable\agy-B15"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$Conservar = "",

    [Parameter(Mandatory=$false)]
    [switch]$Forzar
)

$ErrorActionPreference = "Stop"

Write-Host "=========================================="
Write-Host "===          CENSO ANTES               ==="
Write-Host "=========================================="
& "$PSScriptRoot\agy_censo.ps1"

# Normalizar lista de worktrees a conservar
$conservarList = @()
if (-not [string]::IsNullOrWhiteSpace($Conservar)) {
    $conservarList = $Conservar.Split(',') | ForEach-Object {
        $_.Trim().Replace('/', '\').TrimEnd('\').ToLower()
    }
}

# Obtener mapa PID -> Worktree
$logDir = Join-Path $HOME ".gemini\antigravity-cli\log"
$pidWorktreeMap = @{}
if (Test-Path $logDir) {
    $logFiles = Get-ChildItem -Path (Join-Path $logDir "cli-*.log") -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    foreach ($logFile in $logFiles) {
        try {
            $content = Get-Content -Path $logFile.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($content -and $content -match 'Starting language server process with pid\s+(\d+)') {
                $lp = [int]$matches[1]
                if (-not $pidWorktreeMap.ContainsKey($lp)) {
                    if ($content -match 'workspaceDirs=\[([^\]]*)\]') {
                        $pidWorktreeMap[$lp] = $matches[1].Trim()
                    }
                }
            }
        } catch {}
    }
}

# 1. Evaluar cada proceso agy.exe
$agyProcesses = Get-Process agy -ErrorAction SilentlyContinue
if ($agyProcesses) {
    foreach ($a in $agyProcesses) {
        $agyPid = $a.Id
        $wtRaw = if ($pidWorktreeMap.ContainsKey($agyPid)) { $pidWorktreeMap[$agyPid] } else { "" }
        $wtNorm = $wtRaw.Replace('/', '\').TrimEnd('\').ToLower()

        if ([string]::IsNullOrWhiteSpace($wtNorm) -or ($conservarList -notcontains $wtNorm)) {
            Write-Host ("-> Matando arbol de agy PID {0} (worktree '{1}' no esta en lista conservada)..." -f $agyPid, $wtRaw)
            & "$PSScriptRoot\agy_matar.ps1" -Pid $agyPid -Forzar:$Forzar
        } else {
            Write-Host ("-> Conservando agy PID {0} (worktree '{1}')" -f $agyPid, $wtRaw)
        }
    }
}

# 2. Buscar y limpiar procesos MCP huerfanos
$allProcs = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
$runningPids = New-Object 'System.Collections.Generic.HashSet[int]'
foreach ($p in $allProcs) { [void]$runningPids.Add([int]$p.ProcessId) }

$mcpPattern = '\.gemini|mcp|gbrain|tradingview|notebooklm|obsidian'
$protPattern = 'gobernanza_recursos|mine\.py|cola_mineria|sqcli|next build'

$huerfanos = @()
foreach ($p in $allProcs) {
    $cmd = if ($p.CommandLine) { $p.CommandLine } else { "" }
    if ($cmd -match $mcpPattern -and $cmd -notmatch $protPattern) {
        $parentPidInt = [int]$p.ParentProcessId
        if ($parentPidInt -eq 0 -or (-not $runningPids.Contains($parentPidInt))) {
            $huerfanos += $p
        }
    }
}

if ($huerfanos.Count -gt 0) {
    Write-Host ("Se encontraron {0} procesos MCP huerfanos:" -f $huerfanos.Count)
    foreach ($h in $huerfanos) {
        Write-Host ("  Matando huerfano: PID {0} ({1}) - Padre {2} inexistente" -f $h.ProcessId, $h.Name, $h.ParentProcessId)
        try {
            Stop-Process -Id $h.ProcessId -Force -ErrorAction Stop
        } catch {}
    }
} else {
    Write-Host "0 procesos MCP huerfanos detectados."
}

Write-Host "`n=========================================="
Write-Host "===          CENSO DESPUÉS             ==="
Write-Host "=========================================="
& "$PSScriptRoot\agy_censo.ps1"
