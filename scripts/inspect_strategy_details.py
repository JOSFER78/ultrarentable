"""scripts/inspect_strategy_details.py
Inspección de las 78,550 estrategias reales en la base de datos.
"""
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.api.app.db.database import SessionLocal, StrategyModel

def inspect_details():
    db = SessionLocal()
    try:
        sample = db.query(StrategyModel).filter(StrategyModel.validation_status == "APPROVED").limit(5).all()
        for s in sample:
            print("---")
            print(f"ID: {s.strategy_id}")
            print(f"Name: {s.name}")
            print(f"Family: {s.family}")
            print(f"Validation Status: {s.validation_status}")
            print(f"DSL JSON preview: {s.dsl_json[:200] if s.dsl_json else 'None'}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_details()
