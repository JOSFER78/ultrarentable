# RUNBOOK OPERACIÓN — Ultra_Matrix (API 5050 headless)

> Solo comandos verificados en vivo. Reglas: read-only libre; toda escritura exige backup del project.cfx + ventana de parada + candado (state-file `~/.improve_cycle_state`). Nunca dos mutaciones en paralelo. Nunca matar el proceso.

## 1. Lecturas seguras (siempre permitidas)
```bash
# Estado del proyecto
curl 'http://localhost:5050/call?cmd=-project%20action=status%20name=Ultra_Matrix'
# Bancos y records — ÚNICA vía fiable para el banco legacy con espacio
curl 'http://localhost:5050/call?cmd=-databank%20action=list%20project=Ultra_Matrix'
```
⚠ "Databank 'Last' doesn't exist" = intentaste `count name=` con espacios: usa `action=list`.

## 2. Fases con candado (toda mutación)
1. **Backup primero:** `cp project.cfx pre_<motivo>_$(date +%Y%m%d_%H%M).cfx` (a `evidencia/backups_cfx/`).
2. **Candado:** state-file `~/.improve_cycle_state` (idle_build|improving) o flock `/tmp/um_cycle.lock`.
3. Fase A PARAR: `-project action=stop name=Ultra_Matrix` → verificar con status.
4. Fase B COPIAR banco (solo parado): `-databank action=copy ... destdatabank=ToImprove` → guard: destino >0; si 0 → re-arrancar y abortar.
5. Fase C EXPORTAR evidencia: `-databank action=export ... file=.../evidencia/YYYY-MM-DD/semillas_YYYYmmdd_HHMM.csv`.
6. Fase D MEJORAR: `-project action=startOnlyTask name=Ultra_Matrix task=2` (task 2 = Improve; verificar índice tras lanzar).
7. Fase E REARRANCAR: `-project action=start name=Ultra_Matrix`.
8. Verificación post: status corriendo + list de bancos con los counts esperados.

## 3. Plantilla STOP → COPY → EXPORT → START
```bash
API='http://localhost:5050/call'
u() { curl -sS --max-time 60 "${API}?cmd=$1"; }
u '-project%20action=status%20name=Ultra_Matrix'                              # 1 pre-check
cp project.cfx pre_captura_$(date +%Y%m%d_%H%M).cfx                           # 2 backup
u '-project%20action=stop%20name=Ultra_Matrix'; sleep 5                       # 3 parar
u '-databank%20action=copy%20project=Ultra_Matrix%20name=Last%20generation%20destproject=Ultra_Matrix%20destdatabank=ToImprove'  # 4
u '-databank%20action=list%20project=Ultra_Matrix'                            # 5 guard >0
u '-databank%20action=export%20project=Ultra_Matrix%20name=Last%20generation%20file=/home/ubuntu/ORDENAR/semillas_$(date +%Y%m%d_%H%M).csv'  # 6
u '-project%20action=startOnlyTask%20name=Ultra_Matrix%20task=2'              # 7 improve
u '-project%20action=start%20name=Ultra_Matrix'                               # 8 arranque
u '-project%20action=status%20name=Ultra_Matrix'                              # 9 verificar
```
(los espacios del banco legacy van como `%20` en copy/export — verificado hoy 16:30: `copy`/`export` sí aceptan %20; solo `count name=` falla)

## 3. Procedimiento de parche de project.cfx (ventana de parada)
```bash
bash /home/ubuntu/workspace/pro/trading/01 Ultrarentable/estrategias_um/scripts/APLICAR.sh
```
(Para el motor por API → backup → patcher.py con dry-run → verificación ZIP → re-arranque → verificación post. Sin verificación: no hay éxito.)

## 4. Errores conocidos
| Mensaje | Significado | Acción |
|---|---|---|
| `Databank 'Last' doesn't exist` | nombre con espacios en `count name=` | usar `action=list` |
| `Project is already running` | mutación con motor caliente | parar primero |
| Parche "aplicado" pero sin efecto | motor sirve config de su memoria | recargar/reiniciar proyecto (ventana) |

## 5. Qué NO se hace
- Tocar project.cfx sin backup ni ventana; editar config con motor caliente; dos mutaciones a la vez; matar el proceso java/sqcli; borrar bancos; commitear (working tree solo).

## 6. Documentos hermanos
ESTADO.md (cómo está hoy) · PLAN_PIPELINE.md (plan por fases) · DECISIONES_LOG.md (qué se decidió) · README.md (mapa).
