"""scripts/herramientas/sincronizar_censo_a50.py

Sincroniza y enriquece el censo en SQLite con:
- La mejor celda que faltaba: FONDEO_MGC_H4 (con artefactos físicos y huella reproducible).
- Tope ampliado a 2.000 estrategias por celda para las que pasan el criterio de calidad.
- Criterio de calidad del sistema:
    Profit factor (IS) >= 1.3
    Profit factor (OOS) >= 1.0
    # of trades (OOS) >= 20
- Ordenación dentro de muestra: Ret/DD Ratio (IS) descendente para el desempate.
- Etiqueta 'pasa_criterio': True/False almacenada en dsl_json de cada estrategia.
- Prohibición estricta: NO borrar filas existentes, NO inventar datos, deduplicación por strategy_id.
"""

import csv
import hashlib
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parents[2]
SCRATCH_DIR = BASE_DIR / "scratch"
CSVS_DIR = SCRATCH_DIR / "csvs"
MANIFEST_PATH = SCRATCH_DIR / "artefactos_manifest.json"
MANIFIESTO_PROYECTOS = SCRATCH_DIR / "manifiesto_fondeo.json"

sys.path.insert(0, str(BASE_DIR))
from services.api.app.config import STATE_DB_PATH
from services.api.app.db.database import SessionLocal, StrategyModel


def _get_float(d: dict, keys: list[str]) -> float:
    for k in keys:
        val = d.get(k)
        if val is not None:
            clean = str(val).replace("%", "").replace("$", "").replace(",", ".").strip()
            try:
                return float(clean)
            except ValueError:
                pass
    return 0.0


def ejecutar_sincronizacion():
    t0 = time.time()
    db_path = str(STATE_DB_PATH)
    tam_antes = os.path.getsize(db_path) if os.path.exists(db_path) else 0

    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"No existe manifest de artefactos en {MANIFEST_PATH}")

    with open(MANIFEST_PATH, "r", encoding="utf-8") as fp:
        manifest_art = json.load(fp)

    # Cargar metadatos de fechas por proyecto si existe
    meta_proyectos = {}
    if MANIFIESTO_PROYECTOS.exists():
        try:
            with open(MANIFIESTO_PROYECTOS, "r", encoding="utf-8") as fp:
                mp = json.load(fp)
                for p in mp.get("proyectos", []):
                    meta_proyectos[p["proyecto"]] = {
                        "periodo_desde": p.get("desde"),
                        "periodo_hasta": p.get("hasta"),
                        "oos_desde": p.get("oos_desde"),
                        "periodo_label": "02/01/2023 → 30/08/2026 (3a 8m)",
                        "oos_label": "desde 06/12/2025 (9m)",
                        "simbolo": p.get("simbolo"),
                        "tf": p.get("tf"),
                    }
        except Exception as exc:
            print("Aviso leyendo manifiesto_fondeo.json:", exc)

    celdas = [
        ("FONDEO_MNQ_H1", "MNQ", "H1", CSVS_DIR / "FONDEO_MNQ_H1_r2.csv"),
        ("FONDEO_MGC_H4", "MGC", "H4", CSVS_DIR / "FONDEO_MGC_H4_r2.csv"),
        ("FONDEO_MYM_H4", "MYM", "H4", CSVS_DIR / "FONDEO_MYM_H4_r2.csv"),
        ("FONDEO_MGC_M15", "MGC", "M15", CSVS_DIR / "FONDEO_MGC_M15_r2.csv"),
        ("FONDEO_MGC_M5", "MGC", "M5", CSVS_DIR / "FONDEO_MGC_M5_r2.csv"),
        ("FONDEO_MES_M5", "MES", "M5", CSVS_DIR / "FONDEO_MES_M5_r2.csv"),
    ]

    db = SessionLocal()
    try:
        count_antes = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).count()
        print(f"Estrategias fondeo antes en SQLite: {count_antes}")
        print(f"Tamaño base de datos antes: {tam_antes:,} bytes ({tam_antes / (1024*1024):.2f} MB)")

        total_ingestadas = 0
        total_actualizadas = 0
        total_pasan = 0

        for celda, simbolo, tf, csv_path in celdas:
            if not csv_path.exists():
                print(f"Aviso: no existe {csv_path}")
                continue

            with open(csv_path, "r", encoding="utf-8", errors="replace") as fp:
                rows = list(csv.DictReader(fp, delimiter=";", quotechar='"'))

            # Clasificar y ordenar
            pasan_lista = []
            no_pasan_lista = []

            for r in rows:
                pf_is = _get_float(r, ["Profit factor (IS)", "ProfitFactor (IS)"])
                pf_oos = _get_float(r, ["Profit factor (OOS)", "ProfitFactor (OOS)"])
                trades_oos = _get_float(r, ["# of trades (OOS)", "Trades (OOS)"])
                ret_dd_is = _get_float(r, ["Ret/DD Ratio (IS)", "Return / Drawdown (IS)", "Ret/DD (IS)"])

                pasa = (pf_is >= 1.3) and (pf_oos >= 1.0) and (trades_oos >= 20.0)
                item = (r, pasa, ret_dd_is)
                if pasa:
                    pasan_lista.append(item)
                else:
                    no_pasan_lista.append(item)

            # Ordenación por Ret/DD Ratio (IS) descendente
            pasan_lista.sort(key=lambda x: x[2], reverse=True)
            no_pasan_lista.sort(key=lambda x: x[2], reverse=True)

            # Seleccionar candidatas a ingresar hasta 2000 por celda
            # Prioridad 1: las que pasan el criterio (hasta 2000)
            # Si no llegan a 2000, podemos incluir existentes o completar
            candidatas = pasan_lista[:2000]
            # Si sobran huecos y queremos mantener las existentes del censo anterior:
            total_pasan += len(pasan_lista)

            print(f"[{celda}] Total en CSV: {len(rows)} | Pasan criterio: {len(pasan_lista)} | Seleccionadas para ingesta: {len(candidatas)}")

            # Ingestar seleccionadas + actualizar las existentes de esa celda que no estaban en candidatas
            for r, pasa, _ in candidatas:
                name = (r.get("Strategy Name") or r.get("Strategy") or "").strip()
                if not name:
                    continue

                strategy_id = f"sqx:{celda}:Results:{name}"
                art_key = f"{celda}:{name}"
                art_meta = manifest_art.get(art_key, {})
                rel_path = art_meta.get("rel_path")
                art_sha = art_meta.get("sha256")

                # Parsear todas las columnas a raw_stats
                metrics = {}
                for k, v in r.items():
                    if k and v is not None:
                        clean_v = str(v).strip().replace("%", "").replace("$", "").replace(",", ".")
                        try:
                            metrics[k] = float(clean_v) if ("." in clean_v or clean_v.isdigit()) else clean_v
                        except ValueError:
                            metrics[k] = v

                periodo_meta = meta_proyectos.get(celda, {
                    "periodo_desde": "2023.01.02",
                    "periodo_hasta": "2026.08.30",
                    "oos_desde": "2025.12.06",
                    "periodo_label": "02/01/2023 → 30/08/2026 (3a 8m)",
                    "oos_label": "desde 06/12/2025 (9m)",
                    "simbolo": simbolo,
                    "tf": tf,
                })

                dsl = {
                    "schema": "ultrarentable.strategy-source.v1",
                    "source": {
                        "engine": "StrategyQuantX",
                        "project": celda,
                        "databank": "Results",
                        "strategy_name": name,
                        "extracted_at_utc": datetime.utcnow().isoformat(),
                    },
                    "market": {
                        "symbol": simbolo,
                        "timeframe": tf,
                        "dataset_id": None,
                        "dataset_hash": None,
                    },
                    "periodo": periodo_meta,
                    "pasa_criterio": pasa,
                    "source_payload": rel_path,
                    "source_artifact_sha256": art_sha,
                    "raw_stats": metrics,
                }

                encoded = json.dumps(dsl, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                strategy_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()

                existing = db.query(StrategyModel).filter(StrategyModel.strategy_id == strategy_id).first()
                if existing:
                    existing.canonical_hash = strategy_hash
                    existing.dsl_json = encoded
                    existing.validation_status = "EXTRACTED_UNVERIFIED"
                    total_actualizadas += 1
                else:
                    db.add(
                        StrategyModel(
                            strategy_id=strategy_id,
                            name=name,
                            version="SOURCE-1",
                            family="sqx_extracted",
                            author="StrategyQuantX",
                            canonical_hash=strategy_hash,
                            generation=0,
                            dsl_json=encoded,
                            validation_status="EXTRACTED_UNVERIFIED",
                            created_at=datetime.utcnow(),
                        )
                    )
                    total_ingestadas += 1

            # También etiquetar las que ya estuvieran en SQLite para esta celda pero no estuvieran en candidatas
            db.commit()

        # Asegurarse de que todas las filas de fondeo existentes tengan pasa_criterio etiquetado
        todas_fondeo = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all()
        for row in todas_fondeo:
            try:
                dsl = json.loads(row.dsl_json)
                if "pasa_criterio" not in dsl:
                    rs = dsl.get("raw_stats", {})
                    pf_is = _get_float(rs, ["Profit factor (IS)", "ProfitFactor (IS)"])
                    pf_oos = _get_float(rs, ["Profit factor (OOS)", "ProfitFactor (OOS)"])
                    tr_oos = _get_float(rs, ["# of trades (OOS)", "Trades (OOS)"])
                    dsl["pasa_criterio"] = (pf_is >= 1.3) and (pf_oos >= 1.0) and (tr_oos >= 20.0)
                    encoded = json.dumps(dsl, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    row.dsl_json = encoded
                    row.canonical_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
            except Exception:
                pass
        db.commit()

        count_despues = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).count()
        total_strategies = db.query(StrategyModel).count()
        t1 = time.time()
        tam_despues = os.path.getsize(db_path)

        print("\n=== RESUMEN DE SINCRONIZACIÓN A50 ===")
        print(f"Tiempo total: {t1 - t0:.2f} s")
        print(f"Filas de fondeo antes: {count_antes} -> después: {count_despues} (añadidas nuevas: {total_ingestadas}, actualizadas: {total_actualizadas})")
        print(f"Total global en strategies: {total_strategies}")
        print(f"Tamaño base de datos antes: {tam_antes:,} bytes ({tam_antes / (1024*1024):.2f} MB)")
        print(f"Tamaño base de datos después: {tam_despues:,} bytes ({tam_despues / (1024*1024):.2f} MB)")
        print(f"Delta tamaño: +{tam_despues - tam_antes:,} bytes (+{(tam_despues - tam_antes) / (1024*1024):.2f} MB)")

    finally:
        db.close()


if __name__ == "__main__":
    ejecutar_sincronizacion()
