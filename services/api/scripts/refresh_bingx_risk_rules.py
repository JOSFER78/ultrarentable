"""Fase 5: refrescar snapshot de reglas de riesgo + fees de BingX (REAL).

Captura las reglas de margen vigentes de BingX para un símbolo via Playwright,
normaliza y persiste snapshots frescos (instrument_rule + account fee) en la BD
operacional. Desbloquea el fast_engine (requiere snapshots < 24h).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable")
sys.path.insert(0, str(PROJECT_ROOT))

# Asegurar que Playwright captura con el chromium ya instalado
os.environ.setdefault(
    "CHROMIUM_PATH",
    "/home/ubuntu/.cache/ms-playwright/chromium-1223/chrome-linux/chrome",
)

from services.api.app.db.database import SessionLocal
from services.api.app.ingestion.bingx_risk_rules import (
    capture_and_persist_risk_rules,
    capture_and_persist_public_fees,
)

SYMBOL = os.environ.get("SYMBOL", "ETH-USDT")


def main() -> None:
    db = SessionLocal()
    try:
        risk = capture_and_persist_risk_rules(db, SYMBOL)
        print(
            f"RISK_OK symbol={SYMBOL} snapshot_id={risk.snapshot_id} "
            f"max_leverage={risk.max_leverage} captured_at={risk.captured_at}"
        )
        try:
            fee = capture_and_persist_public_fees(db, SYMBOL)
            print(
                f"FEE_OK symbol={SYMBOL} snapshot_id={fee.snapshot_id} "
                f"maker={fee.maker_fee} taker={fee.taker_fee} "
                f"captured_at={fee.captured_at}"
            )
        except Exception as exc:  # fees son secundarias, no bloquear
            print(f"FEE_WARN symbol={SYMBOL}: {exc}")
        db.commit()
    finally:
        db.close()


if __name__ == "__main__":
    main()
