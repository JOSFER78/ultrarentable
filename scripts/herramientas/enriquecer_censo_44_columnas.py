"""scripts/herramientas/enriquecer_censo_44_columnas.py

Enriquece las 1.651 filas de fondeo en el censo con:
1. Periodo del manifiesto: periodo_desde, periodo_hasta, oos_desde, periodo_label, oos_label.
2. Todas las 44 columnas exportadas por StrategyQuant X almacenadas en raw_stats.
3. Actualización de canonical_hash = sha256(dsl_json).
"""

import csv
import json
import hashlib
from pathlib import Path
from services.api.app.db.database import SessionLocal, StrategyModel

ROOT = Path(__file__).resolve().parents[2]
MANIFIESTO_PATH = ROOT / "scratch" / "manifiesto_fondeo.json"
CSVS_DIR = ROOT / "scratch" / "csvs"


def parse_float_safe(val: str | None) -> float | None:
    if val is None:
        return None
    v = str(val).strip().replace("%", "").replace("$", "").replace(",", ".")
    if not v:
        return None
    try:
        return float(v)
    except ValueError:
        return None


def format_periodo_label(desde: str, hasta: str) -> str:
    # 2023.01.02 -> 02/01/2023
    def fmt(s: str) -> str:
        p = s.split(".")
        if len(p) == 3:
            return f"{p[2]}/{p[1]}/{p[0]}"
        return s
    return f"{fmt(desde)} → {fmt(hasta)} (3a 8m)"


def format_oos_label(oos_desde: str) -> str:
    p = oos_desde.split(".")
    if len(p) == 3:
        return f"desde {p[2]}/{p[1]}/{p[0]} (9m)"
    return f"desde {oos_desde} (9m)"


def enriquecer_censo():
    with open(MANIFIESTO_PATH, "r", encoding="utf-8") as fp:
        mani = json.load(fp)

    periodos_por_celda = {}
    for proj in mani.get("proyectos", []):
        p_name = proj.get("proyecto")
        if p_name:
            desde = proj.get("desde", "2023.01.02")
            hasta = proj.get("hasta", "2026.08.30")
            oos_desde = proj.get("oos_desde", "2025.12.06")
            periodos_por_celda[p_name] = {
                "periodo_desde": desde,
                "periodo_hasta": hasta,
                "oos_desde": oos_desde,
                "periodo_label": format_periodo_label(desde, hasta),
                "oos_label": format_oos_label(oos_desde),
                "simbolo": proj.get("simbolo"),
                "tf": proj.get("tf"),
            }

    csv_rows = {}
    for csv_file in CSVS_DIR.glob("*.csv"):
        # deducir celda del nombre del fichero: ej FONDEO_MYM_H4_r2.csv -> FONDEO_MYM_H4
        name_parts = csv_file.stem.split("_r")
        celda = name_parts[0]
        with open(csv_file, "r", encoding="utf-8", errors="replace") as fp:
            reader = csv.DictReader(fp, delimiter=";", quotechar='"')
            for row in reader:
                strat_name = row.get("Strategy Name")
                if strat_name:
                    # Limpiar claves y valores
                    cleaned_row = {}
                    for k, v in row.items():
                        if k is None:
                            continue
                        k_clean = k.strip()
                        cleaned_row[k_clean] = v.strip() if isinstance(v, str) else v
                    csv_rows[(celda, strat_name.strip())] = cleaned_row

    print(f"Total estrategias parseadas de los 5 CSVs: {len(csv_rows)}")

    db = SessionLocal()
    try:
        rows = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all()
        print(f"Total estrategias fondeo en base de datos: {len(rows)}")

        actualizadas = 0
        encontradas_csv = 0

        for r in rows:
            partes = r.strategy_id.split(":")
            project = partes[1]
            strat_name = ":".join(partes[3:])

            dsl = json.loads(r.dsl_json) if r.dsl_json else {}

            # 1. Metadatos de periodo del manifiesto
            p_info = periodos_por_celda.get(project, {
                "periodo_desde": "2023.01.02",
                "periodo_hasta": "2026.08.30",
                "oos_desde": "2025.12.06",
                "periodo_label": "02/01/2023 → 30/08/2026 (3a 8m)",
                "oos_label": "desde 06/12/2025 (9m)",
            })
            dsl["periodo"] = p_info
            if "market" in dsl:
                dsl["market"]["periodo_desde"] = p_info["periodo_desde"]
                dsl["market"]["periodo_hasta"] = p_info["periodo_hasta"]
                dsl["market"]["oos_desde"] = p_info["oos_desde"]

            # 2. Las 44 columnas completas de SQX
            key = (project, strat_name)
            if key in csv_rows:
                encontradas_csv += 1
                raw_44 = csv_rows[key]
                # Preservar o enriquecer raw_stats con las 44 columnas completas
                stats = dsl.get("raw_stats", {})
                for k, v in raw_44.items():
                    stats[k] = v
                dsl["raw_stats"] = stats
                dsl["sqx_44_columns"] = raw_44

            # 3. Serialización determinista y hash canónico
            encoded = json.dumps(dsl, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            new_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()

            r.dsl_json = encoded
            r.canonical_hash = new_hash
            actualizadas += 1

        db.commit()
        print(f"Enriquecimiento completado: {actualizadas} filas actualizadas ({encontradas_csv} con las 44 columnas de CSV)")
    finally:
        db.close()


if __name__ == "__main__":
    enriquecer_censo()
