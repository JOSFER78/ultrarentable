# Review Fase 1 (2ª iteración) — Auditoría del orquestador (2026-08-29 ~18:56 UTC)

## Qué hizo el ejecutor (verificado)
- ✅ Router `services/api/app/api/strategy_lab_router.py`: hardcode `Results` eliminado como default. Ahora: `databank` como query param + `os.environ.get("SQX_EXTRACT_DATABANK", "Last generation")` (líneas 162, 174-176, 246-248). Fail-closed correcto (502 con motivo real).
- ✅ UI `apps/web/app/estrategias/SQXToolsPanel.tsx` + `apps/web/lib/api.ts`: selector de databanks conectado a `/api/v1/sqx/projects/{p}/databanks` y extracción pasando `?databank=` (encodeURIComponent). Modificados en git status, sin commit (correcto).
- ❌ **Criterio de éxito CRÍTICO NO CUMPLIDO:** `POST /api/v2/strategy-lab/extract/Ultra_Matrix?databank=Last%20generation` (re-ejecutado por el auditor 18:50:26 UTC) devuelve **502**: `SQX_UNAVAILABLE: SQX export failed: Error: Databank 'Last' doesn't exist.` → found=0 estrategias extraídas, no ≥90.

## Causa raíz (diagnóstico forense del auditor, verificado en vivo contra el motor)
1. El transporte de `services/sqx_bridge/sqx_client.py` (`call()`, línea 41) envía `name=Last%20generation` por `/call?cmd=`. El HTTP de sqcli trocea el comando por espacios incondicionalmente → el motor recibe `name=Last`. Probado y descartado por el auditor: `%20`, comillas simples/dobles crudas, `+`, escape con `\`, doble-encode, `position=` (obliga `name=`), y rutas de servlet alternativas. **Ninguna forma con espacio pasa por `/call?cmd=`.**
2. **Vía real que SÍ funciona (descubierta en la auditoría):** `-run file=<path>` por HTTP (`/call?cmd=-run%20file=/tmp/x.txt`) ejecuta el archivo con tokenización estilo CLI, que sí acepta `name="Last generation"`:
   - `count` → `Records: 91` (18:54:43 UTC)
   - `export` → `Databank contents exported.` + CSV real de 100 líneas (1 header + 99 estrategias) en `/tmp/sqx_lastgen_audit.csv` (18:55:08 UTC)
3. El estado real del banco es **`Last generation` = 99 registros** (listado directo a las 18:51:34 UTC; el export da 99 filas — el `count` por `-run` devolvió 91, discrepancia count vs export sin resolver, usar siempre el CSV exportado como verdad). **El semillero está vivo y accesible; el fallo es 100% del transporte del cliente Python, no del motor.**

## Hallazgo grave de reporting
El log del ejecutor (TEST 3) etiqueta el fallo `Databank 'Last' doesn't exist` como "Estado real del motor SQX" — es FALSO: es un artefacto del transporte. Un error de instrumentación no es estado del motor. Esto es lo mismo que causó el fallo de la iteración anterior con otro síntoma.

## Deficiencias menores
- El log no contiene los diffs de los archivos modificados ni la descripción de acciones por subagente (exigido por la fase).
- `version_manifest.json` aparece como untracked en git status sin explicación en el log (posible artefacto no solicitado — NO borrarlo; el usuario decidirá).
- Discrepancia count(91) vs export(99) del mismo banco: documentarla.

## Veredicto

```json
{"veredicto": "repite", "razon": "Router y UI bien implementados, pero el criterio de éxito clave falla: la extracción real por HTTP devuelve 502 porque sqx_client.py usa /call?cmd= que trocea valores con espacio (name=Last). El auditor verificó en vivo que el banco 'Last generation' tiene 99 registros y que la vía '-run file=' con name=\"Last generation\" SÍ funciona (count=91, export CSV real de 99 estrategias). Corrección: reescribir el transporte de SQXMCPClient para comandos con valores con espacios usando -run file= (archivo temporal con comillas CLI), manteniendo solo-lectura, y completar el reporting (diffs + discrepancia count/export)."}
```

---

# Review Fase 1 (3ª iteración) — Auditoría del orquestador (2026-08-29 ~19:05 UTC)

## Verificación propia (comandos del auditor, no confío en el informe)

| Criterio de `current_phase.md` (3ª iter.) | Resultado de la auditoría |
|---|---|
| Router sin hardcode `Results` (default = query param + env) | ✅ PASS — verificado en `strategy_lab_router.py` (líneas 162, 174-176); fail-closed con listado de bancos disponible |
| Transporte `call_cli` vía `-run file=` en `sqx_client.py` | ✅ PASS — implementado (líneas 50-60, usado por `list_strategies`/`export_databank`); git status muestra el archivo modificado, sin commit |
| curl REAL `databank=Last%20generation` → found ≥90 | ✅ PASS — **re-ejecutado por el auditor 19:04 UTC: HTTP 200, `found: 92`, `named: 92`, `inserted: 79`** |
| Regresión `databank=Results` (sin espacio) → found 0 | ✅ PASS — re-ejecutado por el auditor 19:04 UTC: HTTP 200, found 0, sin error de transporte |
| Fail-closed banco inexistente | ✅ PASS (log del ejecutor: 502 con bancos disponibles) — coherente con el código del router |
| UI selector + botón conectados | ✅ PASS — archivos modificados en git (`SQXToolsPanel.tsx`, `api.ts`), consistente con iteración 2 ya auditada |
| Log con salidas crudas + discrepancia count vs export | ✅ PASS — `results/fase_01.log` documenta count(91) vs export(99 filas) |
| Sin git commit; solo archivos de la fase | ✅ PASS — `git status`: 6 archivos modificados de la fase + orchestration/ + `version_manifest.json` untracked (preexistente, sin explicar) |

## Observaciones (no bloqueantes)
1. **found varía entre ejecuciones:** el ejecutor reportó found=94 (18:58), el auditor midió found=92 (19:04). El banco vive en RAM y el motor puede reciclar estrategias entre ticks — coherente con el riesgo documentado (semillero solo en RAM). El criterio ≥90 se cumple en ambas.
2. **inserted(79) < named(92) con unchanged=0 y quarantined=0:** 13 estrategias nombradas no quedaron insertadas en esa pasada (probable dedup por identidad contra las 94 ya insertadas a las 18:58). Conviene que la contabilidad extract/insert sea explícita en fases futuras (campo `duplicates` o similar).
3. `version_manifest.json` sigue untracked sin explicación — decisión del usuario, NO borrar.
4. El semillero (`Last generation`, ~92-99 registros) sigue vivo SOLO en RAM del motor. Riesgo de pérdida persiste hasta ejecutar la captura a ToImprove + CSV.

## Veredicto

```json
{"veredicto": "avanza", "razon": "Los 4 criterios técnicos de la fase se verifican con comandos propios: transporte call_cli vía -run file= implementado, extracción real HTTP 200 found=92 (>=90) re-ejecutada por el auditor a las 19:04 UTC, regresión con banco sin espacio correcta (found=0) y fail-closed honesto. Sin commits. La siguiente fase (captura del semillero a ToImprove + CSV en ventana de parada) requiere visto bueno del usuario -> needs_user_input."}
```
