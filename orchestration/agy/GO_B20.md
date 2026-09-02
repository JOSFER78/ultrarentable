# GO_B20 — `scripts/orq/agy_cerrar.sh <ID> [dispatch]`: cierre completo y seguro de un agente (release, stop, censo, junctions, worktree, issue)

## Identidad
- ID: B20 · Ola: S (sistema) · Rama/worktree: JOSFER78/agy-B20 · Timebox: 30 min
- Variables ya puestas: AGY_AGENT=B20, PYTHONPATH=<raíz de tu worktree>. Python: `PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"`.

## OBJETIVO (una frase verificable)
`scripts/orq/agy_cerrar.sh <ID> [<dispatchId>] [--sin-worktree] [--issue N --etiqueta integrado|repite]` ejecuta, en este orden y parando en el primer fallo con mensaje claro: (1) `orca orchestration worker-release --dispatch <ctx>` (con `timeout 25`; si no se pasa ctx, lo busca en `worker-list` por `agentTerminalHandle` cuyo terminal esté en el worktree `agy-<ID>`); (2) `orca terminal stop --worktree path:<ruta>`; (3) censo: ningún `agy.exe` cuyo log `cli-*.log` apunte a ese worktree sigue vivo (si sigue, `scripts/orq/agy_matar.ps1 -ProcesoId <pid>`; nunca `-Forzar`), y ningún proceso MCP huérfano; (4) junctions: cada reparse point dentro del worktree (raíz, `apps/web`, `data`) se elimina con `[IO.DirectoryInfo]::Delete()` (nunca recursivo) y se comprueba que el destino sigue existiendo con el mismo número de entradas; (5) `git -C <checkout principal> worktree remove --force <ruta>` + `worktree prune` (omitido con `--sin-worktree`); (6) si `--issue N`, `gh issue edit N --add-label <etiqueta> --remove-label en-vuelo` y `gh issue close N` solo con `integrado`; (7) resumen final en una línea y registro JSON en `orchestration/state/agentes.jsonl` (`evento: cierre`).

## TERRITORIO (únicas rutas donde puede ESCRIBIR; fuera, solo lectura)
- scripts/orq/agy_cerrar.sh (nuevo) · tests/test_orq_agentes.py (añadir casos; no romper los existentes)
- orchestration/OPERACION_AGENTES.md (sección "Cerrar": sustituir la lista manual por el script)
- orchestration/results/agy/B20.md (nuevo) · orchestration/agy/DONE_B20.md (nuevo)

## ENTRADAS (leer antes de tocar nada; con ruta exacta)
- scripts/orq/agy_matar.ps1, agy_censo.ps1, agy_limpiar.ps1 (B15) y orchestration/OPERACION_AGENTES.md.
- Lo que el ORQ hizo hoy a mano y que hay que productizar (verificado): `orca terminal stop --worktree path:<ruta>` mata el árbol del terminal (agy incluido); `worker-release` no mata nada y los workers muertos quedan `terminalState: retained` en `worker-list`; las junctions se borran con `(New-Object IO.DirectoryInfo '<ruta>').Delete()` y se verifica el destino (`data/normalized` del checkout principal: 531 entradas; `node_modules` de devilray: 75).
- `orca orchestration worker-release --help`, `orca terminal stop --help`, `git worktree remove --help`, `gh issue edit --help`.
- Checkout principal: `C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable`; worktrees en `C:/Users/yo/orca/workspaces/ultrarentable/agy-<ID>`.

## PASOS (numerados, cortos, en orden)
1. `git status --porcelain` vacío; lee las ENTRADAS.
2. Escribe `agy_cerrar.sh` (Git Bash; PowerShell solo para reparse points y procesos; sin `&&` en PowerShell 5.1). Cada paso imprime `[cerrar <ID>] paso N: OK|FALLO <motivo>`.
3. Tests reales: (a) `bash -n`; (b) función de junctions sobre un árbol temporal que el test crea con `cmd /c mklink /J` apuntando a otro directorio temporal con 3 ficheros: tras el cierre, la junction no existe y el destino conserva los 3 ficheros; (c) función de "buscar dispatch por worktree" sobre un JSON de `worker-list` guardado por ti en el test desde la salida REAL de `orca orchestration worker-list --json` (fichero fixture real, no inventado); (d) el registro JSON de cierre es válido. No cierres agentes reales desde el test.
4. OPERACION_AGENTES.md: sección "Cerrar" con el comando único. Informe; DONE; cierre.

## ACEPTACIÓN (comandos exactos + salida esperada; el orquestador los re-ejecuta desde la raíz del worktree)
```bash
PY="C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
bash -n scripts/orq/agy_cerrar.sh; echo "rc=$?"                                                       # esperado: rc=0
"$PY" -m pytest tests/test_orq_agentes.py -q -p no:cacheprovider                                      # esperado: >= 8 passed (los de B15 + los tuyos)
grep -c -E "worker-release|terminal stop|DirectoryInfo|worktree remove|gh issue" scripts/orq/agy_cerrar.sh   # esperado: >= 5
grep -c "agy_cerrar" orchestration/OPERACION_AGENTES.md                                                # esperado: >= 1
git diff --name-only   # ⊆ TERRITORIO
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO. ¿Ejecuta algo pesado? NO. NO cierres agentes, terminales ni worktrees reales desde los tests (hay agentes trabajando: B03, B18, B19, B21, B22).
- Fail-closed: si el destino de una junction no se puede verificar, NO se borra nada y el script para.

## PROHIBIDO (lista negra, sin excepciones)
git de escritura en el repo · rm recursivo · `Remove-Item -Recurse` sobre reparse points · tocar agentes reales · escribir fuera del TERRITORIO · mocks (los fixtures son salidas reales guardadas) · inventar cifras · declarar subagentes.

## SALIDA
1. Working tree con los cambios (SIN commit). 2. orchestration/results/agy/B20.md. 3. orchestration/agy/DONE_B20.md.
4. Cierre: orca orchestration send --type worker_done --subject "B20 <PASA|FALLA|PARCIAL>" --body "<3 frases>" --task-id <T> --dispatch-id <D> --outcome succeeded|failed --json

## CORRECCION_1 (ORQ, 2026-09-02 18:25) — el cierre real falla en el paso 4 (junctions): variables de PowerShell expandidas por bash

Hechos (prueba real del ORQ sobre B19 y B20 con `bash scripts/orq/agy_cerrar.sh B19 ctx_cc6db4af99f7 --issue 34 --etiqueta integrado`): pasos 1-3 OK; en el paso 4 el script muere con `line 295: ErrorActionPreference: unbound variable` y `line 295: wt: unbound variable`, y los pasos 5-7 no se ejecutan (worktree sin retirar, issue sin etiquetar). Causa: el bloque de PowerShell va dentro de comillas dobles de bash con `set -u`, y `$ErrorActionPreference`, `$wt` (y cualquier otra `$variable` de PowerShell) los expande bash. El test `test_agy_cerrar_junctions_safe_removal` pasó porque no ejecuta ese camino del script.

Qué hacer:
1. Todo bloque de PowerShell embebido va con `\$` escapado o, mejor, en un heredoc con delimitador entre comillas simples (`<<'PS'`) escrito a un fichero temporal y ejecutado con `powershell -NoProfile -ExecutionPolicy Bypass -File`. Revisa TODOS los bloques de PowerShell del script, no solo el del paso 4 (`grep -n 'powershell' scripts/orq/agy_cerrar.sh`).
2. Idempotencia: si `worker-release` responde que el dispatch ya no existe o está liberado, o `terminal stop` no encuentra terminales, el paso se marca `OK (ya hecho)` y se sigue; el ORQ va a re-ejecutar el cierre de B19 y B20 con el script corregido.
3. Test de punta a punta REAL: nuevo flag `--solo-junctions <ruta>` que ejecuta únicamente el paso 4 sobre un directorio; el test crea un árbol temporal con `cmd /c mklink /J` hacia un destino con 3 ficheros, invoca el SCRIPT (no una función) con `bash scripts/orq/agy_cerrar.sh X --solo-junctions <tmp>`, y comprueba rc=0, junction eliminada y destino intacto. Añade también `bash -n` y una ejecución con `--sin-worktree` sobre un ID inexistente (`ZZZ`) que debe terminar con rc≠0 y mensaje claro, sin `unbound variable`.
4. Los 14 tests actuales de `tests/test_orq_agentes.py` siguen en verde (ojo: en tu worktree hay 10; el ORQ ya fusionó B19 y B20 en devilray: no reescribas el fichero entero, añade tus casos al final).

Aceptación adicional (el ORQ la re-ejecuta):
```bash
grep -c "unbound" <(bash scripts/orq/agy_cerrar.sh ZZZ --sin-worktree 2>&1) || true     # esperado: 0
grep -c -- "--solo-junctions" scripts/orq/agy_cerrar.sh                                  # esperado: >= 2
```
