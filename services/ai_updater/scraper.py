"""
Scraper HTTP Asíncrono de Páginas Oficiales y Help Desks de Prop Firms
Ultrarentable V3.2.0 · Zero Mocks Architecture
"""

import httpx
import logging
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
]


class PropFirmScraper:
    def __init__(self, timeout_seconds: float = 12.0):
        self.timeout = timeout_seconds

    async def fetch_clean_text(self, url: str) -> Optional[str]:
        headers = {
            "User-Agent": USER_AGENTS[0],
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code == 200:
                    return self._html_to_clean_text(resp.text)
                else:
                    logger.warning(f"Failed to fetch {url} - Status {resp.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return None

    def _html_to_clean_text(self, html: str) -> str:
        # Remover scripts, estilos y etiquetas HTML básicas
        text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
        text = re.sub(r"<[^>]+>", " ", text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:12000]  # Limitar tamaño de ventana para el LLM
