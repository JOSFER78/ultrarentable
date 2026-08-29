# 08 — PLAN DE CUARENTENA (`01 Ultrarentable/`)

Fecha: 2026-08-29 · **DRY-RUN: no se ha movido ni borrado nada.**

## Resumen

| Métrica | Valor |
|---|---|
| Tamaño total repo | **1.8 GB** (`du -sh .`) |
| Recuperable estimado (cuarentena) | **~977 MB** |
| Candidatos a cuarentena | **10** |

Estado runtime detectado: `uvicorn services.api.app.main:app --port 8000` **CORRIENDO** (PID 1705570) usando `.venv` → NO mover `.venv`, `node_modules`, `apps/web/node_modules`, `apps/web/.next`, `data/`, ni los sqlite hasta parar servicios.

## Reglas

- Cuarentena = `mv` a `cuarentena/<fecha>/` + manifest CSV. **Jamás `rm`.**
- No tocar nada con mtime < 3 h.
- NO tocar: `data/` (DATO-VIVO), `database.sqlite`, `learning_store.sqlite`, `backups/`, `uv.lock`, `pyproject.toml`, `.git`, código/docs vigentes.
- Fuera de alcance: `~/.antigravity-ide-server` (no está en este repo).

## Tabla elemento | tamaño | clase | acción propuesta | riesgo

| Elemento | Tamaño | Clase | Acción | Riesgo |
|---|---|---|---|---|
| `apps/web/node_modules/` | 391 MB | REGENERABLE | Cuarentena si se para el frontend; regenerable con `npm i` | ⚠️ ALTO: rompe `next dev/build` si corre. Regenerable |
| `apps/web/.next/` | 155 MB | REGENERABLE | Cuarentena (build cache) | ⚠️ MEDIO: fuerza rebuild; rompe servidor Next si corre |
| `.venv/` | 448 MB | REGENERABLE | **NO mover ahora** — uvicorn activo la usa (PID 1705570) | ⚠️ CRÍTICO: mata la API en ejecución. Regenerable con `uv sync` |
| `node_modules/` (raíz) | 96 MB | REGENERABLE | Cuarentena tras parar procesos Node | ⚠️ MEDIO: rompe tooling npm si corre. Regenerable |
| `.kilo/` | 63 MB | HISTÓRICO | Cuarentena (cache plugin IDE/agentes) | BAJO: se recrea; puede regenerar índices |
| `v540_audit_screenshots/` | 9.8 MB | HISTÓRICO | Cuarentena (PNGs auditoría v540) | BAJO: evidencia, conservada en cuarentena |
| `apps/web/frontend_audit_screenshots/` | 6.8 MB | HISTÓRICO | Cuarentena | BAJO |
| `scratch/` | 1.2 MB | HISTÓRICO | Cuarentena | BAJO |
| `informes/` | 16 KB | HISTÓRICO | Cuarentena (informes cerrados) | BAJO |
| `.ruff_cache/` | 580 KB | REGENERABLE | Cuarentena | MÍNIMO: cache puro |
| `node_modules` + `.next` mtime | — | CHECK | mtime ok (>3h para raíz; revisar en ejecución real) | — |

### NO TOCAR (clase DATO-VIVO / ACTIVO)

| Elemento | Tamaño | Clase | Motivo |
|---|---|---|---|
| `data/` | 321 MB | DATO-VIVO | normalized/sqx_imports/evidence — pipeline real |
| `learning_store.sqlite` | 28 MB | DATO-VIVO | store de aprendizaje activo (mtime 02:06 hoy) |
| `database.sqlite` | 1.6 MB | DATO-VIVO | DB principal (mtime 02:09 hoy) |
| `backups/` | 436 KB | DATO-VIVO | snapshot recuperación firebase |
| `.git/` | 216 MB | ACTIVO | historia; nunca cuarentena |
| `apps/web/app,lib,components…` | ~2 MB | ACTIVO | código fuente frontend |
| `estrategias_um/`, `services/`, `contracts/`, `tests/`, `docs/`, md raíz, `pyproject.toml`, `uv.lock` | ~40 MB | ACTIVO | código y docs vigentes |

## Script `cuarentename.sh` (DRY-RUN — solo echo + manifest)

> Versión final validada en `/tmp/um_restruct/cuarentename.sh` (bash -n OK, dry-run ejecutado; nombres de destino aplanados `apps/web/node_modules` → `apps_web_node_modules` para evitar colisiones). NO EJECUTAR tal cual: imprime los `mv` y genera manifest. Para ejecutar real, cambiar `DRY_RUN=0`.

```bash
#!/usr/bin/env bash
# cuarentename.sh — cuarentena segura (DRY-RUN por defecto)
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
  # regla mtime < 3h
  if find "$src" -maxdepth 0 -newermt '-3 hours' | grep -q .; then
    echo "SKIP (mtime<3h): $rel"; continue
  fi
  sz=$(du -sh "$src" | cut -f1)
  echo "DRY-RUN mv: '$src' -> '$DEST/$(basename "$rel")'"
  echo "$rel,$sz,$clase,$DEST,$motivo" >> "$MANIFEST"
  if [ "$DRY_RUN" = "0" ]; then
    mv "$src" "$DEST/$(basename "$rel")"
  fi
done
echo "Manifest: $MANIFEST"
echo "WARNING: .venv EXCLUIDO a proposito (uvicorn activo PID 1705570)."
```

## Orden recomendado de liberación

1. Parar uvicorn/frontend → confirmar sin procesos vivos.
2. Ejecutar `DRY_RUN=1 bash cuarentename.sh` → revisar manifest.
3. Ejecutar `DRY_RUN=0 bash cuarentename.sh` (con .venv aún excluido).
4. `.venv` solo en cuarentena tras decidir regenerarlo (`uv sync`).
5. Recuperación: `mv cuarentena/<fecha>/<item> <ruta_original>` consultando manifest.
