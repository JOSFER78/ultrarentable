<#
.SYNOPSIS
  agy_matar.ps1 - Mata un arbol de procesos de agy (raiz y descendientes) garantizando
  la proteccion estricta de procesos de campana/mineria (gobernanza_recursos, mine.py,
  cola_mineria, sqcli, next build), sus descendientes y toda su cadena de ancestros hasta la raiz.

.PARAMETER ProcesoId
  PID de la raiz del arbol a terminar (posicional o -ProcesoId).

.PARAMETER Forzar
  Si se especifica, mata los procesos no protegidos del arbol conservando los protegidos,
  sus ancestros y sus descendientes. Si no se especifica y hay protegidos, se niega a matar.

.PARAMETER Proteger
  Patron regex de procesos a proteger. Por defecto: 'gobernanza_recursos|mine\.py|cola_mineria|sqcli|next build'

.EXAMPLE
  .\scripts\orq\agy_matar.ps1 12345
  .\scripts\orq\agy_matar.ps1 -ProcesoId 12345 -Forzar
#>
[CmdletBinding()]
param(
    [Parameter(Position=0, Mandatory=$true)]
    [int]$ProcesoId,

    [Parameter(Mandatory=$false)]
    [switch]$Forzar,

    [Parameter(Mandatory=$false)]
    [string]$Proteger = 'gobernanza_recursos|mine\.py|cola_mineria|sqcli|next build'
)

$ErrorActionPreference = "Stop"

if ($ProcesoId -le 0) {
    Write-Host "Error: Debe especificar un PID valido."
    return
}

$allProcesses = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue
$procMap = @{}
$childrenMap = @{}

foreach ($p in $allProcesses) {
    $curId = [int]$p.ProcessId
    $parentInt = [int]$p.ParentProcessId
    $procMap[$curId] = $p
    if (-not $childrenMap.ContainsKey($parentInt)) {
        $childrenMap[$parentInt] = @()
    }
    $childrenMap[$parentInt] += $curId
}

if (-not $procMap.ContainsKey($ProcesoId)) {
    Write-Host ("raiz {0}: no existe ningun proceso con ese PID." -f $ProcesoId)
    return
}

# 1. Obtener todo el subarbol con raiz en $ProcesoId (BFS)
$subtreePids = @()
$queue = New-Object System.Collections.Queue
$queue.Enqueue($ProcesoId)
$visited = New-Object 'System.Collections.Generic.HashSet[int]'
[void]$visited.Add($ProcesoId)

while ($queue.Count -gt 0) {
    $curr = $queue.Dequeue()
    $subtreePids += $curr
    if ($childrenMap.ContainsKey($curr)) {
        foreach ($childPid in $childrenMap[$curr]) {
            if ($visited.Add($childPid)) {
                $queue.Enqueue($childPid)
            }
        }
    }
}

# 2. Identificar procesos directamente protegidos dentro del subarbol
$matchingProtectedPids = @()
foreach ($nodeId in $subtreePids) {
    if ($procMap.ContainsKey($nodeId)) {
        $p = $procMap[$nodeId]
        $cmd = if ($p.CommandLine) { $p.CommandLine } else { "" }
        if ($cmd -match $Proteger) {
            $matchingProtectedPids += $nodeId
        }
    }
}

# 3. Construir el conjunto protegido completo:
#    - El propio proceso protegido
#    - Todos sus descendientes (BFS descendente)
#    - Toda su cadena de ancestros hasta la raiz $ProcesoId
$protectedSet = New-Object 'System.Collections.Generic.HashSet[int]'

foreach ($protNodeId in $matchingProtectedPids) {
    [void]$protectedSet.Add($protNodeId)

    # Descendientes del protegido
    $qDown = New-Object System.Collections.Queue
    $qDown.Enqueue($protNodeId)
    while ($qDown.Count -gt 0) {
        $node = $qDown.Dequeue()
        [void]$protectedSet.Add($node)
        if ($childrenMap.ContainsKey($node)) {
            foreach ($c in $childrenMap[$node]) {
                if ($protectedSet.Add($c)) {
                    $qDown.Enqueue($c)
                }
            }
        }
    }

    # Ancestros del protegido hasta la raiz del subarbol
    $curr = $protNodeId
    while ($curr -ne $ProcesoId -and $procMap.ContainsKey($curr)) {
        $parentPid = [int]$procMap[$curr].ParentProcessId
        if ($parentPid -gt 0) {
            [void]$protectedSet.Add($parentPid)
            $curr = $parentPid
        } else {
            break
        }
    }
    if ($matchingProtectedPids.Count -gt 0) {
        [void]$protectedSet.Add($ProcesoId)
    }
}

# 4. Evaluacion de guardarrail: si hay protegidos y no hay -Forzar, NEGARSE
if ($matchingProtectedPids.Count -gt 0) {
    $descList = $matchingProtectedPids | ForEach-Object { "{0}({1})" -f $procMap[$_].Name, $_ }
    if (-not $Forzar) {
        Write-Host ("Se niega a matar el arbol PID {0}: contiene procesos protegidos ({1}). Use -Forzar para terminar unicamente los no protegidos." -f $ProcesoId, ($descList -join ', '))
        return
    } else {
        Write-Host ("Aviso: Se encontraron procesos protegidos ({0}). Se conservan los protegidos, sus ancestros y sus descendientes." -f ($descList -join ', '))
    }
}

# 5. Filtrar victimas (procesos del subarbol que NO estan en $protectedSet)
$victimas = @()
foreach ($nodeId in $subtreePids) {
    if (-not $protectedSet.Contains($nodeId)) {
        $victimas += $nodeId
    }
}

# 6. Matar victimas en orden inverso (hijos antes que padres)
$matadosCount = 0
foreach ($vId in ($victimas | Sort-Object -Descending)) {
    try {
        Stop-Process -Id $vId -Force -ErrorAction Stop
        $matadosCount++
    } catch {
        # ignorar si ya cerro
    }
}

$protListStr = if ($matchingProtectedPids.Count -gt 0) {
    ($matchingProtectedPids | ForEach-Object { "{0}({1})" -f $procMap[$_].Name, $_ }) -join ' '
} else {
    "ninguno"
}

Write-Host ("raiz {0}: matados {1}; protegidos: {2}" -f $ProcesoId, $matadosCount, $protListStr)
