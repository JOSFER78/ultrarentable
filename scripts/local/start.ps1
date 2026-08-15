$ErrorActionPreference = "Stop"
$root = Resolve-Path "$PSScriptRoot\..\.."
Set-Location $root

if (-not (Test-Path ".venv\Scripts\python.exe")) {
  throw "Falta .venv. Ejecuta scripts/local/install.ps1 primero."
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; .\.venv\Scripts\python.exe -m uvicorn services.api.app.main:app --host 127.0.0.1 --port 8000 --reload"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root'; npm run web:dev"
Write-Host "API: http://127.0.0.1:8000"
Write-Host "Web: http://127.0.0.1:3000"
