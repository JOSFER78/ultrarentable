# ==============================================================================
# scripts/orq/tunel_ia_oracle.ps1
# Tunel SSH persistente  PC 127.0.0.1:8742  ->  Oracle 127.0.0.1:8742
#
# 8742 es el puente de IA de Antigravity que ya vive en el servidor Oracle: habla el
# protocolo de OpenAI (/v1/chat/completions) y sirve el modelo gemini-3.7-flash-high.
# Comprobado el 03-09: responde a una pregunta real en menos de 45 s.
#
# Escucha SOLO en 127.0.0.1 dentro del servidor, asi que no se llega a el desde fuera:
# este tunel es la unica via desde el PC. Cuando la aplicacion corra en el servidor
# (que es donde debe vivir), este tunel deja de hacer falta: alli el puente es local.
#
# Uso:  powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/tunel_ia_oracle.ps1
# Log:  orchestration/site/tunel_ia.log
# ==============================================================================
param(
    [int]$Puerto = 8742,
    [string]$Servidor = "oracle-vps"
)
$RepoRoot = (Resolve-Path "$PSScriptRoot\..\..").Path
$SiteDir = Join-Path $RepoRoot "orchestration\site"
if (-not (Test-Path $SiteDir)) { New-Item -ItemType Directory -Force -Path $SiteDir | Out-Null }
$Log = Join-Path $SiteDir "tunel_ia.log"
while ($true) {
    "$(Get-Date -Format u) conectando 127.0.0.1:$Puerto -> $Servidor" | Out-File -Append -Encoding utf8 $Log
    & ssh -N -o BatchMode=yes -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=3 -o ConnectTimeout=15 -L "127.0.0.1:${Puerto}:127.0.0.1:${Puerto}" $Servidor
    "$(Get-Date -Format u) tunel de IA caido (rc=$LASTEXITCODE); reintento en 10 s" | Out-File -Append -Encoding utf8 $Log
    Start-Sleep -Seconds 10
}
