<#
.SYNOPSIS
  mcp_vacio.ps1 - Vacia los ficheros de configuracion MCP de Antigravity (config y antigravity-ide)
  dejandolos en {"mcpServers": {}} y guardando un backup fechado al lado si tenian servidores.

.PARAMETER ConfigDir
  Directorio base de configuracion de Gemini. Por defecto: ~/.gemini ($HOME/.gemini).

.EXAMPLE
  .\scripts\orq\mcp_vacio.ps1
  .\scripts\orq\mcp_vacio.ps1 -ConfigDir "C:\temp\test_gemini"
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigDir = (Join-Path $HOME ".gemini")
)

$ErrorActionPreference = "Stop"

$targets = @(
    (Join-Path $ConfigDir "config\mcp_config.json"),
    (Join-Path $ConfigDir "antigravity-ide\mcp_config.json")
)

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$totalPrevio = 0
$detalles = @()

foreach ($target in $targets) {
    $parentDir = Split-Path -Parent $target
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force -ErrorAction SilentlyContinue | Out-Null
    }

    $numServidores = 0
    if (Test-Path $target) {
        try {
            $raw = [System.IO.File]::ReadAllText($target, [System.Text.Encoding]::UTF8)
            if (-not [string]::IsNullOrWhiteSpace($raw)) {
                $jsonObj = $raw | ConvertFrom-Json -ErrorAction SilentlyContinue
                if ($jsonObj -and $jsonObj.mcpServers) {
                    $props = $jsonObj.mcpServers.PSObject.Properties
                    if ($props) {
                        $numServidores = ($props | Measure-Object).Count
                    }
                }
            }
        } catch {
            Write-Host "Aviso: no se pudo parsear $target como JSON"
        }

        if ($numServidores -gt 0) {
            $stamp = (Get-Date).ToString("yyyyMMdd_HHmmss")
            $backupPath = Join-Path $parentDir "mcp_config.backup_$stamp.json"
            Copy-Item -Path $target -Destination $backupPath -Force -ErrorAction Stop
            Write-Host "Backup creado: $backupPath ($numServidores servidores)"
        }
    }

    $totalPrevio += $numServidores
    [System.IO.File]::WriteAllText($target, '{"mcpServers": {}}', $utf8NoBom)
    $detalles += "$target : $numServidores servidores previos"
}

foreach ($d in $detalles) {
    Write-Host "  -> $d"
}
Write-Host "Resultado: $totalPrevio servidores encontrados antes -> 0 servidores tras vaciar"
