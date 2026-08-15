$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path "$PSScriptRoot\..\..")

$pythonArgs = $null
if (Get-Command py -ErrorAction SilentlyContinue) {
  try { & py -3.12 -c "import sys"; $pythonArgs = @("-3.12") } catch {}
  if (-not $pythonArgs) {
    try { & py -3.11 -c "import sys"; $pythonArgs = @("-3.11") } catch {}
  }
}
if ($pythonArgs) {
  & py @pythonArgs -m venv .venv
} else {
  & python -m venv .venv
}
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\pip.exe install -e ".[dev]"
npm install
npm run web:build
Write-Host "Instalación local completada y frontend compilado. Ejecuta scripts/local/start.ps1"
