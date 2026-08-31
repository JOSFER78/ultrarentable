# FASE 0 — AUDITORÍA DEL CHANGESET 258-ARCHIVOS (SOLO LECTURA)

> **ANTES DE EMPEZAR, LEE `orchestration/METODOLOGIA_ANTIGRAVITY.md` ENTERO.** Es tu procedimiento operativo.
> Plan vigente: `orchestration/state/plan_maestro.md` (v3, 2026-08-31).
> Decisiones selladas del usuario: `orchestration/DOCTRINA_ORQUESTADOR.md §14`. **Léelas antes de empezar.**
> Esta fase es **SOLO LECTURA**. Prohibido modificar, arreglar o "mejorar" ningún archivo auditado.

## Contexto (no lo re-investigues, es un hecho verificado)

Entre 2026-08-30 08:46 y 2026-08-31 02:31 se ejecutaron 4 commits en este rango (258 archivos, +28.748 líneas)
**fuera del loop formal**: Firebase Auth + RTDB + ~25 scripts `mine_and_certify_*` + cambios en el
motor de validación. Rango exacto: `23c8733a9..245009fef`.

## Qué tienes que entregar (6 entregables, todos con evidencia cruda)

### E1 — Inventario del changeset
Comando obligatorio (pega la salida REAL en el informe):
`git diff --stat 23c8733a9..245009fef | tail -30`
`git log 23c8733a9..245009fef --oneline`  (son exactamente 4 commits: 687aed29f, cfc3b10c0, f38beaf4b, 245009fef)

### E2 — Auditoría REAL-ONLY de los ~25 scripts `mine_and_certify_*`
Para CADA script en `scripts/` que empiece por `mine_and_certify`, `certify`, `fast_`, `mine_`:
- `grep -n "random\|randint\|uniform\|np.random\|seed(\|fake\|dummy\|mock\|synthetic" <archivo>`
- Por cada coincidencia: ¿es un dato de mercado fabricado, o un uso legítimo (p.ej. semilla de un
  algoritmo genético)? Clasifica cada una: `LEGÍTIMO` / `VIOLACIÓN` / `DUDOSO`.
- Tabla final: fichero | nº coincidencias | veredicto.

### E3 — Diff línea a línea de los 4 ficheros de motor
`git diff 23c8733a9..245009fef -- services/validation/gates/gate_09_novelty_antifit.py`
(y equivalentes para `event_backtest_engine.py`, `discovery_validation_pipeline.py`,
`strategy_search_registry.py`; localiza sus rutas reales con `git diff --name-only`).
Para cada uno responde EXPLÍCITAMENTE:
- ¿Se ha cambiado algún umbral, comparador o condición de aprobación de un gate? SÍ/NO.
- Si SÍ: cita el número de línea, el valor antes y después, y la **dirección**:
  `MÁS ESTRICTO` / `MÁS LAXO` / `NEUTRO`.
- **Cualquier cambio `MÁS LAXO` es una VIOLACIÓN hasta que se demuestre lo contrario.**

### E4 — Estado de la suite de tests
`python3 -m pytest tests/ -q --tb=line 2>&1 | tail -25`
Pega la salida real. Si falla la colección, reporta el error tal cual. NO lo arregles.

### E5 — Censo de certificaciones producidas por esos scripts
- Localiza las estrategias con fecha de certificación entre 2026-08-30 y hoy en
  `~/.local/state/ultrarentable/ultrarentable.sqlite3` y/o `data/evidence/`.
- Para cada una: `strategy_id`, SHA-256, fecha, y **cuántos de los 11 `EvidenceRecord` existen
  físicamente** en `data/evidence/<sid>/gate_*.json` (cuenta ficheros reales con `ls`).
- Si una estrategia figura como certificada pero le faltan gates en disco → `CERTIFICACIÓN SIN EVIDENCIA`.
- Si no encuentras la BD o el directorio: escribe `NO DATA` y el comando que lo demuestra. NO inventes.

### E6 — Veredicto final
Una de estas tres palabras, en la última línea del informe:
`VEREDICTO: LIMPIO` | `VEREDICTO: VIOLACIÓN DETECTADA` | `VEREDICTO: NO_EVIDENCE`
Con un párrafo de justificación anclado a E2–E5.

## Método obligatorio
Multi-agente. Mínimo 3 subagentes en paralelo:
- **A1** → E1 + E2 (scripts de minería)
- **A2** → E3 + E4 (motor de gates y tests)
- **A3** → E5 (censo de evidencias en disco/BD)
El coordinador consolida E6. El informe debe llevar tabla de "qué subagente hizo qué".

## Reglas de esta fase
1. **SOLO LECTURA.** Cero ediciones, cero `git commit`, cero `rm`, cero movimientos de ficheros.
2. **Cero invención.** Todo dato va acompañado del comando que lo produjo y su salida cruda.
   Un dato sin comando reproducible = fase `repite`.
3. Si un comando falla, se pega el error. No se sustituye por una estimación.
4. Informe en `orchestration/results/fase_00.log`. Al terminar: `status = "done"` + fichero `DONE`.

## Nota sobre trabajo en paralelo (IMPORTANTE para tu §4)
El Orquestador está trabajando **en paralelo** en:
- la reorganización documental (`docs/`, `docs/archive/`, `README.md`, `orchestration/*.md`)
- la ingesta de datos Dukascopy (`services/data-ingestion/`, `data/`)

Por eso **`git status` te va a mostrar cambios que NO son tuyos** (renames de `.md`, ficheros
nuevos en `orchestration/` y `services/data-ingestion/`). En tu §4 declara **únicamente** lo que
hayas tocado tú — que en esta fase debe ser **NADA**, porque es solo-lectura. Usa este comando
para demostrarlo, acotado a tu territorio:

`git status --short -- scripts/ services/validation/ services/discovery/ tests/ data/evidence/`

Ese comando debe salir **vacío**. Si sale algo, has tocado lo que no debías.
No toques `docs/`, `services/data-ingestion/`, `data/` ni `orchestration/*.md`. No es tu fase.
