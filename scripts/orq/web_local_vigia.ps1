# -*- coding: utf-8 -*-
# VIGIA DE LA INSTANCIA LOCAL (API :8100 + Web :3100)
#
# Comprueba que la instancia local de Ultrarentable responde y, si no, la vuelve a levantar.
# Pensado para ejecutarse cada pocos minutos desde una tarea programada de Windows
# (ULTRARENTABLE_vigia_local): hace UNA pasada y termina; no se queda vivo.
#
# Regla del proyecto (D8): nada se lanza "a mano y ya"; lo que se deja corriendo resucita solo.
#
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\orq\web_local_vigia.ps1
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\orq\web_local_vigia.ps1 -Instalar
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts\orq\web_local_vigia.ps1 -Desinstalar

param(
    [switch]$Instalar,
    [switch]$Desinstalar,
    [int]$PuertoApi = 8100,
    [int]$PuertoWeb = 3100,
    [int]$TimeoutApiSeg = 15,
    [int]$TimeoutWebSeg = 25
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
$SiteDir = Join-Path $RepoRoot "orchestration\site"
$LogPath = Join-Path $SiteDir "watchdog.log"
$EstadoPath = Join-Path $SiteDir "vigia_estado.json"
$WebLocal = Join-Path $RepoRoot "scripts\orq\web_local.ps1"
$ManifestPath = Join-Path $RepoRoot "apps\web\.next\server\app-paths-manifest.json"
$NombreTarea = "ULTRARENTABLE_vigia_local"

if (-not (Test-Path $SiteDir)) { New-Item -ItemType Directory -Path $SiteDir -Force | Out-Null }

function Write-Vigia([string]$Mensaje) {
    $ts = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $linea = "[$ts] [VIGIA] $Mensaje"
    Add-Content -Path $LogPath -Value $linea -Encoding UTF8
    Write-Host $linea
}

# ---------------------------------------------------------------- instalacion
if ($Instalar) {
    # Se usa schtasks.exe y no Register-ScheduledTask a proposito: Register-ScheduledTask
    # devuelve "Acceso denegado" sin elevacion en esta maquina, y schtasks crea la tarea
    # como el usuario actual sin pedir administrador. Un disparador ONLOGON si exige
    # elevacion, asi que la periodicidad de 3 minutos (indefinida) es la que sostiene el
    # servicio tambien despues de un reinicio.
    $comando = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$PSCommandPath`""
    & schtasks.exe /Create /TN $NombreTarea /TR $comando /SC MINUTE /MO 3 /F /IT /RL LIMITED
    if ($LASTEXITCODE -ne 0) {
        Write-Vigia "FALLO al instalar la tarea '$NombreTarea' (rc=$LASTEXITCODE)."
        exit $LASTEXITCODE
    }
    Write-Vigia "Tarea programada '$NombreTarea' instalada (cada 3 min) sobre $RepoRoot."
    & schtasks.exe /Query /TN $NombreTarea /FO LIST
    exit 0
}

if ($Desinstalar) {
    & schtasks.exe /Delete /TN $NombreTarea /F
    Write-Vigia "Tarea programada '$NombreTarea' desinstalada (rc=$LASTEXITCODE)."
    exit 0
}

# ------------------------------------------------------------------- sondeo
function Test-Endpoint([string]$Url, [int]$TimeoutSeg) {
    try {
        $r = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSeg -ErrorAction Stop
        return [int]$r.StatusCode
    } catch {
        return 0
    }
}

function Test-BuildIntegro() {
    # Un build a medias deja manifiestos vacios: Next arranca y muere con
    # "SyntaxError: Unexpected end of JSON input" en loadManifest.
    if (-not (Test-Path $ManifestPath)) { return $false }
    try {
        $txt = Get-Content -Path $ManifestPath -Raw -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($txt)) { return $false }
        $null = $txt | ConvertFrom-Json
        return $true
    } catch {
        return $false
    }
}

$acciones = @()
$codApi = Test-Endpoint "http://127.0.0.1:$PuertoApi/" $TimeoutApiSeg
$codWeb = Test-Endpoint "http://127.0.0.1:$PuertoWeb/" $TimeoutWebSeg

if ($codApi -eq 200) {
    Write-Vigia "API :$PuertoApi responde (HTTP 200)."
} else {
    Write-Vigia "ALERTA: API :$PuertoApi no responde. Relanzando la instancia local..."
    $acciones += "arrancar-api"
}

$buildIntegro = Test-BuildIntegro
if ($codWeb -eq 200) {
    Write-Vigia "Web :$PuertoWeb responde (HTTP 200)."
} elseif (-not $buildIntegro) {
    Write-Vigia "ALERTA: Web :$PuertoWeb no responde y el build de produccion esta incompleto ($ManifestPath). Reconstruyendo..."
    $acciones += "reconstruir-web"
} else {
    Write-Vigia "ALERTA: Web :$PuertoWeb no responde (build integro). Relanzando..."
    $acciones += "arrancar-web"
}

foreach ($a in ($acciones | Select-Object -Unique)) {
    try {
        if ($a -eq "reconstruir-web") {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $WebLocal -Reconstruir 2>&1 | Out-Null
        } else {
            & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $WebLocal -Arrancar 2>&1 | Out-Null
        }
        Write-Vigia "Accion '$a' ejecutada (rc=$LASTEXITCODE)."
    } catch {
        Write-Vigia "Accion '$a' FALLO: $($_.Exception.Message)"
    }
}

if ($acciones.Count -gt 0) {
    $codApi = Test-Endpoint "http://127.0.0.1:$PuertoApi/" $TimeoutApiSeg
    $codWeb = Test-Endpoint "http://127.0.0.1:$PuertoWeb/" $TimeoutWebSeg
    Write-Vigia "Tras reparar: API=$codApi Web=$codWeb."
}

# ------------------------------------------------------- estado para la web
$estado = [ordered]@{
    schema        = "ultrarentable.vigia_local.v1"
    medido        = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    worktree      = $RepoRoot
    api           = [ordered]@{ puerto = $PuertoApi; http = $codApi; ok = ($codApi -eq 200) }
    web           = [ordered]@{ puerto = $PuertoWeb; http = $codWeb; ok = ($codWeb -eq 200) }
    build_integro = $buildIntegro
    acciones      = @($acciones | Select-Object -Unique)
    todo_en_pie   = (($codApi -eq 200) -and ($codWeb -eq 200))
}
$tmp = "$EstadoPath.tmp"
$estado | ConvertTo-Json -Depth 5 | Out-File -FilePath $tmp -Encoding utf8
Move-Item -Path $tmp -Destination $EstadoPath -Force

if (-not $estado.todo_en_pie) { exit 1 }
exit 0
