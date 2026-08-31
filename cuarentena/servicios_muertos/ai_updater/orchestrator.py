"""
Orquestador de Actualización con IA (Scheduler 24h/48h & On-Demand)
Ultrarentable V3.2.0 · Zero Mocks Architecture
"""

import uuid
import logging
from typing import List, Dict, Any
from datetime import datetime
from .scraper import PropFirmScraper
from .llm_extractor import LLMExtractor
from .db_manager import DatabaseManager

logger = logging.getLogger(__name__)

OFFICIAL_SOURCES = [
    {"slug": "topstep", "name": "Topstep", "url": "https://topstep.com"},
    {"slug": "mffu", "name": "MyFundedFutures", "url": "https://myfundedfutures.com"},
    {"slug": "tradeify", "name": "Tradeify", "url": "https://tradeify.co"},
    {"slug": "apex", "name": "Apex Trader Funding", "url": "https://apextraderfunding.com"},
    {"slug": "tradeday", "name": "TradeDay", "url": "https://tradeday.com"},
    {"slug": "tpt", "name": "Take Profit Trader", "url": "https://takeprofittrader.com"},
    {"slug": "bulenox", "name": "Bulenox", "url": "https://bulenox.com"},
    {"slug": "blusky", "name": "BluSky Trading", "url": "https://blusky.pro"},
]


class AIUpdateOrchestrator:
    def __init__(self):
        self.scraper = PropFirmScraper()
        self.extractor = LLMExtractor()
        self.db = DatabaseManager()

    async def run_update_pipeline(self, force_full_scan: bool = False) -> Dict[str, Any]:
        run_id = f"run_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        logger.info(f"Starting AI update run: {run_id}")
        changes_detected: List[str] = []

        scanned = 0
        updated = 0

        for target in OFFICIAL_SOURCES:
            scanned += 1
            raw_text = await self.scraper.fetch_clean_text(target["url"])
            if raw_text:
                extracted = await self.extractor.extract_firm_data(
                    target["slug"], target["name"], target["url"], raw_text
                )
                if extracted:
                    updated += 1
                    changes_detected.append(f"{target['name']}: Datos verificados mediante scraping.")

        self.db.record_run(run_id, "COMPLETED", changes_detected)

        return {
            "run_id": run_id,
            "status": "COMPLETED",
            "firms_scanned": scanned,
            "firms_updated": updated,
            "changes_detected": changes_detected,
            "timestamp": datetime.utcnow().isoformat(),
        }
