"""services/data/holdout_gateway.py
Firewall Criptográfico de Aislamiento de Blind Holdout (Fase 0 - P0).

Garantiza que la partición del 20% más reciente de datos temporales (Blind Holdout OOS)
sea estrictamente inaccesible para cualquier proceso de Búsqueda, Optimización, Algoritmos Genéticos,
o Agentes de Investigación, denegando el acceso y levantando excepciones bloqueantes.
"""

from __future__ import annotations

import hashlib
import hmac
import inspect
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger("HoldoutGateway")


class BlindHoldoutAccessViolation(PermissionError):
    """Excepción forense levantada ante cualquier intento no autorizado de acceso al Blind Holdout."""
    pass


class HoldoutGateway:
    """Guardián criptográfico y particionador inmutable de series temporales de datos físicos."""

    _GATEWAY_SECRET = os.environ.get("HOLDOUT_GATEWAY_SECRET", "ultrarentable_canonical_holdout_firewall_secret_2026")

    @classmethod
    def generate_validation_token(cls, strategy_id: str, strategy_snapshot_hash: str) -> str:
        """Genera un token de autorización criptográfico unívoco para el evaluador ciego final."""
        msg = f"{strategy_id}:{strategy_snapshot_hash}:BLIND_VALIDATION_AUTHORIZED"
        return hmac.new(cls._GATEWAY_SECRET.encode("utf-8"), msg.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def verify_validation_token(cls, strategy_id: str, strategy_snapshot_hash: str, token: str) -> bool:
        """Verifica la validez matemática del token de autorización para acceso a Blind Holdout."""
        expected = cls.generate_validation_token(strategy_id, strategy_snapshot_hash)
        return hmac.compare_digest(expected, token)

    @classmethod
    def get_in_sample_data(cls, candles: list[dict[str, Any]], is_ratio: float = 0.60) -> list[dict[str, Any]]:
        """Devuelve de forma segura el 60% inicial (In-Sample) para exploración y entrenamiento."""
        n = len(candles)
        n_is = int(n * is_ratio)
        return candles[:n_is]

    @classmethod
    def get_validation_data(
        cls,
        candles: list[dict[str, Any]],
        is_ratio: float = 0.60,
        val_ratio: float = 0.20,
    ) -> list[dict[str, Any]]:
        """Devuelve el 20% intermedio (Pre-OOS / Validación WFO) para optimización y calibración."""
        n = len(candles)
        n_is = int(n * is_ratio)
        n_val = int(n * val_ratio)
        return candles[n_is : n_is + n_val]

    @classmethod
    def get_blind_holdout_data(
        cls,
        candles: list[dict[str, Any]],
        strategy_id: str,
        strategy_snapshot_hash: str,
        auth_token: str,
        is_ratio: float = 0.60,
        val_ratio: float = 0.20,
    ) -> list[dict[str, Any]]:
        """Acceso estrictamente protegido al 20% final de datos (Blind Holdout OOS).
        Requiere un token criptográfico válido emitido exclusivamente para el evaluador ciego final.
        """
        # Inspección de pila forense: detectar si algún optimizador o motor de búsqueda está en la cadena de llamadas
        stack = inspect.stack()
        for frame_info in stack:
            filename = frame_info.filename.lower()
            if any(forbidden in filename for forbidden in ["discovery", "genetic", "optimizer", "search", "autopilot", "miner"]):
                raise BlindHoldoutAccessViolation(
                    f"VIOLACION_DE_FIREWALL_HOLDOUT: El módulo '{frame_info.filename}' (función '{frame_info.function}') "
                    f"intentó acceder a la partición ciega de validación (Blind Holdout). "
                    f"Acceso denegado de forma incondicional por la Directiva Maestra de Cero Simulación y Cero Fuga de Datos."
                )

        if not cls.verify_validation_token(strategy_id, strategy_snapshot_hash, auth_token):
            raise BlindHoldoutAccessViolation(
                f"TOKEN_DE_VALIDACION_INVALIDO_O_AUSENTE: No se suministró un token de autorización válido "
                f"para la estrategia '{strategy_id}'. El Blind Holdout permanece sellado criptográficamente."
            )

        n = len(candles)
        n_is = int(n * is_ratio)
        n_val = int(n * val_ratio)
        return candles[n_is + n_val :]
