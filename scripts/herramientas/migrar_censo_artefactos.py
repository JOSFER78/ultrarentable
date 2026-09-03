"""scripts/herramientas/migrar_censo_artefactos.py

Actualiza las filas de fondeo en el censo (StrategyModel) para asociar:
- source_payload: ruta relativa del artefacto en el repositorio de evidencia.
- source_artifact_sha256: huella SHA-256 física del fichero .sqx en disco.
- canonical_hash: hashlib.sha256(dsl_json.encode('utf-8')).hexdigest() (reproducible).
"""

import json
import hashlib
from pathlib import Path
from services.api.app.db.database import SessionLocal, StrategyModel

MANIFEST_PATH = Path(__file__).resolve().parents[2] / "scratch" / "artefactos_manifest.json"
MGC_M15_R2_CSV_SHA256 = "03ee55bae7ef21b239662cc16ba76c2dfeda96afc3688d8bb31dc15408f03a6c"


def migrar_censo():
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"No existe {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as fp:
        manifest = json.load(fp)

    db = SessionLocal()
    try:
        rows = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all()
        print(f"Total filas de fondeo a procesar: {len(rows)}")

        actualizadas = 0
        con_sqx = 0
        con_csv = 0

        for r in rows:
            partes = r.strategy_id.split(":")
            project = partes[1]
            name = ":".join(partes[3:])
            key = f"{project}:{name}"

            if key in manifest:
                rel_path = manifest[key]["rel_path"]
                sha256_art = manifest[key]["sha256"]
                con_sqx += 1
            elif project == "FONDEO_MGC_M15":
                rel_path = "fondeo/resultados/FONDEO_MGC_M15_r2.csv"
                sha256_art = MGC_M15_R2_CSV_SHA256
                con_csv += 1
            else:
                print(f"ADVERTENCIA: No se encontró artefacto para {key}")
                continue

            dsl = json.loads(r.dsl_json) if r.dsl_json else {}
            dsl["source_payload"] = rel_path
            dsl["source_artifact_sha256"] = sha256_art

            # Serialización canónica determinista
            encoded = json.dumps(dsl, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            new_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()

            r.dsl_json = encoded
            r.canonical_hash = new_hash
            actualizadas += 1

        db.commit()
        print(f"Censo migrado con éxito: {actualizadas} filas actualizadas ({con_sqx} con .sqx, {con_csv} con .csv)")
    finally:
        db.close()


if __name__ == "__main__":
    migrar_censo()
