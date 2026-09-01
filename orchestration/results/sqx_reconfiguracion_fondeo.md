# SQX — auditoría y reconfiguración para el carril FONDEO

Fecha: 2026-09-01 · Autor: subagente Hermes (auditoría de `sqx.service` / `Ultra_Matrix`)

## Resumen ejecutivo

El proyecto SQX `Ultra_Matrix` lleva 37+ ciclos hoy generando estrategias sin ningún valor:
**2.035/2.035 estrategias del último export son del mismo símbolo (AUDUSD_H1)** y su OOS es
**decorativo (mediana 1 trade OOS, ratio global OOS/total ≈ 0,27 %)**. Causa raíz identificada
con evidencia en disco (no es un bug de SQX: es una mala generación de `project.cfx`):

1. `Ultra_Matrix` mete **97 `<Setup>` dentro de un único `<Data><Setups>`** de una única tarea
   Build. SQX solo usa el primero (orden alfabético → `AUDUSD_H1`); los otros 96 son XML muerto.
2. El `<OutOfSample><Range>` de esa tarea es la **unión global de fechas de las 97 celdas**
   (min/max de TODAS), no un tramo final anidado dentro del `<Setup>` activo — rompe la
   convención del propio template de SQX.

Se preparó una configuración nueva (**sin tocar `Ultra_Matrix`**) para el carril FONDEO:
4 tareas Build independientes, una por celda símbolo×TF (ES 5m/15m, NQ 5m/15m), cada una con
**un único `<Setup>`** y **OOS = 20 % final del rango propio de cada Setup**. Queda en
`artifacts/sqx/import/Fondeo_ES_NQ_5m15m.cfx` + manifiesto SHA-256, generada por un script nuevo
y reproducible: `scripts/herramientas/generar_sqx_fondeo.py`.

**Bloqueo real, no de configuración**: los datos de los proxies CFD todavía no están completos
en disco ni importados en el `data.db` interno de SQX (ver §4-5). YM (USA30IDXUSD) no tiene
backfill en absoluto todavía.

---

## 1. Dónde vive cada pieza (auditoría)

| Pieza | Ubicación | Notas |
| :--- | :--- | :--- |
| Servicio headless SQX | `systemctl cat sqx.service` → `/etc/systemd/system/sqx.service` | `ExecStart=/home/ubuntu/StrategyQuantX144/sqcli`, puerto 5050, `enabled` |
| Proyecto activo | `/home/ubuntu/StrategyQuantX144/user/projects/Ultra_Matrix/project.cfx` | ZIP con `config.xml` + `Build-Task1.xml` (1,3 MB) + `Improve-Task1.xml` |
| Generador del proyecto | `/home/ubuntu/build_ultra_matrix.py` (fuera del repo, en `$HOME`) | Escribe 97 `<Setup>` en un solo `Build-Task1.xml`; comentario propio línea ~140: *"OutOfSample: dejar el que haya; solo ajustar Range al rango global si existe"* — es la causa raíz confesada en el propio script |
| Cron de auto-mejora | crontab de `ubuntu`, minuto `:40` → `/home/ubuntu/improve_cycle.sh` (copia casi idéntica de `estrategias_um/scripts/improve_cycle.sh` del repo, con un pequeño retry-loop añadido a mano el 30-ago) | Orquesta Build→stop→copy→Improve→export vía `PROJECT="Ultra_Matrix"`; NO decide instrumento/TF/OOS, eso ya viene fijado en `project.cfx` |
| Cliente Python | `services/sqx_bridge/sqx_client.py` | Solo `-project action=start\|stop\|status`, `-databank action=list\|count\|export`; no toca Setups |
| Repartos IS/OOS del Build (evolutivo, dentro del propio Setup) | `<BuildMode><EvoInSamplePeriod ratio="70">` en `Build-Task1.xml` | Es OTRO parámetro (70/30 interno del algoritmo genético), no es el `<OutOfSample><Range>` que se usa como holdout de reporte — ver §3 |
| Datos internos de SQX | `/home/ubuntu/StrategyQuantX144/user/data/data.db` (SQLite, tabla `DATA`: `SYMBOL, TIMEFRAME, DATEFROM, DATETO, ROWS`) | Cada símbolo se importa YA segmentado por TF con nombre dedicado, p.ej. `AUDUSD_H1`, `ES_M5` — confirmado por consulta directa (copia RO) |

## 2. Bug "solo el primer Setup" — evidencia concreta

`Build-Task1.xml` extraído de `Ultra_Matrix/project.cfx` (copia de solo lectura en scratchpad):

```
grep -c "<Setup dateFrom" Build-Task1.xml   → 97
```

El **primer** `<Setup>` del bloque (línea 160, justo tras abrir `<Data>`) es:
```xml
<Setup dateFrom="2023.11.01" dateTo="2026.08.18" ...>
  <Chart symbol="AUDUSD_H1" timeframe="H1" spread="2" spreadValue="0" />
```
Los 4 primeros son `AUDUSD_H1, AUDUSD_H4, AUDUSD_M15, AUDUSD_M5` — alfabéticamente antes que
`ES_*`, `EURUSD_*`, `GBPUSD_*`, `NQ_*`, `YM_*`, etc.

Confirmación empírica sobre el export real (`data/sqx_exports/toimprove_2026-08-31.csv`,
2.035 filas, solo lectura):
```python
syms = set(row['Symbol (IS)'] for row in rows)
# → {'AUDUSD_H1'}   (100 % de 2.035 filas, un único símbolo)
```
La plantilla POR DEFECTO de SQX (`internal/web/BUILDER/templates/tpl_build.xml`, ajena a este
proyecto) solo trae **un** `<Setup>` en `<Data><Setups>` — ese es el contrato real de una tarea
Build: un Setup = un mercado. Meter 97 no hace "portfolio de 97 mercados": SQX toma el primero
y descarta el resto en silencio, sin error ni log.

## 3. OOS decorativo — evidencia cuantificada

`Build-Task1.xml`, bloque `<Data>` (línea 1131):
```xml
<OutOfSample showGraph="false">
  <Range dateFrom="2021.11.03" dateTo="2026.08.18" />
</OutOfSample>
```
`2021.11.03` es **anterior** al `dateFrom` del propio Setup activo (`2023.11.01` para
`AUDUSD_H1`) — el Range de OOS no es un subconjunto del rango del Setup, es la unión global de
las 97 celdas (`gfrom=min(...)`, `gto=max(...)` en `build_ultra_matrix.py`). Comparar con el
template por defecto de SQX, donde el Range de OOS es SIEMPRE la cola final, subconjunto
estricto del único Setup (`Setup: 2014.1.1→2016.12.30`, `OOS Range: 2015.11.15→2016.12.30`,
≈36 % final).

Medición directa sobre las 2.035 filas exportadas:
```python
IS trades:  mediana 326  media 366,7  (min 1, max 1972)
OOS trades: mediana 1    media 1,006  (min 0, max 8)
ratio OOS/(IS+OOS) global = 0,27 %
```
Coincide con el diagnóstico previo ya guardado en
`orchestration/state/PUNTO_GUARDADO_ULTRA.md` ("OOS del 0,3 %, mediana 1 trade") — confirmado
de forma independiente aquí con los números exactos.

## 4. Datos disponibles para el proxy FONDEO (auditoría en disco, solo lectura)

| Instrumento (proxy CFD Dukascopy) | Futuro objetivo | M5/M15 en `data/sqx_imports/dukascopy/` | Rango real | Estado |
| :--- | :--- | :--- | :--- | :--- |
| `USA500IDXUSD` | ES | Sí | 2023.01.02 → 2026.08.30 (1.336 días) | **Completo** |
| `USATECHIDXUSD` | NQ | Sí (parcial) | 2023.01.02 → 2024.09.30 (637 días) | **Backfill en curso** (`data/dukascopy_backfill_progress.json`: hasta 2024-Q3; proceso vivo `run_dukascopy_backfill --start 2023-01-01 --end 2026-08-30`, PID activo, ~3 % CPU — es la excepción I/O-bound autorizada, no tocar) |
| `USA30IDXUSD` | YM | **No existe ningún CSV** | — | **Backfill no iniciado** |

Ninguno de los tres está todavía importado en el `data.db` interno de SQX (consulta directa,
copia de solo lectura: `SELECT ... WHERE SYMBOL LIKE '%USA%'` → 0 filas). Son datos en el
repositorio, no datos que SQX pueda usar todavía.

## 5. Configuración nueva preparada

- **Script generador** (nuevo, en el repo, no toca `Ultra_Matrix`):
  `scripts/herramientas/generar_sqx_fondeo.py`
  - Lee fechas reales directamente de los CSV en disco (sin inventar rangos).
  - Por cada celda genera **un Build-Task con un único `<Setup>`** (nunca varios) y un
    `<OutOfSample><Range>` que es el **20 % final, anidado dentro del rango propio del Setup**
    (`OOS_FRACTION = 0.20`, ≥ el mínimo pedido, igual al "Blind OOS 20 %" ya usado en el resto
    del pipeline).
  - Comisión heredada de `build_ultra_matrix.py::FUT_COMM` (PerTrade $2,4, convención ya
    auditada para ES/NQ en `Ultra_Matrix`) — no se reinventa, se documenta como heredada.
  - El resto del XML (`WhatToBuild`, `RiskMoneyManagement`, `Rankings`, `PartsToImprove`,
    `WalkForward...`) es **byte-idéntico** al `Build-Task1.xml` de producción — verificado
    programáticamente (`resto idéntico fuera de <Data>: True`). Cambio quirúrgico, sin
    rediseñar parámetros de búsqueda que no son objeto de esta tarea.
  - `--check-only` audita qué celdas tienen CSV sin generar nada (usado para YM: `SKIP`).

- **Artefacto generado** (gitignored, igual que `scripts/create_sqx_improvement_project.py`):
  - `artifacts/sqx/import/Fondeo_ES_NQ_5m15m.cfx` (ZIP: `config.xml` + 4×`Build-TaskN.xml`)
  - `artifacts/sqx/import/Fondeo_ES_NQ_5m15m.manifest.json` (SHA-256, rangos, celdas pendientes)
  - SHA-256 del artefacto: `f6793942fa6fa0b2b1b4d450593dd84b9f52402589d622060f68ea79bb6b17fd`

- **4 celdas incluidas AHORA** (datos completos en disco):

  | Tarea | Símbolo SQX | IS | OOS (20 %) |
  | :--- | :--- | :--- | :--- |
  | Build-Task1 (`ES_M5`) | `USA500IDXUSD_M5` | 2023.01.02 → 2025.12.06 | 2025.12.06 → 2026.08.30 (267 días) |
  | Build-Task2 (`ES_M15`) | `USA500IDXUSD_M15` | 2023.01.02 → 2025.12.06 | 2025.12.06 → 2026.08.30 (267 días) |
  | Build-Task3 (`NQ_M5`) | `USATECHIDXUSD_M5` | 2023.01.02 → 2024.05.26 | 2024.05.26 → 2024.09.30 (127 días) |
  | Build-Task4 (`NQ_M15`) | `USATECHIDXUSD_M15` | 2023.01.02 → 2024.05.26 | 2024.05.26 → 2024.09.30 (127 días) |

  **NQ usa el rango parcial disponible HOY** (backfill sigue corriendo). No es un dato
  inventado, pero tampoco es el rango final: hay que **regenerar** `Build-Task3/4` cuando
  `USATECHIDXUSD` llegue a 2026.08.30 (ver comando de regeneración en §6).

- **YM excluido** de este artefacto (celda `PENDING_CELLS` en el script, documentada pero sin
  generar): no hay CSV. Cuando el backfill de `USA30IDXUSD` exista, `--check-only` lo mostrará
  como `OK` automáticamente y basta añadirlo a `CELLS` y regenerar.

## 6. Comandos exactos

**Ninguno de estos pasos reinicia ni para `sqx.service`.** Son llamadas HTTP al servicio ya
en marcha (puerto 5050, igual que hace `improve_cycle.sh`) o copias de fichero dentro del
propio `$HOME` de `ubuntu` (mismo usuario dueño de `StrategyQuantX144/`, no requieren sudo real
— se listan igualmente en un bloque aparte para que Emilio decida si prefiere ejecutarlos él).
El **espacio en la ruta del repo** (`01 Ultrarentable`) obliga a usar transporte `-run file=`,
igual que hace `call_cli()` en `improve_cycle.sh` — nunca pasar `filepath=` directo en la
query string.

### 6.1 Desplegar el proyecto nuevo (no pisa `Ultra_Matrix`)
```bash
mkdir -p /home/ubuntu/StrategyQuantX144/user/projects/Fondeo_ES_NQ_5m15m
cp "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/artifacts/sqx/import/Fondeo_ES_NQ_5m15m.cfx" \
   /home/ubuntu/StrategyQuantX144/user/projects/Fondeo_ES_NQ_5m15m/project.cfx
```

### 6.2 Importar los datos ES en el `data.db` interno de SQX (dato completo, listo hoy)
```bash
for CELL in "USA500IDXUSD_M5:M5" "USA500IDXUSD_M15:M15"; do
  SYM="${CELL%%:*}"; TF="${CELL##*:}"
  cat > /tmp/sqx_import_${SYM}.txt <<EOF
-data action=import symbol=${SYM} instrument=USA500IDXUSD timeframe=${TF} timezone=Etc/UCT bartype=startofbar errorhandling=stop filepath="/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports/dukascopy" filename=${SYM}.csv
EOF
  curl -sS --max-time 300 "http://localhost:5050/call?cmd=-run%20file=/tmp/sqx_import_${SYM}.txt"
done
```
*(sintaxis de `-data action=import` verificada contra la ayuda oficial embebida,
`internal/web/SQUANT/help.txt`; no hay una ejecución previa registrada en logs para confirmar
`bartype`/`timezone` exactos → **primera importación real: verificar el recuento de filas
resultante con `-data action=update` o releyendo `data.db` antes de lanzar el Build**.)*

### 6.3 NQ — esperar a que termine el backfill, luego regenerar y repetir 6.2
```bash
# Comprobar que el backfill de USATECHIDXUSD llegó a 2026-Q3:
cat "/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/dukascopy_backfill_progress.json"
# Cuando esté completo, regenerar el artefacto con el rango final:
cd "/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
rm artifacts/sqx/import/Fondeo_ES_NQ_5m15m.cfx artifacts/sqx/import/Fondeo_ES_NQ_5m15m.manifest.json
python3 scripts/herramientas/generar_sqx_fondeo.py
# y repetir 6.1 + 6.2 (import) para USATECHIDXUSD_M5/M15
```

### 6.4 YM — bloqueado hasta que exista backfill de `USA30IDXUSD`
No hay comando que ejecutar todavía: falta el CSV. Cuando exista (`ls data/sqx_imports/dukascopy/USA30IDXUSD_M*.csv`),
añadir la celda a `CELLS` en `generar_sqx_fondeo.py` (ya está preparada en `PENDING_CELLS`,
mover la tupla) y regenerar.

### 6.5 Verificar que SQX ve el proyecto nuevo
```bash
curl -sS "http://localhost:5050/call?cmd=-project%20action=status%20name=Fondeo_ES_NQ_5m15m"
```
Si responde "proyecto no encontrado" (SQX puede cachear el listado de proyectos al arrancar),
**única acción que sí requiere sudo**, y solo si el paso anterior falla:
```bash
sudo systemctl restart sqx.service
```

### 6.6 Lanzar UNA tarea a la vez — nunca `action=start` del proyecto completo
El bug de §2 es precisamente "SQX usa solo la primera cosa que encuentra". Por prudencia, hasta
tener evidencia de que un proyecto multi-tarea itera correctamente con `-project action=start`,
lanzar cada Build Task por índice explícito (mismo patrón ya probado en `improve_cycle.sh` con
`startOnlyTask task=2` para Improve):
```bash
curl -sS "http://localhost:5050/call?cmd=-project%20action=startOnlyTask%20name=Fondeo_ES_NQ_5m15m%20task=1"
# dejar correr, comprobar en el databank "Results" que Symbol (IS) == USA500IDXUSD_M5 (no otro)
curl -sS "http://localhost:5050/call?cmd=-project%20action=stop%20name=Fondeo_ES_NQ_5m15m"
curl -sS "http://localhost:5050/call?cmd=-project%20action=startOnlyTask%20name=Fondeo_ES_NQ_5m15m%20task=2"
# ... task=3 y task=4 solo tras importar NQ (§6.3)
```

## 7. Riesgos y puntos NO verificados (declarados explícitamente, no se afirma lo que no se probó)

1. **`<Resources><Symbols>`**: `Build-Task1.xml` de `Ultra_Matrix` contiene además un bloque
   `<Resources><Symbols>` con metadatos cacheados de TODOS los símbolos conocidos por SQX
   (`source="1"` uniforme pese a que `build_ultra_matrix.py` había escrito `source="7"` para
   cripto — indicio de que SQX **reescribe este bloque solo** al abrir/guardar el proyecto,
   sincronizándolo contra su `data.db` real). Los `Build-TaskN.xml` nuevos heredan el bloque
   viejo (97 símbolos de `Ultra_Matrix`, sin entradas para `USA500IDXUSD_*`/`USATECHIDXUSD_*`).
   **No se ha verificado empíricamente** que SQX lo autocorrija al cargar el proyecto nuevo. Si
   al abrir `Fondeo_ES_NQ_5m15m` SQX se queja de símbolo desconocido pese a estar ya importado
   en `data.db` (§6.2), este es el primer sitio a mirar.
2. **Multi-Task en un mismo proyecto**: no hay evidencia (en logs ni en documentación local) de
   que `-project action=start` itere correctamente las 4 tareas Build. Por eso §6.6 recomienda
   `startOnlyTask` una por una, no `start` del proyecto — evita repetir exactamente el patrón
   de bug ya confirmado en §2.
3. **Comando de import (§6.2)**: la sintaxis viene de la ayuda oficial embebida del propio SQX,
   no de un log de ejecución real anterior contra estos ficheros. Primera vez que se ejecuta:
   confirmar recuento de filas importado contra el `wc -l` del CSV fuente antes de fiarse.
4. **NQ con rango parcial**: si se importa y se lanza Build-Task3/4 ANTES de que termine el
   backfill de `USATECHIDXUSD`, el resultado quedará atado a datos hasta 2024-09-30 únicamente
   — hay que regenerar y reimportar cuando el backfill complete (§6.3), no maquillar el `.cfx`
   con una fecha de fin que los datos no respaldan.

## 8. Ficheros de esta entrega

- `scripts/herramientas/generar_sqx_fondeo.py` — nuevo, en git, reproducible (`--check-only`
  para reauditar disponibilidad de datos en cualquier momento).
- `artifacts/sqx/import/Fondeo_ES_NQ_5m15m.cfx` + `.manifest.json` — nuevos, gitignored (misma
  convención que `scripts/create_sqx_improvement_project.py` / `artifacts/sqx/import/`).
- Este informe: `orchestration/results/sqx_reconfiguracion_fondeo.md`.
- `Ultra_Matrix` **no se ha tocado**: ni `project.cfx`, ni `databanks/`, ni el cron, ni el
  servicio. `data/sqx_imports/`, `data/sqx_exports/` y `data.db` de SQX se han leído siempre
  desde copias de solo lectura en el scratchpad de esta sesión.
