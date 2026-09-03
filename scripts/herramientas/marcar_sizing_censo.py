"""scripts/herramientas/marcar_sizing_censo.py

Marca cada estrategia existente en SQLite con el dimensionamiento con el que fue construida:
FixedSize (1 contrato micro, capital 100.000 USD).
Las nuevas generadas con A47/A51 se marcarán con RiskFixedBalancePct (0.5% riesgo, 50.000 USD).
"""

import hashlib
import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))
from services.api.app.db.database import SessionLocal, StrategyModel


def marcar_sizing():
    db = SessionLocal()
    try:
        filas = db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all()
        print(f"Total estrategias fondeo a etiquetar sizing: {len(filas)}")
        actualizadas = 0

        for r in filas:
            try:
                dsl = json.loads(r.dsl_json)
                if "sizing" not in dsl or dsl["sizing"] is None:
                    # Las 6.167 actuales fueron construidas con la plantilla previa de 1 micro / 100k
                    dsl["sizing"] = {
                        "metodo": "FixedSize",
                        "contratos": 1,
                        "capital": 100000,
                    }
                    encoded = json.dumps(dsl, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                    r.dsl_json = encoded
                    r.canonical_hash = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
                    actualizadas += 1
            except Exception as e:
                print(f"Error en {r.strategy_id}: {e}")

        db.commit()
        print(f"Etiquetadas con sizing: {actualizadas} filas.")

        # Comprobar aceptación 2
        nulos = 0
        total_fondeo = 0
        for r in db.query(StrategyModel).filter(StrategyModel.strategy_id.like("sqx:FONDEO_%")).all():
            total_fondeo += 1
            dsl = json.loads(r.dsl_json)
            if not dsl.get("sizing"):
                nulos += 1

        print(f"Comprobación: Total fondeo: {total_fondeo} | Sizing nulo: {nulos}")
    finally:
        db.close()


if __name__ == "__main__":
    marcar_sizing()
