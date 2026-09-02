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
 (agy_lanzar.sh)     (agy_censo.ps1)        (Orquestador)      (worker-release + agy_matar.ps1)
```

### Fase 1: Lanzamiento Limpio y Endurecido (`scripts/orq/agy_lanzar.sh` v2)
1. **Vaciar MCP**: Ejecuta `mcp_vacio.ps1` antes de arrancar para evitar carga parasitaria de servidores Node/Python.
2. **Worktree Resiliente**: Crea worktree aislado con `orca worktree create <rama> --setup skip`. Si Orca agota su timeout (60-90 s) pero el directorio aparece, `esperar_worktree` sondea la existencia de `<worktree>/.git` (≤ 90 s, sondeo cada 2 s) sin abortar. Restaura drift en `package-lock.json` y crea junctions (`node_modules`, `data/normalized`) según el tipo de agente.
3. **Confianza Pre-sembrada**: Inyecta la ruta del worktree en `trustedWorkspaces` de `.gemini/antigravity-cli/settings.json` antes de iniciar el agente.
4. **Terminal Puro y TUI**: Crea terminal con comando puro (`agy --model gemini-3.7-flash-high --dangerously-skip-permissions`), espera banner y sincronización a `tui-idle`.
5. **Creación de Tarea y Worker**: Crea la tarea en Orca (`orca orchestration task-create`) y vincula el worker (`orca orchestration worker-start`).
6. **Verificación de Prompt y Re-despacho Único**: Comprueba durante 60 s que el prompt se envió correctamente. Si `orca orchestration worker-list --json` muestra `dispatchStatus: failed` o el cuadro de entrada queda atascado con el spec, detiene el terminal (`orca terminal stop --worktree path:<ruta>`), resetea la tarea (`orca orchestration task-update --id <task> --status ready`) y re-despacha UNA sola vez reutilizando la secuencia limpia.
7. **Vigilancia Activa de Encuesta CLI**: Durante los primeros 180 s vigila la pantalla cada 10 s y, si aparece `How's the CLI experience`, envía `0` + Enter de forma autónoma.
8. **Telemetría y Registro de Fases**: Registra en `orchestration/state/agentes.jsonl` una línea JSON estructurada con: `id`, `hora`, `pid`, `worktree`, `t_worktree`, `t_terminal`, `t_banner`, `t_idle`, `t_start`, `t_total`, `hijos`, `mb`, `reintento_prompt`, `task`, `dispatch`, `terminal`, `hijos_no_shell`.

#### Tiempos Esperados por Fase (Medidos en Host Windows 11)
- **`t_worktree`**: 0 - 30 s (worktree existente / rápido) o 60 - 90 s si Orca agota timeout pero completa creación.
- **`t_terminal`**: 0.7 - 5 s (creación de terminal puro).
- **`t_banner`**: 4 - 20 s (detección de banner Antigravity CLI).
- **`t_idle`**: 5 - 25 s (sincronización `tui-idle`).
- **`t_start`**: 1 - 3 s (`worker-start` y asignación de `dispatchId`).
- **`t_total`**: Típico 25 - 75 s en despacho limpio sin reintento; hasta 150 s si hubo reintento o espera de worktree.

#### Protocolo de Actuación si `t_total` > 180 s
- Si `t_total` > 180 s, el script sale estrictamente con error `rc=1` y no autoriza el despacho.
- **Diagnóstico y Corrección**:
  1. Inspeccionar `orchestration/state/agentes.jsonl` para identificar la fase con exceso de latencia (`t_worktree`, `t_idle`, etc.).
  2. Verificar estado de terminales con `orca terminal list` y leer la consola con `orca terminal read --terminal <handle>`.
  3. Auditar censo de procesos con `powershell -File scripts/orq/agy_censo.ps1` y terminar procesos huérfanos/lentos con `agy_matar.ps1`.
  4. Vaciar servidores parásitos con `powershell -File scripts/orq/mcp_vacio.ps1`.
  5. Comprobar carga de RAM (<78%) y CPU antes de reintentar el despacho.

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

### Fase 4: Cierre Atómico y Censo a Cero
1. Notificar liberación del worker en Orca:
   ```bash
   orca terminal send-raw --handle <worker_terminal> --data "exit\r"
   ```
2. Detener terminal en Orca:
   ```bash
   orca terminal stop --worktree "path:<ruta_worktree>"
   ```
3. Terminar árbol de procesos residuales protegiendo ancestros y procesos críticos:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/agy_matar.ps1 -ProcesoId <PID_AGY>
   ```
4. Comprobar que el censo no contiene procesos huérfanos:
   ```powershell
   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/orq/agy_censo.ps1
   ```

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
