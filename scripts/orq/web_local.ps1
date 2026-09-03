# ==============================================================================
# scripts/orq/web_local.ps1
# ULTRARENTABLE — Instancia LOCAL desacoplada (FastAPI + Next.js Produccion)
# ZERO-MOCK · REAL-ONLY · SIN AFECTAR PUERTOS 3000/8000 (TUNEL SSHD VPS)
# ==============================================================================

[CmdletBinding(DefaultParameterSetName = "Arrancar")]
param(
    [Parameter(ParameterSetName = "Arrancar")]
    [switch]$Arrancar,

    [Parameter(ParameterSetName = "Estado")]
    [switch]$Estado,

    [Parameter(ParameterSetName = "Parar")]
    [switch]$Parar,

    [Parameter(ParameterSetName = "Reconstruir")]
    [switch]$Reconstruir,

    [int]$PuertoApi = 8100,
    [int]$PuertoWeb = 3100,
    [string]$HostName = "127.0.0.1"
)

$ErrorActionPreference = "Continue"

# 1. Resolucion de rutas del worktree
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$SiteDir = Join-Path $RepoRoot "orchestration\site"
$PidFile = Join-Path $SiteDir "local.pids.json"
$WebDir = Join-Path $RepoRoot "apps\web"

if (-not (Test-Path $SiteDir)) {
    New-Item -ItemType Directory -Force -Path $SiteDir | Out-Null
}

# 2. Resolucion de Python del proyecto
$PyExe = "C:\Users\yo\Pictures\Descargaspc\pro\UltrarentablePC\ultrarentable\.venv\Scripts\python.exe"
if (-not (Test-Path $PyExe)) {
    $LocalVenvPy = Join-Path $RepoRoot ".venv\Scripts\python.exe"
    if (Test-Path $LocalVenvPy) {
        $PyExe = $LocalVenvPy
    } else {
        $PyExe = "python.exe"
    }
}

# 3. Funcion para lanzar procesos desacoplados persistentes
function Start-DaemonProcess {
    param(
        [string]$CommandLine,
        [string]$WorkingDirectory
    )
    try {
        $res = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
            CommandLine = $CommandLine
            CurrentDirectory = $WorkingDirectory
        }
        if ($res.ReturnValue -eq 0 -and $res.ProcessId) {
            return [int]$res.ProcessId
        }
    } catch {
        # Fallback a Start-Process
    }
    $p = Start-Process -FilePath "cmd.exe" -ArgumentList "/c $CommandLine" -WorkingDirectory $WorkingDirectory -WindowStyle Hidden -PassThru
    return [int]$p.Id
}

# 4. Obtener PID que escucha en un puerto
function Get-PortOwnerPid {
    param([int]$Port)
    try {
        $conns = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if ($conns) {
            $pids = @($conns | Select-Object -ExpandProperty OwningProcess | Where-Object { $_ -gt 0 } | Select-Object -Unique)
            if ($pids.Count -gt 0) {
                return [int]$pids[0]
            }
        }
    } catch {}
    return $null
}

# 5. Funcion auxiliar para sondeo HTTP
function Probe-Endpoint {
    param(
        [string]$Url,
        [int]$TimeoutSec = 3
    )
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $resp = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec $TimeoutSec -ErrorAction Stop
        $sw.Stop()
        return [PSCustomObject]@{
            Url = $Url
            Status = $resp.StatusCode
            LatencyMs = [int]$sw.ElapsedMilliseconds
            Success = ($resp.StatusCode -eq 200)
            Content = $resp.Content
            Error = $null
        }
    } catch {
        $sw.Stop()
        $statusCode = "OFFLINE"
        if ($_.Exception -and $_.Exception.Response) {
            try {
                $statusCode = [int]$_.Exception.Response.StatusCode
            } catch {
                $statusCode = "ERROR"
            }
        }
        return [PSCustomObject]@{
            Url = $Url
            Status = $statusCode
            LatencyMs = [int]$sw.ElapsedMilliseconds
            Success = $false
            Content = $null
            Error = $_.Exception.Message
        }
    }
}

# 6. Funcion para detener arbol de procesos
function Stop-ProcessTree {
    param([int]$ProcessId)
    if ($ProcessId -le 0) { return }
    try {
        $p = Get-Process -Id $ProcessId -ErrorAction SilentlyContinue
        if ($p) {
            Start-Process -FilePath "cmd.exe" -ArgumentList "/c taskkill /PID $ProcessId /T /F >nul 2>&1" -Wait -WindowStyle Hidden -ErrorAction SilentlyContinue
            Stop-Process -Id $ProcessId -Force -ErrorAction SilentlyContinue
        }
    } catch {
        # Proceso ya no existe
    }
}

# Accion por defecto si no se especifico switch
if (-not $Estado -and -not $Parar -and -not $Reconstruir) {
    $Arrancar = $true
}

# ------------------------------------------------------------------------------
# PARAR
# ------------------------------------------------------------------------------
if ($Parar) {
    Write-Host "=== ULTRARENTABLE LOCAL: DETENIENDO SERVICIOS ===" -ForegroundColor Yellow
    $puertoApiStop = $PuertoApi
    $puertoWebStop = $PuertoWeb

    if (Test-Path $PidFile) {
        try {
            $pidContent = Get-Content -Raw -Path $PidFile | ConvertFrom-Json
            $apiPid = $pidContent.api_pid
            $webPid = $pidContent.web_pid
            if ($pidContent.puerto_api) { $puertoApiStop = [int]$pidContent.puerto_api }
            if ($pidContent.puerto_web) { $puertoWebStop = [int]$pidContent.puerto_web }

            if ($apiPid) {
                Write-Host "Deteniendo API FastAPI (PID $apiPid)..."
                Stop-ProcessTree -ProcessId $apiPid
            }
            if ($webPid) {
                Write-Host "Deteniendo Web Next.js (PID $webPid)..."
                Stop-ProcessTree -ProcessId $webPid
            }

            # NUNCA rm: renombramos a local.pids.<timestamp>.json
            $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
            $archivePidFile = Join-Path $SiteDir "local.pids.$timestamp.json"
            Move-Item -Path $PidFile -Destination $archivePidFile -Force
            Write-Host "Fichero PID archivado en: $archivePidFile (regla: nunca rm)" -ForegroundColor DarkGray
        } catch {
            Write-Warning ("Error leyendo " + $PidFile + ": " + $_)
        }
    } else {
        Write-Host "No hay fichero local.pids.json activo." -ForegroundColor Gray
    }

    # Asegurar liberacion de puertos locales 8100 y 3100
    $lingeringApi = Get-PortOwnerPid -Port $puertoApiStop
    if ($lingeringApi) {
        Write-Host "Cerrando proceso remanente en puerto $puertoApiStop (PID $lingeringApi)..."
        Stop-ProcessTree -ProcessId $lingeringApi
    }
    $lingeringWeb = Get-PortOwnerPid -Port $puertoWebStop
    if ($lingeringWeb) {
        Write-Host "Cerrando proceso remanente en puerto $puertoWebStop (PID $lingeringWeb)..."
        Stop-ProcessTree -ProcessId $lingeringWeb
    }

    Write-Host "Servicios locales detenidos." -ForegroundColor Green
    exit 0
}

# ------------------------------------------------------------------------------
# RECONSTRUIR
# ------------------------------------------------------------------------------
if ($Reconstruir) {
    Write-Host "=== ULTRARENTABLE LOCAL: RECONSTRUYENDO WEB PRODUCCION ===" -ForegroundColor Cyan
    $apiPortCurrent = $PuertoApi
    if (Test-Path $PidFile) {
        try {
            $pidContent = Get-Content -Raw -Path $PidFile | ConvertFrom-Json
            if ($pidContent.puerto_api) { $apiPortCurrent = [int]$pidContent.puerto_api }
            $webPid = $pidContent.web_pid
            if ($webPid) {
                Write-Host "Deteniendo proceso Web actual (PID $webPid)..."
                Stop-ProcessTree -ProcessId $webPid
            }
        } catch {}
    }
    $lingeringWeb = Get-PortOwnerPid -Port $PuertoWeb
    if ($lingeringWeb) {
        Stop-ProcessTree -ProcessId $lingeringWeb
    }

    $env:BACKEND_URL = "http://${HostName}:${apiPortCurrent}"
    $env:ULTRARENTABLE_API_URL = "http://${HostName}:${apiPortCurrent}"

    $buildLog = Join-Path $SiteDir "build.log"
    $buildErrLog = Join-Path $SiteDir "build_err.log"
    Write-Host "Ejecutando build de produccion de Next.js (apps/web)..."
    $buildProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run build" -WorkingDirectory $WebDir -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrLog -PassThru -Wait
    if ($buildProc.ExitCode -ne 0) {
        Write-Error "Fallo npm run build (ExitCode $($buildProc.ExitCode)). Consulta $buildLog"
        exit $buildProc.ExitCode
    }
    Write-Host "Build de produccion completado exitosamente." -ForegroundColor Green

    # Reiniciar proceso Web con npm run start
    $webOutLog = Join-Path $SiteDir "web.log"
    $webErrLog = Join-Path $SiteDir "web_err.log"
    Write-Host "Iniciando servidor Next.js produccion en puerto $PuertoWeb..."
    $webCmd = "cmd.exe /c set BACKEND_URL=http://${HostName}:${apiPortCurrent}& set ULTRARENTABLE_API_URL=http://${HostName}:${apiPortCurrent}& npm run start -- -p $PuertoWeb > `"$webOutLog`" 2> `"$webErrLog`""
    $webSpawnPid = Start-DaemonProcess -CommandLine $webCmd -WorkingDirectory $WebDir

    # Esperar a que la Web responda
    Write-Host "Esperando a que la Web responda en http://${HostName}:${PuertoWeb}/..." -NoNewline
    $webReady = $false
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    while ($stopwatch.ElapsedMilliseconds -lt 45000) {
        Start-Sleep -Milliseconds 600
        Write-Host "." -NoNewline
        try {
            $resp = Invoke-WebRequest -Uri "http://${HostName}:${PuertoWeb}/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($resp.StatusCode -eq 200) {
                $webReady = $true
                break
            }
        } catch {}
    }
    Write-Host ""
    if (-not $webReady) {
        Write-Error "Tiempo de espera agotado esperando a la Web en puerto $PuertoWeb."
        exit 1
    }

    $actualWebPid = Get-PortOwnerPid -Port $PuertoWeb
    if (-not $actualWebPid) { $actualWebPid = $webSpawnPid }
    Write-Host "Web Next.js ONLINE tras reconstruccion (PID $actualWebPid)." -ForegroundColor Green

    # Actualizar local.pids.json
    if (Test-Path $PidFile) {
        try {
            $pidContent = Get-Content -Raw -Path $PidFile | ConvertFrom-Json
            $pidContent.web_pid = $actualWebPid
            $pidContent.rebuilt_at = (Get-Date).ToUniversalTime().ToString("o")
            $pidContent | ConvertTo-Json -Depth 5 | Set-Content -Path $PidFile -Encoding UTF8
        } catch {}
    }

    $Estado = $true
}

# ------------------------------------------------------------------------------
# ARRANCAR
# ------------------------------------------------------------------------------
if ($Arrancar) {
    Write-Host "=== ULTRARENTABLE LOCAL: ARRANCANDO INSTANCIA ===" -ForegroundColor Cyan
    Write-Host "Worktree: $RepoRoot"
    Write-Host "Puerto API: $PuertoApi | Puerto Web: $PuertoWeb"

    # 1. Iniciar API FastAPI con uvicorn en segundo plano si no esta activa
    $activeApiPid = Get-PortOwnerPid -Port $PuertoApi
    if ($activeApiPid) {
        Write-Host "API FastAPI ya activa en puerto $PuertoApi (PID $activeApiPid)." -ForegroundColor Green
        $apiPid = $activeApiPid
    } else {
        $apiOutLog = Join-Path $SiteDir "api.log"
        $apiErrLog = Join-Path $SiteDir "api_err.log"
        Write-Host "Iniciando API FastAPI con uvicorn en http://${HostName}:${PuertoApi}..."
        $apiCmd = "cmd.exe /c set PYTHONPATH=$RepoRoot& set ULTRARENTABLE_AUTONOMOUS_RUNTIME=false& set SQX_API_URL=http://127.0.0.1:5051& `"$PyExe`" -u -m uvicorn services.api.app.main:app --host $HostName --port $PuertoApi > `"$apiOutLog`" 2> `"$apiErrLog`""
        $apiSpawnPid = Start-DaemonProcess -CommandLine $apiCmd -WorkingDirectory $RepoRoot

        # Esperar hasta 60 s a que la API responda
        Write-Host "Esperando a que la API responda en http://${HostName}:${PuertoApi}/..." -NoNewline
        $apiReady = $false
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        while ($stopwatch.ElapsedMilliseconds -lt 60000) {
            Start-Sleep -Milliseconds 600
            Write-Host "." -NoNewline
            try {
                $resp = Invoke-WebRequest -Uri "http://${HostName}:${PuertoApi}/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($resp.StatusCode -eq 200) {
                    $apiReady = $true
                    break
                }
            } catch {}
        }
        Write-Host ""
        if (-not $apiReady) {
            Write-Error "Tiempo de espera agotado (60s) esperando a la API en puerto $PuertoApi."
            exit 1
        }
        $actualApiPid = Get-PortOwnerPid -Port $PuertoApi
        if (-not $actualApiPid) { $actualApiPid = $apiSpawnPid }
        $apiPid = $actualApiPid
        Write-Host "API FastAPI ONLINE (PID $apiPid)." -ForegroundColor Green
    }

    # 2. Verificar build de produccion de Next.js
    $nextBuildDir = Join-Path $WebDir ".next"
    $buildLog = Join-Path $SiteDir "build.log"
    $buildErrLog = Join-Path $SiteDir "build_err.log"
    if (-not (Test-Path $nextBuildDir)) {
        Write-Host "No existe build de produccion previo. Ejecutando npm run build..."
        $buildProc = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run build" -WorkingDirectory $WebDir -RedirectStandardOutput $buildLog -RedirectStandardError $buildErrLog -PassThru -Wait
        if ($buildProc.ExitCode -ne 0) {
            Write-Error "Fallo npm run build (ExitCode $($buildProc.ExitCode)). Revisa $buildLog"
            exit $buildProc.ExitCode
        }
        Write-Host "Build de produccion completado exitosamente." -ForegroundColor Green
    } else {
        Write-Host "Build de produccion existente detectado en $nextBuildDir." -ForegroundColor Gray
    }

    # 3. Iniciar servidor Web Next.js con npm run start si no esta activo
    $activeWebPid = Get-PortOwnerPid -Port $PuertoWeb
    if ($activeWebPid) {
        Write-Host "Web Next.js ya activa en puerto $PuertoWeb (PID $activeWebPid)." -ForegroundColor Green
        $webPid = $activeWebPid
    } else {
        $webOutLog = Join-Path $SiteDir "web.log"
        $webErrLog = Join-Path $SiteDir "web_err.log"
        Write-Host "Iniciando Web Next.js produccion en http://${HostName}:${PuertoWeb}..."
        $webCmd = "cmd.exe /c set BACKEND_URL=http://${HostName}:${PuertoApi}& set ULTRARENTABLE_API_URL=http://${HostName}:${PuertoApi}& npm run start -- -p $PuertoWeb > `"$webOutLog`" 2> `"$webErrLog`""
        $webSpawnPid = Start-DaemonProcess -CommandLine $webCmd -WorkingDirectory $WebDir

        # Esperar hasta 45 s a que la Web responda
        Write-Host "Esperando a que la Web responda en http://${HostName}:${PuertoWeb}/..." -NoNewline
        $webReady = $false
        $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
        while ($stopwatch.ElapsedMilliseconds -lt 45000) {
            Start-Sleep -Milliseconds 600
            Write-Host "." -NoNewline
            try {
                $resp = Invoke-WebRequest -Uri "http://${HostName}:${PuertoWeb}/" -UseBasicParsing -TimeoutSec 2 -ErrorAction SilentlyContinue
                if ($resp.StatusCode -eq 200) {
                    $webReady = $true
                    break
                }
            } catch {}
        }
        Write-Host ""
        if (-not $webReady) {
            Write-Error "Tiempo de espera agotado esperando a la Web en puerto $PuertoWeb."
            exit 1
        }
        $actualWebPid = Get-PortOwnerPid -Port $PuertoWeb
        if (-not $actualWebPid) { $actualWebPid = $webSpawnPid }
        $webPid = $actualWebPid
        Write-Host "Web Next.js ONLINE (PID $webPid)." -ForegroundColor Green
    }

    # 4. Guardar PIDs en orchestration/site/local.pids.json
    $pidsData = [ordered]@{
        api_pid = $apiPid
        web_pid = $webPid
        puerto_api = $PuertoApi
        puerto_web = $PuertoWeb
        host = $HostName
        backend_url = "http://${HostName}:${PuertoApi}"
        started_at = (Get-Date).ToUniversalTime().ToString("o")
        worktree = $RepoRoot
    }
    $pidsJson = $pidsData | ConvertTo-Json -Depth 5
    Set-Content -Path $PidFile -Value $pidsJson -Encoding UTF8
    Write-Host "PIDs guardados en: $PidFile" -ForegroundColor DarkGray

    $Estado = $true
}

# ------------------------------------------------------------------------------
# ESTADO
# ------------------------------------------------------------------------------
if ($Estado) {
    Write-Host "`n=== ULTRARENTABLE LOCAL: ESTADO DE SERVICIOS ===" -ForegroundColor Cyan

    $apiPidVal = $null
    $webPidVal = $null
    $puertoApiVal = $PuertoApi
    $puertoWebVal = $PuertoWeb

    if (Test-Path $PidFile) {
        try {
            $pidInfo = Get-Content -Raw -Path $PidFile | ConvertFrom-Json
            $apiPidVal = $pidInfo.api_pid
            $webPidVal = $pidInfo.web_pid
            if ($pidInfo.puerto_api) { $puertoApiVal = [int]$pidInfo.puerto_api }
            if ($pidInfo.puerto_web) { $puertoWebVal = [int]$pidInfo.puerto_web }
        } catch {}
    }

    # Comprobar PID activo en sistema o por puerto
    $activeApiOwner = Get-PortOwnerPid -Port $puertoApiVal
    if ($activeApiOwner) { $apiPidVal = $activeApiOwner }

    $activeWebOwner = Get-PortOwnerPid -Port $puertoWebVal
    if ($activeWebOwner) { $webPidVal = $activeWebOwner }

    $apiProcStatus = "NO REGISTRADO"
    if ($apiPidVal) {
        $ap = Get-Process -Id $apiPidVal -ErrorAction SilentlyContinue
        if ($ap) {
            $apiProcStatus = "ACTIVO (PID $apiPidVal - $($ap.ProcessName))"
        } else {
            $apiProcStatus = "DETENIDO (PID $apiPidVal)"
        }
    }

    $webProcStatus = "NO REGISTRADO"
    if ($webPidVal) {
        $wp = Get-Process -Id $webPidVal -ErrorAction SilentlyContinue
        if ($wp) {
            $webProcStatus = "ACTIVO (PID $webPidVal - $($wp.ProcessName))"
        } else {
            $webProcStatus = "DETENIDO (PID $webPidVal)"
        }
    }

    Write-Host "Procesos:"
    Write-Host "  - API FastAPI (Puerto $puertoApiVal): $apiProcStatus"
    Write-Host "  - Web Next.js (Puerto $puertoWebVal): $webProcStatus"

    # Sondeo de endpoints
    $endpoints = @(
        @{ Servicio = "API Root";           Url = "http://${HostName}:${puertoApiVal}/" },
        @{ Servicio = "API Version";        Url = "http://${HostName}:${puertoApiVal}/api/v1/version" },
        @{ Servicio = "API System Health";  Url = "http://${HostName}:${puertoApiVal}/api/v1/system/health" },
        @{ Servicio = "Web Home";           Url = "http://${HostName}:${puertoWebVal}/" },
        @{ Servicio = "Web Estrategias";    Url = "http://${HostName}:${puertoWebVal}/estrategias" },
        @{ Servicio = "Web Prop-Firms";     Url = "http://${HostName}:${puertoWebVal}/prop-firms" }
    )

    $results = @()
    $engineVersion = "NO DATA"
    $dbStatus = "NO DATA"

    foreach ($ep in $endpoints) {
        $probe = Probe-Endpoint -Url $ep.Url -TimeoutSec 3
        $results += [PSCustomObject]@{
            Servicio   = $ep.Servicio
            URL        = $ep.Url
            HTTP_Code  = $probe.Status
            LatenciaMs = "$($probe.LatencyMs) ms"
            Resultado  = if ($probe.Success) { "OK (200)" } else { "FALLO ($($probe.Status))" }
        }

        if ($ep.Servicio -eq "API Version" -and $probe.Success -and $probe.Content) {
            try {
                $vJson = $probe.Content | ConvertFrom-Json
                if ($vJson.canonical_engine_version) {
                    $engineVersion = $vJson.canonical_engine_version
                } elseif ($vJson.engine_version) {
                    $engineVersion = $vJson.engine_version
                }
            } catch {}
        }
        if ($ep.Servicio -eq "API System Health" -and $probe.Success -and $probe.Content) {
            try {
                $hJson = $probe.Content | ConvertFrom-Json
                if ($hJson.database -and $hJson.database.db_path) {
                    $dbPath = $hJson.database.db_path
                    if (Test-Path $dbPath) {
                        $dbStatus = "CONECTADA ($dbPath)"
                    } else {
                        $dbStatus = "NO DATA (BD no encontrada en disco local)"
                    }
                }
            } catch {}
        }
    }

    Write-Host "`nSondeo de Endpoints:"
    $results | Format-Table -AutoSize | Out-String | Write-Host

    Write-Host "Metadatos del Motor y Sistema:"
    Write-Host "  - Version del Motor (API): $engineVersion" -ForegroundColor Yellow
    Write-Host "  - Estado Base de Datos:    $dbStatus" -ForegroundColor Gray
    Write-Host "  - Backend URL Web:         http://${HostName}:${puertoApiVal}"
    Write-Host ""
}
