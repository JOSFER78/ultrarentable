# Protocolo Operativo de Gobernanza de Agentes Antigravity (AGY)

> **Autoridad & Ámbito**: Procedimiento canónico de gestión del ciclo de vida de agentes en el entorno Orca / Ultrarentable.  
> **Directiva de IA**: Pure Antigravity (`gemini-3.7-flash-high`). Prohibición absoluta de Codex (Emilio, 2026-09-02).

---

## 1. Capacidad del Sistema y Guardarraíles de Recursos

El hardware del host local tiene límites estrictos de concurrencia para evitar degradación térmica, saturación de RAM y colisión con procesos críticos (campañas de minería, compilaciones):

- **Límite de Agentes Concurrentes**: Máximo **6 - 7 workers** de Antigravity simultáneos.
- **Techo de Memoria RAM**: RAM total del sistema **< 78%**. Si supera el 80%, pausar nuevos despachos.
- **Tareas Pesadas Simultáneas**: Máximo **2 tareas intensivas** concurrentes (ej. minería SQX, `next build`, backtests masivos).
- **Procesos Protegidos Intocables**: `gobernanza_recursos`, `mine.py`, `cola_mineria`, `sqcli`, `next build`. Ninguna herramienta de limpieza o terminación puede tocarlos a ellos, a sus descendientes ni a sus procesos ancestros.

---

## 2. Ciclo de Vida Oficial del Agente

El ciclo de vida de todo worker despachado consta de 4 fases deterministas:

```
[1. LANZAR] ──> [2. AUDITAR (45s)] ──> [3. INTEGRAR] ──> [4. CERRAR]
 (agy_lanzar.sh)     (agy_censo.ps1)        (Orquestador)      (agy_cerrar.sh)
```

### Fase 1: Lanzamiento Limpio (`scripts/orq/agy_lanzar.sh`)
1. Comprobar que MCP está limpio ejecutando `mcp_vacio.ps1`.
2. Crear worktree aislado con `orca worktree create <rama> --setup skip`.
3. Inyectar el worktree en `.gemini/antigravity-ide/settings.json` (`security.workspace.trust.untrustedFiles = "open"`).
4. Crear terminal con `orca terminal create --type antigravity-cli --args "--model gemini-3.7-flash-high"`.
5. Esperar banner inicial y sincronización a `tui-idle`.
6. Crear tarea en Orca (`orca task create`) y despachar worker (`orca task start`).

### Fase 2: Auditoría Parasitaria a los 45 Segundos
A los 45 segundos del arranque, auditar el censo de procesos:
```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/agy_censo.ps1
```
- **Umbral Aceptable**: ≤ 3 descendientes, RAM < 450 MB por worker.
- **Detección de Parásitos**: Si `descendientes > 5` o `RAM > 1000 MB`, indica que el IDE reescribió `mcp_config.json` y levantó servidores Node/Python no deseados.
- **Acción Correctora**: Ejecutar `mcp_vacio.ps1` y `agy_limpiar.ps1`.

### Fase 3: Integración del Entregable
El coordinador de Orca verifica el commit/diff en el worktree del worker y re-ejecuta los comandos de verificación de forma independiente.

### Fase 4: Cierre Atómico y Censo a Cero (`scripts/orq/agy_cerrar.sh`)

Cierre completo, determinista y seguro de un agente agy:
```bash
scripts/orq/agy_cerrar.sh <ID> [<dispatchId>] [--sin-worktree] [--issue N --etiqueta integrado|repite]
```

Ejemplos:
```bash
# Cierre tras integración completa (libera worker, detiene terminal, limpia censo, borra junctions, elimina worktree y cierra issue)
scripts/orq/agy_cerrar.sh B15 --issue 42 --etiqueta integrado

# Cierre conservando el worktree para inspección forense
scripts/orq/agy_cerrar.sh B15 --sin-worktree

# Cierre con dispatch explícito
scripts/orq/agy_cerrar.sh B15 ctx_675fbc52ee66 --issue 42 --etiqueta repite
```

El script ejecuta de forma secuencial y parando al primer fallo (`fail-closed`):
1. `orca orchestration worker-release --dispatch <ctx>` (timeout 25s; auto-descubrimiento en `worker-list` si no se especifica `ctx`).
2. `orca terminal stop --worktree path:<ruta_worktree>` para terminar el terminal supervisado.
3. Censo de procesos: comprueba que ningún `agy.exe` del worktree sigue vivo (vía `agy_matar.ps1` sin `-Forzar` protegiendo ancestros/minería) y purga procesos MCP huérfanos.
4. Reparse Points / Junctions: eliminación segura con `(New-Object IO.DirectoryInfo <ruta>).Delete()` tras verificar que los destinos existen y preservan todas sus entradas.
5. Worktree Git: eliminación atómica con `git -C <checkout> worktree remove --force <ruta>` y `git worktree prune` (omitido con `--sin-worktree`).
6. GitHub Issues: si se pasa `--issue N`, ejecuta `gh issue edit N --add-label <etiqueta> --remove-label en-vuelo` (y `gh issue close N` si `--etiqueta integrado`).
7. Registro de auditoría: emite evento estructurado en `orchestration/state/agentes.jsonl` (`evento: cierre`).

---

## 3. Recuperación ante Reinicio de Antigravity IDE

Si Antigravity IDE o una extensión reescribe `~/.gemini/config/mcp_config.json` o `~/.gemini/antigravity-ide/mcp_config.json` con servidores MCP pesados:

1. Ejecutar de inmediato:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/mcp_vacio.ps1
   ```
   *(El script guarda automáticamente un backup fechado antes de vaciar a `{"mcpServers": {}}`)*.

2. Purgar servidores MCP huérfanos desvinculados:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/agy_limpiar.ps1
   ```

3. Verificar con el censo que los workers vuelven al estado óptimo (≤ 3 descendientes).

---

## 4. Prohibición Explícita de Codex (Emilio, 2026-09-02)

Queda **estrictamente prohibido** invocar, configurar o referenciar `codex` como backend o worker. Todos los agentes deben operar bajo el motor oficial Antigravity (`agy` con modelo `gemini-3.7-flash-high`).
