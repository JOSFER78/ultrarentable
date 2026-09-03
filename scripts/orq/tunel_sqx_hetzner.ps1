# ==============================================================================
# scripts/orq/tunel_sqx_hetzner.ps1
# Tunel SSH persistente  PC 127.0.0.1:5051  ->  Hetzner 127.0.0.1:5051
# (StrategyQuant X headless en modo comandos). SQX NO tiene autenticacion: el puerto
# nunca se abre en el servidor (ufw: solo 22/80/443); a el se llega SOLO por este tunel.
# Uso (bucle que reconecta solo):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/tunel_sqx_hetzner.ps1
# Comprobar:  curl "http://127.0.0.1:5051/call?cmd=-symbol%20action=list"
# Log:        orchestration/site/tunel_sqx.log
# ==============================================================================
param(
    [int]$PuertoLocal = 5051,
    [int]$PuertoRemoto = 5051,
    [string]$Servidor = "sqx-hetzner"
)
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$SiteDir = Join-Path $RepoRoot "orchestration\site"
if (-not (Test-Path $SiteDir)) { New-Item -ItemType Directory -Force -Path $SiteDir | Out-Null }
$Log = Join-Path $SiteDir "tunel_sqx.log"
while ($true) {
    "$(Get-Date -Format u) conectando 127.0.0.1:$PuertoLocal -> $Servidor 127.0.0.1:$PuertoRemoto" | Out-File -Append -Encoding utf8 $Log
    & ssh -N -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=15 -L "127.0.0.1:${PuertoLocal}:127.0.0.1:${PuertoRemoto}" $Servidor
    "$(Get-Date -Format u) tunel caido (rc=$LASTEXITCODE); reintento en 10 s" | Out-File -Append -Encoding utf8 $Log
    Start-Sleep -Seconds 10
}
