"""
Modelos Pydantic v2 para el Motor de Extracción y Actualización Autónoma con IA
Ultrarentable V3.2.0 · Zero Mocks Architecture
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


class AccountTierExtraction(BaseModel):
    tier_name: str = Field(..., description="Nombre del plan o cuenta, ej: 50K Rapid")
    account_size_usd: float = Field(..., description="Tamaño nominal de balance simulado")
    exam_price_regular_usd: float = Field(..., description="Precio regular de suscripción o pago único")
    exam_price_promo_usd: float = Field(..., description="Precio con cupón aplicado")
    active_coupon_code: str = Field(..., description="Código de cupón oficial")
    discount_percentage: float = Field(..., description="Porcentaje de descuento (0 a 100)")
    activation_fee_usd: float = Field(0.0, description="Cuota de activación al aprobar ($0 si es gratis)")
    profit_target_usd: float = Field(..., description="Objetivo de beneficio")
    max_drawdown_usd: float = Field(..., description="Límite de pérdida máxima")
    drawdown_type: str = Field(..., description="STATIC, EOD_TRAILING, INTRADAY_TRAILING")
    daily_loss_limit_usd: float = Field(0.0, description="Límite diario de pérdida (0 si no aplica)")
    max_contracts_minis: int = Field(..., description="Contratos máximos permitidos en Minis")
    bot_policy: str = Field(..., description="ALLOWED_100, RESTRICTED, PROHIBITED")
    payout_frequency: str = Field(..., description="DAY_1_ON_DEMAND, SAME_DAY_BUSINESS, BIWEEKLY, WEEKLY, MONTHLY")
    evidence_quote: str = Field(..., description="Cita textual exacta de la web oficial que respalda estos datos")


class PropFirmUpdateData(BaseModel):
    firm_slug: str = Field(..., description="Identificador único, ej: mffu, topstep, tradeify")
    firm_name: str = Field(..., description="Nombre oficial de la firma")
    official_website: str = Field(..., description="URL oficial")
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    active_coupons: List[Dict[str, Any]] = Field(default_factory=list)
    accounts: List[AccountTierExtraction] = Field(default_factory=list)
    rules_notes: Optional[str] = None


class AIUpdateRunStatus(BaseModel):
    run_id: str
    status: str  # "IDLE", "RUNNING", "COMPLETED", "FAILED"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    firms_scanned: int = 0
    firms_updated: int = 0
    changes_detected: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
