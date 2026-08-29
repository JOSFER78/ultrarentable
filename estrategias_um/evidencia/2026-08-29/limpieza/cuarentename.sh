#!/usr/bin/env bash
# cuarentename.sh — cuarentena segura (DRY-RUN por defecto, NO ejecutar sin revisar)
set -euo pipefail
REPO="/home/ubuntu/workspace/pro/trading/01 Ultrarentable"
DEST="$REPO/cuarentena/$(date +%Y%m%d_%H%M)"
DRY_RUN="${DRY_RUN:-1}"
MANIFEST="$DEST/manifest.csv"

ITEMS=(
  "apps/web/node_modules|REGENERABLE|npm i regenera"
  "apps/web/.next|REGENERABLE|next build regenera"
  "node_modules|REGENERABLE|npm i regenera"
  ".kilo|REGENERABLE|cache plugins, se recrea"
  "v540_audit_screenshots|HISTORICO|pngs auditoria v540"
  "apps/web/frontend_audit_screenshots|HISTORICO|pngs auditoria frontend"
  "scratch|HISTORICO|notas temporales"
  "informes|HISTORICO|informes cerrados"
  ".ruff_cache|REGENERABLE|cache linter"
)

echo "== DRY_RUN=$DRY_RUN =="
mkdir -p "$DEST"
echo "item,tamano,clase,destino,motivo" > "$MANIFEST"

for entry in "${ITEMS[@]}"; do
  IFS='|' read -r rel clase motivo <<< "$entry"
  src="$REPO/$rel"
  [ -e "$src" ] || { echo "SKIP (no existe): $rel"; continue; }
  if find "$src" -maxdepth 0 -newermt '-3 hours' | grep -q .; then
    echo "SKIP (mtime<3h): $rel"; continue
  fi
  sz=$(du -sh "$src" | cut -f1)
  dst_name="${rel//\//_}"
  echo "DRY-RUN mv: '$src' -> '$DEST/$dst_name'"
  echo "$rel,$sz,$clase,$DEST/$dst_name,$motivo" >> "$MANIFEST"
  if [ "$DRY_RUN" = "0" ]; then
    mv "$src" "$DEST/$dst_name"
  fi
done
echo "Manifest: $MANIFEST"
echo "WARNING: .venv EXCLUIDO a proposito (uvicorn activo PID 1705570)."
