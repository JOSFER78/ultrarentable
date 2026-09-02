# GO_B16 — Localhost de ULTRARENTABLE en el PC: web en producción + API locales, arrancables/parables con un script, para ver `/estrategias` al momento

## Identidad
- ID: B16 · Ola: B · Rama/worktree: JOSFER78/agy-B16 · Timebox: 45 min
- Variables ya puestas: AGY_AGENT=B16, PYTHONPATH=<raíz de tu worktree>. Node: `node_modules/` y `apps/web/node_modules/` de tu worktree son junctions al worktree del orquestador; NO ejecutes `npm install`/`npm ci`. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
`scripts/orq/web_local.ps1` levanta en el PC una instancia LOCAL de ULTRARENTABLE con el código del worktree desde el que se ejecuta: la API FastAPI (`services/api/app/main.py`, uvicorn del venv) en `-PuertoApi` (por defecto **8100**) y la web Next.js en **build de producción** (`npm run build` + `npm run start -- -p <PuertoWeb>`, por defecto **3100**), ambas como procesos desacoplados (`Start-Process`, PIDs en `orchestration/site/local.pids.json`, salida en `orchestration/site/*.log`), con `-Estado` (HTTP 200 en `/`, `/estrategias`, `/prop-firms` y en `/api/v1/...` de salud de la API, más versión del motor leída de la API), `-Parar` (mata solo esos PIDs) y `-Reconstruir` (build + reinicio de la web); y la web local habla con la API local: `next.config` y `apps/web/lib/api.ts` leen `BACKEND_URL` (por defecto `http://127.0.0.1:8000`, sin cambiar el comportamiento actual) y el script arranca la web con `BACKEND_URL=http://127.0.0.1:<PuertoApi>`. Los puertos 3000 y 8000 del PC los ocupa hoy un túnel `sshd` hacia el VPS: NO se tocan.

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/orq/web_local.ps1 (nuevo) · orchestration/site/ (nuevo: pids, logs; añade `orchestration/site/*.log` y `local.pids.json` a `.gitignore` SOLO si `.gitignore` ya existe en la raíz; si no, déjalo como HALLAZGO)
- apps/web/next.config.* y apps/web/lib/api.ts (SOLO para leer `BACKEND_URL` con el mismo valor por defecto de hoy)
- orchestration/OPERACION_WEB_LOCAL.md (nuevo; 1 página: cómo arrancar, ver, reconstruir y parar)
- orchestration/results/agy/B16.md (nuevo) · orchestration/agy/DONE_B16.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- apps/web/next.config.* (rewrites `/api/:path*` → `${backendUrl}`; mira de dónde sale `backendUrl` hoy) y apps/web/lib/api.ts líneas 60-125 (`BASE_URL` servidor = `http://127.0.0.1:8000`).
- services/api/app/main.py y services/api/app/config.py (`STATE_DB_PATH`; la BD canónica está FUERA del repo: si no existe en el PC, la API debe arrancar igual y decirlo en `-Estado` como `NO DATA`).
- `powershell -NoProfile -Command "Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 3000,8000,3100,8100 }"` (pega la salida: 3000/8000 = túnel sshd).
- CLAUDE.md §"Servicios locales" (la web SIEMPRE en build de producción; nunca `next dev`).

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee las ENTRADAS; comprueba que `apps/web/.next/` no existe o ignórala.
2. `BACKEND_URL` en `next.config.*` y `lib/api.ts` (valor por defecto idéntico al actual). `npx tsc --noEmit -p apps/web` ⇒ rc=0.
3. `web_local.ps1` (PowerShell 5.1: sin `&&`, sin `??`): `-Arrancar` (por defecto): uvicorn `services.api.app.main:app --host 127.0.0.1 --port <PuertoApi>` con `-WorkingDirectory` = raíz del worktree y `PYTHONPATH` = raíz; espera hasta 30 s a que responda; luego `npm run build` (PESADO: ~2 min; pide admisión con `orca orchestration ask` si el ORQ no la ha dado ya en el spec) y `npm run start -- -p <PuertoWeb>` con `BACKEND_URL` en el entorno del proceso; guarda PIDs. `-Estado`: tabla puerto/proceso/HTTP por URL. `-Parar`: mata los PIDs del fichero y lo borra... NO: lo renombra a `local.pids.<fecha>.json` (nunca `rm`). `-Reconstruir`: build + reinicio solo de la web.
4. Ejecuta `-Arrancar` de verdad; pega `-Estado`; abre `curl -s http://127.0.0.1:3100/estrategias | head -c 600` y pégalo; `-Parar`; vuelve a `-Estado` (todo caído). Deja la instancia PARADA al cerrar (el ORQ la arranca desde devilray).
5. `orchestration/OPERACION_WEB_LOCAL.md`; informe con salidas crudas; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
cd apps/web && npx tsc --noEmit -p . ; echo "rc=$?"; cd ../..                                  # esperado: rc=0
grep -c "BACKEND_URL" apps/web/lib/api.ts apps/web/next.config.* | tail -2                       # esperado: >= 1 en cada uno
grep -cE "8000" apps/web/lib/api.ts                                                              # esperado: >= 1 (el valor por defecto sigue)
powershell -NoProfile -Command "[scriptblock]::Create((Get-Content -Raw scripts/orq/web_local.ps1)) | Out-Null; 'sintaxis ok'"   # esperado: sintaxis ok
grep -cE "Start-Process|uvicorn|npm run start" scripts/orq/web_local.ps1                          # esperado: >= 3
grep -c "3100" orchestration/OPERACION_WEB_LOCAL.md                                              # esperado: >= 1
git diff --name-only   # ⊆ TERRITORIO; esperado: apps/web/lib/api.ts y apps/web/next.config.* (y .gitignore si existía)
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? SÍ, `npm run build` (~2 min, 1 vez): ADMITIDO por el ORQ para esta tarea (semáforo: build SQX de B06 + campaña E2 de B03 son los dos pesados; el build de web se tolera como tercero por ser corto). Ejecútalo con `Start-Process -PriorityClass BelowNormal` o `cmd /c start /low /b /wait`.
- NO tocar los puertos 3000/8000 (túnel al VPS) ni ningún proceso `sshd`.
- `.env.local`/Firebase NO se tocan (issue #22 punto 3).

## PROHIBIDO (lista negra, sin excepciones)
git de escritura · rm (los ficheros de PIDs se renombran) · `npm install` · `next dev` · matar procesos que no arrancó el script · escribir fuera del TERRITORIO · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B16.md. 3. orchestration/agy/DONE_B16.md.
4. Cierre: orca orchestration send --type worker_done --subject "B16 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json
