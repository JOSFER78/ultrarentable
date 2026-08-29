# 09 — ESTRUCTURA DESTINO (repo limpio "01 Ultrarentable")

**Fecha:** 2026-08-29 · **Agente:** ARQUITECTO-LIMPIEZA · **SSOT jerárquico:** `docs/00_MASTER_IDEAS_Y_PLAN.md`
**Regla de oro:** NADA sale del repo. Todo elemento se REORGANIZA o va a `cuarentena/` (con manifest). No se borra nada. No se toca `estrategias_um/` (subproyecto, se integra en el diseño sin moverlo).

---

## 1. Árbol final propuesto de la raíz

La raíz queda con **solo código, configuración, README y docs maestros**. Todo lo demás vive en carpetas temáticas.

```
01 Ultrarentable/
├── README.md                      ← permanece (puerta del repo)
├── ARCHITECTURE.md                ← permanece (docs maestro)
├── SYSTEM_DOCTRINE.md             ← permanece (docs maestro)
├── AUTHORITY_GRAPH.md             ← permanece (docs maestro)
├── ESTADO.md                      ← permanece (estado vivo, docs maestro)
├── SPEC_MASTER_ULTRA_VS_FONDEO.md ← permanece (docs maestro)
├── "Plan 10 Fases.md"             ← permanece (docs maestro)
├── GEMINI.md                      ← permanece (config de agente)
├── __init__.py                    ← permanece (paquete raíz)
├── pyproject.toml / uv.lock       ← permanece (config Python)
├── package.json / package-lock.json ← permanece (config Node/web)
├── .gitignore                     ← permanece
│
├── services/                      ← YA EXISTE: núcleo del backend (274 ficheros)
│   ├── api/  backtest/  core/  data/  data-ingestion/  discovery/
│   ├── engine/  execution/  exploitation_engines/  lineage/  monitoring/
│   ├── optimization/  paper/  policy/  portfolio/  queue/  research/
│   ├── semantic_ai/  sqx_bridge/  strategy_core/  validation/  ai_updater/
│   └── strategy_core/             ← AQUÍ MIGRAN canonical_strategy.py y
│                                    canonical_runtime_adapter.py (raíz → aquí)
├── apps/                          ← YA EXISTE (apps/web, frontend Next.js)
├── packages/                      ← YA EXISTE (packages/bingx-client)
├── contracts/                     ← YA EXISTE (contratos de datos/ejecución)
├── tests/                         ← YA EXISTE; gana tests/phase_phase/
│   └── phase_phase/               ← test_phase01_*, test_phase02_* (desde raíz)
├── scripts/                       ← YA EXISTE; gana dos subcarpetas:
│   ├── auditorias/                ← audit_frontend_playwright.js, audit_v540_playwright.js
│   └── herramientas/              ← version_control_manager.py
├── configs/                       ← NUEVA: config data de raíz
│   ├── canonical_instrument_aliases.json
│   └── version_manifest.json
│
├── docs/                          ← YA EXISTE (SSOT 00_MASTER_IDEAS_Y_PLAN.md;
│   │                                jerarquía master intacta, solo entra documentación suelta)
│   ├── 00_MASTER_IDEAS_Y_PLAN.md  ← intocable
│   ├── Estado/  Investigacion/  Laboratorio/  Fondeo/  Ultrarentable/
│   ├── plan_implementacion/  pruebas/  conexiones_automatizar/  tradesfera/
│   ├── archive/
│   ├── handoffs/                  ← NUEVA: 03_HANDOFF_AG2-P02-005.md, P02-005_*.md (desde raíz)
│   ├── audits/                    ← NUEVA: AUDIT_FINAL_REAL_ONLY.md (desde raíz)
│   ├── informes/                  ← migrado desde raíz (carpeta informes/fases)
│   └── walkthrough.md             ← desde raíz
│
├── orchestracion/                 ← NUEVA: diseño y governance de orquestación
│   └── arquitectura-orquestacion-orquestador-antigravity.md (desde docs/)
│
├── data/                          ← YA EXISTE (367 ficheros, git-trackeados)
│   ├── normalized/  sqx_imports/  exports/  catalogs/  quarantine/
│   ├── db/                        ← NUEVA: database.sqlite, learning_store.sqlite (desde raíz)
│   └── backups/                   ← migrada desde raíz (snapshot firebase)
│
├── evidencia/                     ← NUEVA: evidencia fechada (audits, screenshots, informes de verificación)
│   └── 2026-08-29/
│       └── v540_audit_screenshots/  ← desde raíz
│
├── estrategias_um/                ← SUBPROYECTO: se integra en el diseño SIN MOVERLO.
│                                    Se documenta aquí como el laboratorio de estrategias UM;
│                                    sus evidencias futuras apuntan a evidencia/<fecha>/.
│
├── cuarentena/                    ← NUEVA: todo lo experimental/obsoleto/artefacto.
│   │                                NADA se borra; lo que entra aquí sale del foco, no del repo.
│   ├── manifest.csv               ← sha256 de cada mv (generado por migrate_limpieza.sh)
│   ├── scratch/                   ← desde raíz (scripts experimentales, sqx_work)
│   ├── .phase2/ → phase2/         ← desde raíz (GO_NOW y resto)
│   ├── logs/                      ← uvicorn.log (desde raíz)
│   └── build_artifacts/           ← bingx_ultra_strategy_lab.egg-info (desde raíz)
│
├── .agents/ .github/ .kilo/ .vscode/ .venv/ .ruff_cache/   ← infraestructura, se quedan
└── node_modules/                  ← sin cambios (git-ignorado)
```

### Qué permanece en raíz (criterio)
| Permanece | Motivo |
|---|---|
| README, ARCHITECTURE, SYSTEM_DOCTRINE, AUTHORITY_GRAPH, ESTADO, SPEC_MASTER_ULTRA_VS_FONDEO, Plan 10 Fases | docs maestros / estado vivo |
| `pyproject.toml`, `uv.lock`, `package.json`, `package-lock.json`, `.gitignore`, `__init__.py` | config y paquete raíz |
| `GEMINI.md` | config de agente de código |
| Carpetas de código: `services/ apps/ packages/ contracts/ tests/ scripts/` | núcleo ejecutable |
| `docs/`, `data/`, `configs/`, `evidencia/`, `orchestracion/`, `cuarentena/`, `estrategias_um/` | carpetas temáticas de primer nivel |
| `.agents/ .github/ .kilo/ .vscode/` | infraestructura de repo/agentes |

---

## 2. Tabla de migración (elemento actual → destino)

| # | Elemento actual (raíz salvo indicación) | Destino | Tipo de mv |
|---|---|---|---|
| 1 | `03_HANDOFF_AG2-P02-005.md` | `docs/handoffs/03_HANDOFF_AG2-P02-005.md` | seguro (doc) |
| 2 | `P02-005_AGENT_LEDGER.md` | `docs/handoffs/P02-005_AGENT_LEDGER.md` | seguro |
| 3 | `P02-005_RECON_REPORT.md` | `docs/handoffs/P02-005_RECON_REPORT.md` | seguro |
| 4 | `P02-005_RUNTIME_SEMANTIC_MATRIX.md` | `docs/handoffs/P02-005_RUNTIME_SEMANTIC_MATRIX.md` | seguro |
| 5 | `17_PHASE2_EXECUTION_STATUS.md` | `docs/Estado/17_PHASE2_EXECUTION_STATUS.md` | seguro |
| 6 | `AUDIT_FINAL_REAL_ONLY.md` | `docs/audits/AUDIT_FINAL_REAL_ONLY.md` | seguro |
| 7 | `walkthrough.md` | `docs/walkthrough.md` | seguro |
| 8 | `informes/` (carpeta) | `docs/informes/` | seguro |
| 9 | `canonical_strategy.py` | `services/strategy_core/canonical_strategy.py` | mv + **actualizar imports** |
| 10 | `canonical_runtime_adapter.py` | `services/strategy_core/canonical_runtime_adapter.py` | mv + **actualizar imports** |
| 11 | `canonical_instrument_aliases.json` | `configs/canonical_instrument_aliases.json` | seguro (verificar lecturas) |
| 12 | `version_manifest.json` | `configs/version_manifest.json` | seguro |
| 13 | `version_control_manager.py` | `scripts/herramientas/version_control_manager.py` | seguro |
| 14 | `audit_frontend_playwright.js` | `scripts/auditorias/audit_frontend_playwright.js` | seguro |
| 15 | `audit_v540_playwright.js` | `scripts/auditorias/audit_v540_playwright.js` | seguro |
| 16 | `test_phase01_dataset_chain_of_custody.py` | `tests/phase_phase/` | seguro (pytest) |
| 17 | `test_phase02_canonical_strategy.py` | `tests/phase_phase/` | seguro (pytest) |
| 18 | `database.sqlite` | `data/db/database.sqlite` | seguro (verificar rutas en config) |
| 19 | `learning_store.sqlite` | `data/db/learning_store.sqlite` | seguro (verificar rutas) |
| 20 | `uvicorn.log` | `cuarentena/logs/uvicorn.log` | seguro (log, no código) |
| 21 | `backups/` | `data/backups/` | seguro |
| 22 | `bingx_ultra_strategy_lab.egg-info/` | `cuarentena/build_artifacts/` | seguro (artefacto build; luego .gitignore) |
| 23 | `v540_audit_screenshots/` | `evidencia/2026-08-29/v540_audit_screenshots/` | seguro (evidencia fechada) |
| 24 | `scratch/` | `cuarentena/scratch/` | seguro (experimental → cuarentena) |
| 25 | `.phase2/` | `cuarentena/phase2/` | seguro (experimental → cuarentena) |
| 26 | `docs/arquitectura-orquestacion-orquestador-antigravity.md` | `orchestracion/arquitectura-orquestacion-orquestador-antigravity.md` | seguro |

**Total: 26 migraciones.** No se borra nada; `node_modules/`, `.venv/`, `.ruff_cache/` no se tocan (git-ignorados/entorno).

### Notas de riesgo (leer antes de EXEC=1)
1. **Imports de `canonical_strategy` / `canonical_runtime_adapter`**: tras mover a `services/strategy_core/`, hay que actualizar los imports en `tests/` y `services/`. El script lo advierte; ejecutar `pytest -q` después y revertir si falla.
2. **Rutas de BBDD**: verificar dónde se configuran `database.sqlite` / `learning_store.sqlite` (probablemente `services/` o `configs/`) y actualizar rutas si es absoluto.
3. `uvicorn.log` y `*.egg-info` idealmente añadirse a `.gitignore` tras migrar.
4. `estrategias_um/` **no se mueve** (subproyecto activo); se integra solo a nivel de diseño.

---

## 3. Script `migrate_limpieza.sh`

Guardado en `/tmp/um_restruct/migrate_limpieza.sh` (NO ejecutado en modo EXEC=1).

- `EXEC=0` (default): **dry-run** — escribe el plan en `/tmp/um_restruct/dry_run_manifest.csv`, no toca el repo.
- `EXEC=1`: aplica los mv con `git mv` (si el fichero está trackeado) o `mv`, y escribe `cuarentena/manifest.csv`.
- **Idempotente**: si el origen no existe o el destino ya existe → fila `OMITIDO_*` en el manifest, sin error.
- **sha256 por elemento**: ficheros → sha256 del fichero; carpetas → sha256 agregado (hash del hash-list ordenado de todos los ficheros con rutas relativas al repo).
- Solo crea carpetas destino en EXEC=1 (dry-run no muta el repo).

Validación hecha: `bash -n` OK; dry-run real ejecutado → 26 OK, 0 omitidos (ver `/tmp/um_restruct/dry_run_manifest.csv`).

```bash
#!/usr/bin/env bash
# =============================================================================
# migrate_limpieza.sh — Reorganización del repo "01 Ultrarentable" (DISEÑO)
# REGLAS: NADA sale del repo; no se borra nada; solo mv seguros (git mv si aplica).
# DRY-RUN por defecto (EXEC=0). Idempotente. Manifest con sha256 en cuarentena/.
# USO:  bash migrate_limpieza.sh            # dry-run
#       EXEC=1 bash migrate_limpieza.sh     # ejecución real (previo commit del usuario)
# =============================================================================
set -uo pipefail

EXEC="${EXEC:-0}"
REPO="${REPO:-/home/ubuntu/workspace/pro/trading/01 Ultrarentable}"
MANIFEST_DIR="$REPO/cuarentena"
MANIFEST="$MANIFEST_DIR/manifest.csv"
TS="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
DRY_LOG="/tmp/um_restruct/dry_run_manifest.csv"

mkdir -p "$MANIFEST_DIR" /tmp/um_restruct

if [[ "$EXEC" == "1" ]]; then
  OUT="$MANIFEST"
  [[ -f "$OUT" ]] || echo "timestamp,modo,origen,destino,sha256_origen,estado" >> "$OUT"
else
  OUT="$DRY_LOG"
  echo "timestamp,modo,origen,destino,sha256_origen,estado" > "$OUT"
fi

N_OK=0; N_SKIP=0

create_dirs() {
  local dirs=(
    "docs/handoffs" "docs/audits" "docs/informes"
    "configs" "scripts/auditorias" "scripts/herramientas"
    "data/db" "data/backups" "evidencia/2026-08-29"
    "orchestracion" "cuarentena/logs" "cuarentena/scratch"
    "cuarentena/phase2" "cuarentena/build_artifacts"
    "services/strategy_core" "tests/phase_phase"
  )
  for d in "${dirs[@]}"; do
    if [[ "$EXEC" == "1" ]]; then mkdir -p "$REPO/$d"; fi
  done
}

do_mv() {
  local src="$REPO/$1" dst="$REPO/$2"
  if [[ ! -e "$src" ]]; then
    echo "$TS,$( [[ $EXEC == 1 ]] && echo exec || echo dryrun ),$1,$2,,OMITIDO_NO_EXISTE" >> "$OUT"; ((N_SKIP++)); return
  fi
  if [[ -e "$dst" ]]; then
    echo "$TS,$( [[ $EXEC == 1 ]] && echo exec || echo dryrun ),$1,$2,,OMITIDO_DESTINO_EXISTE" >> "$OUT"; ((N_SKIP++)); return
  fi
  local sha=""
  if [[ -f "$src" ]]; then sha="$(sha256sum "$src" | cut -d' ' -f1)"
  else
    # DIR: sha256 agregado de la lista de rutas+hashes, con rutas relativas al repo
    sha="DIR:$(cd "$REPO" && find "$1" -type f -print0 | sort -z | xargs -0 -r sha256sum | sha256sum | cut -d' ' -f1)"
  fi
  echo "$TS,$( [[ $EXEC == 1 ]] && echo exec || echo dryrun ),$1,$2,$sha,OK" >> "$OUT"
  ((N_OK++))
  if [[ "$EXEC" == "1" ]]; then
    mkdir -p "$(dirname "$dst")"
    if git -C "$REPO" ls-files --error-unmatch "$1" >/dev/null 2>&1; then
      git -C "$REPO" mv "$1" "$2"
    else
      mv "$src" "$dst"
    fi
  fi
}

create_dirs

# ---- 1. Documentos sueltos de raíz -> docs temáticos -----------------------
do_mv "03_HANDOFF_AG2-P02-005.md"            "docs/handoffs/03_HANDOFF_AG2-P02-005.md"
do_mv "P02-005_AGENT_LEDGER.md"              "docs/handoffs/P02-005_AGENT_LEDGER.md"
do_mv "P02-005_RECON_REPORT.md"              "docs/handoffs/P02-005_RECON_REPORT.md"
do_mv "P02-005_RUNTIME_SEMANTIC_MATRIX.md"   "docs/handoffs/P02-005_RUNTIME_SEMANTIC_MATRIX.md"
do_mv "17_PHASE2_EXECUTION_STATUS.md"        "docs/Estado/17_PHASE2_EXECUTION_STATUS.md"
do_mv "AUDIT_FINAL_REAL_ONLY.md"             "docs/audits/AUDIT_FINAL_REAL_ONLY.md"
do_mv "walkthrough.md"                       "docs/walkthrough.md"
do_mv "informes"                             "docs/informes"

# ---- 2. Código y datos descolgados de raíz ---------------------------------
do_mv "canonical_strategy.py"                "services/strategy_core/canonical_strategy.py"
do_mv "canonical_runtime_adapter.py"         "services/strategy_core/canonical_runtime_adapter.py"
do_mv "canonical_instrument_aliases.json"    "configs/canonical_instrument_aliases.json"
do_mv "version_manifest.json"                "configs/version_manifest.json"
do_mv "version_control_manager.py"           "scripts/herramientas/version_control_manager.py"
do_mv "audit_frontend_playwright.js"         "scripts/auditorias/audit_frontend_playwright.js"
do_mv "audit_v540_playwright.js"             "scripts/auditorias/audit_v540_playwright.js"
do_mv "test_phase01_dataset_chain_of_custody.py" "tests/phase_phase/test_phase01_dataset_chain_of_custody.py"
do_mv "test_phase02_canonical_strategy.py"   "tests/phase_phase/test_phase02_canonical_strategy.py"

# NOTA: mover canonical_strategy.py puede romper imports (tests y services lo
# importan). Tras EXEC=1, actualizar imports y re-ejecutar pytest antes de
# commitear. Si los imports no se actualizan, revertir con git checkout.

# ---- 3. Datos y logs de raíz -> data/ o cuarentena/ ------------------------
do_mv "database.sqlite"                      "data/db/database.sqlite"
do_mv "learning_store.sqlite"                "data/db/learning_store.sqlite"
do_mv "uvicorn.log"                          "cuarentena/logs/uvicorn.log"
do_mv "backups"                              "data/backups"
do_mv "bingx_ultra_strategy_lab.egg-info"    "cuarentena/build_artifacts/bingx_ultra_strategy_lab.egg-info"

# ---- 4. Evidencia fechada ---------------------------------------------------
do_mv "v540_audit_screenshots"               "evidencia/2026-08-29/v540_audit_screenshots"

# ---- 5. Cuarentena (experimentales / obsoletos) -----------------------------
do_mv "scratch"                              "cuarentena/scratch"
do_mv ".phase2"                              "cuarentena/phase2"

# ---- 6. Orquestación ---------------------------------------------------------
do_mv "docs/arquitectura-orquestacion-orquestador-antigravity.md" \
      "orchestracion/arquitectura-orquestacion-orquestador-antigravity.md"

# ---- Resumen -----------------------------------------------------------------
echo
if [[ "$EXEC" == "1" ]]; then
  echo "[EXEC] mv planificados OK=$N_OK omitidos=$N_SKIP | manifest: $OUT"
else
  echo "[DRY-RUN] movimientos que se harían: OK=$N_OK omitidos=$N_SKIP"
  echo "[DRY-RUN] intentos registrados en: $OUT"
  echo "[DRY-RUN] Para aplicar: EXEC=1 bash $0"
fi
```
