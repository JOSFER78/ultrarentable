"""
Extractor Estructurado con LLM (Hermes Local :8742 / FreeLLMAPI)
Ultrarentable V3.2.0 · Zero Mocks & Physical Evidence Verification
"""

import httpx
import json
import logging
from typing import Optional, Dict, Any
from .models import PropFirmUpdateData

logger = logging.getLogger(__name__)

HERMES_LLM_URL = "http://127.0.0.1:8742/v1/chat/completions"


class LLMExtractor:
    def __init__(self, endpoint_url: str = HERMES_LLM_URL):
        self.endpoint_url = endpoint_url

    async def extract_firm_data(
        self, firm_slug: str, firm_name: str, official_url: str, raw_text: str
    ) -> Optional[PropFirmUpdateData]:
        system_prompt = (
            "Eres un auditor forense de empresas de fondeo de futuros CME bajo la estricta Doctrina Zero-Mocks.\n"
            "Tu tarea es extraer los datos reales de precios, cupones activos, tipos de drawdown (EOD, STATIC, INTRADAY) "
            "y cuotas de activación a partir del texto scrapeado de la web oficial.\n"
            "REGLAS INQUEBRANTABLES:\n"
            "1. PROHIBIDO INVENTAR: Si un dato no aparece explícitamente en el texto, descártalo o indícalo.\n"
            "2. Toda cifra debe tener una cita textual exacta en 'evidence_quote'.\n"
            "3. Devuelve ÚNICAMENTE un objeto JSON válido que cumpla con el esquema PropFirmUpdateData."
        )

        user_prompt = f"Firma: {firm_name} ({firm_slug})\nURL: {official_url}\nTexto:\n{raw_text}"

        payload = {
            "model": "gemini-2.5-flash",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.0,
            "response_format": {"type": "json_object"},
        }

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                res = await client.post(self.endpoint_url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return PropFirmUpdateData(**parsed)
                else:
                    logger.warning(f"Hermes LLM returned status {res.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error in LLMExtractor: {e}")
            return None
