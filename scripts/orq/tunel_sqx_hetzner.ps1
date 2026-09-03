# ==============================================================================
# scripts/orq/tunel_sqx_hetzner.ps1
# Tunel SSH persistente PC -> Hetzner, dos puertos:
#   127.0.0.1:5051 -> StrategyQuant X headless en modo comandos (sqcli)
#   127.0.0.1:5052 -> estado de la rejilla M1 (estado.json y CSVs del runner, solo lectura)
# Ninguno de los dos tiene autenticacion, asi que NO se abren en el servidor: ufw permite
# solo 22/80/443 y ademas niega 5050:5052 explicitamente. Se llega SOLO por este tunel.
# Uso (bucle que reconecta solo):
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/tunel_sqx_hetzner.ps1
# Comprobar:  curl "http://127.0.0.1:5051/call?cmd=-symbol%20action=list"
#             curl "http://127.0.0.1:5052/estado.json"
# Log:        orchestration/site/tunel_sqx.log
# ==============================================================================
param(
    [int]$PuertoSqx = 5051,
    [int]$PuertoEstado = 5052,
    [string]$Servidor = "sqx-hetzner"
)
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$SiteDir = Join-Path $RepoRoot "orchestration\site"
if (-not (Test-Path $SiteDir)) { New-Item -ItemType Directory -Force -Path $SiteDir | Out-Null }
$Log = Join-Path $SiteDir "tunel_sqx.log"
while ($true) {
    "$(Get-Date -Format u) conectando 127.0.0.1:$PuertoSqx y :$PuertoEstado -> $Servidor" | Out-File -Append -Encoding utf8 $Log
    & ssh -N -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=15 -L "127.0.0.1:${PuertoSqx}:127.0.0.1:${PuertoSqx}" -L "127.0.0.1:${PuertoEstado}:127.0.0.1:${PuertoEstado}" $Servidor
    "$(Get-Date -Format u) tunel caido (rc=$LASTEXITCODE); reintento en 10 s" | Out-File -Append -Encoding utf8 $Log
    Start-Sleep -Seconds 10
}
