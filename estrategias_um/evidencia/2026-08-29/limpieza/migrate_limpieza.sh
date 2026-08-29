#!/usr/bin/env bash
# =============================================================================
# migrate_limpieza.sh — Reorganización del repo "01 Ultrarentable" (DISEÑO)
#
# REGLAS:
#   * NADA sale del repo: todo elemento se REORGANIZA o va a cuarentena/.
#   * NO se borra nada. Solo `mv` seguros (git mv cuando aplica).
#   * DRY-RUN por defecto: EXEC=0. Pasa EXEC=1 para aplicar de verdad.
#   * Idempotente: si el origen no existe o el destino ya existe, se omite.
#   * Cada mv se registra en cuarentena/manifest.csv con sha256 previo.
#
# USO:
#   bash migrate_limpieza.sh            # dry-run (solo plan + manifest de intentos)
#   EXEC=1 bash migrate_limpieza.sh     # ejecución real
#
# REQUISITO PREVIO: working tree limpio o al menos commit del usuario.
#   (La directiva maestra prohíbe commits automáticos: el usuario commitea.)
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

# Crea carpetas destino (en EXEC=1; en dry-run solo se listan)
create_dirs() {
  local dirs=(
    "docs/handoffs" "docs/audits" "docs/informes"
    "configs" "scripts/auditorias" "scripts/herramientas"
    "data/db" "data/backups" "evidencia"
    "orchestracion" "cuarentena/logs" "cuarentena/scratch"
    "cuarentena/phase2" "cuarentena/build_artifacts"
    "services/strategy_core" "tests/phase_phase"
  )
  for d in "${dirs[@]}"; do
    if [[ "$EXEC" == "1" ]]; then mkdir -p "$REPO/$d"; fi
  done
}

# do_mv <origen-relativo> <destino-relativo>
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

# NOTA: mover canonical_strategy.py can romper imports (tests y services lo
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
