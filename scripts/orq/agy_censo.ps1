<#
.SYNOPSIS
  agy_censo.ps1 - Censo de procesos agy.exe en ejecucion: PID, hora de arranque,
  worktree asociado (segun logs de antigravity-cli), numero de descendientes,
  consumo en MB y deteccion de descendientes protegidos.

.PARAMETER Json
  Si se especifica, emite la salida en formato JSON (siempre un array).

.PARAMETER LogDir
  Ruta a la carpeta de logs de antigravity-cli. Por defecto: ~/.gemini/antigravity-cli/log.

.EXAMPLE
  .\scripts\orq\agy_censo.ps1
  .\scripts\orq\agy_censo.ps1 -Json
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [switch]$Json,

    [Parameter(Mandatory=$false)]
    [string]$LogDir = (Join-Path $HOME ".gemini\antigravity-cli\log"),

    [Parameter(Mandatory=$false)]
    [string]$PatronProtegido = 'gobernanza_recursos|mine\.py|cola_mineria|sqcli|next build'
)

$ErrorActionPreference = "Stop"

# Mapa de PID -> Worktree a partir de los logs cli-*.log
$pidWorktreeMap = @{}
if (Test-Path $LogDir) {
    $logFiles = Get-ChildItem -Path (Join-Path $LogDir "cli-*.log") -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending
    foreach ($logFile in $logFiles) {
        try {
            $content = Get-Content -Path $logFile.FullName -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($content -and $content -match 'Starting language server process with pid\s+(\d+)') {
                $lp = [int]$matches[1]
                if (-not $pidWorktreeMap.ContainsKey($lp)) {
                    if ($content -match 'workspaceDirs=\[([^\]]*)\]') {
                        $wt = $matches[1].Trim()
                        $pidWorktreeMap[$lp] = $wt
                    } else {
                        $pidWorktreeMap[$lp] = "NO DATA"
                    }
                }
            }
        } catch {
            # ignorar fallos de lectura de logs individuales
        }
    }
}

# Obtener todos los procesos del sistema para mapear relaciones padre-hijo
$allProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
$agyProcesses = Get-Process agy -ErrorAction SilentlyContinue

$resultados = @()

if ($agyProcesses) {
    foreach ($a in $agyProcesses) {
        $pidNum = $a.Id
        $startTime = try { $a.StartTime.ToString("yyyy-MM-dd HH:mm:ss") } catch { "NO DATA" }
        $worktree = if ($pidWorktreeMap.ContainsKey($pidNum)) { $pidWorktreeMap[$pidNum] } else { "NO DATA" }

        # Medir descendientes y buscar protegidos por BFS
        $queue = New-Object System.Collections.Queue
        $queue.Enqueue($pidNum)
        $numDescendientes = 0
        $totalBytes = $a.WorkingSet64
        $tieneProtegidos = $false
        $detallesProtegidos = @()

        while ($queue.Count -gt 0) {
            $currPid = $queue.Dequeue()
            $hijos = $allProcesses | Where-Object { $_.ParentProcessId -eq $currPid }
            foreach ($hijo in $hijos) {
                $numDescendientes++
                $totalBytes += $hijo.WorkingSetSize
                $cmdLine = if ($hijo.CommandLine) { $hijo.CommandLine } else { "" }
                if ($cmdLine -match $PatronProtegido) {
                    $tieneProtegidos = $true
                    $detallesProtegidos += ("{0}({1})" -f $hijo.Name, $hijo.ProcessId)
                }
                $queue.Enqueue($hijo.ProcessId)
            }
        }

        $mbTotal = [math]::Round($totalBytes / 1MB, 1)

        $item = [PSCustomObject]@{
            pid                 = $pidNum
            hora_arranque       = $startTime
            worktree            = $worktree
            descendientes       = $numDescendientes
            mb                  = $mbTotal
            protegidos          = $tieneProtegidos
            detalles_protegidos = $detallesProtegidos
        }
        $resultados += $item
    }
}

if ($Json) {
    if (-not $resultados -or $resultados.Count -eq 0) {
        "[]"
    } elseif ($resultados.Count -eq 1) {
        "[" + ($resultados[0] | ConvertTo-Json -Depth 4) + "]"
    } else {
        $resultados | ConvertTo-Json -Depth 4
    }
} else {
    Write-Host ("=== CENSO AGY ({0}) ===" -f (Get-Date).ToString("yyyy-MM-dd HH:mm:ss"))
    if ($resultados.Count -eq 0) {
        Write-Host "No hay procesos agy.exe en ejecucion."
    } else {
        Write-Host ("{0,-8} {1,-20} {2,-15} {3,-8} {4,-12} {5}" -f "PID", "ARRANQUE", "DESCENDIENTES", "MB", "PROTEGIDOS", "WORKTREE")
        Write-Host ("-" * 100)
        foreach ($r in $resultados) {
            $protStr = if ($r.protegidos) { "SI (" + ($r.detalles_protegidos -join ",") + ")" } else { "NO" }
            Write-Host ("{0,-8} {1,-20} {2,-15} {3,-8} {4,-12} {5}" -f $r.pid, $r.hora_arranque, $r.descendientes, $r.mb, $protStr, $r.worktree)
        }
        $totMb = ($resultados | Measure-Object -Property mb -Sum).Sum
        $totDesc = ($resultados | Measure-Object -Property descendientes -Sum).Sum
        Write-Host ("-" * 100)
        Write-Host ("Total: {0} agy | {1} descendientes | {2} MB total" -f $resultados.Count, $totDesc, $totMb)
    }
}
