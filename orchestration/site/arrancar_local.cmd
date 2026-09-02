@echo off
cd /d "C:\Users\yo\orca\workspaces\ultrarentable\devilray"
set PYTHONPATH=C:\Users\yo\orca\workspaces\ultrarentable\devilray
powershell -NoProfile -ExecutionPolicy Bypass -File "C:\Users\yo\orca\workspaces\ultrarentable\devilray\scripts\orq\web_local.ps1" -Arrancar > "C:\Users\yo\orca\workspaces\ultrarentable\devilray\orchestration\site\arrancar_local.out" 2>&1
rem La tarea programada se mantiene viva: si este proceso termina, el Programador cierra el job y mata la web y la API
:espera
timeout /t 300 /nobreak > nul
goto espera
