from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Iterable, Sequence


class MarginModelError(ValueError):
    """Raised when a position cannot be modelled without inventing exchange rules."""


class PositionSide(str, Enum):
    LONG = "LONG"
    SHORT = "SHORT"

    @property
    def direction(self) -> int:
        return 1 if self is PositionSide.LONG else -1


class MarginMode(str, Enum):
    ISOLATED = "ISOLATED"
    CROSS = "CROSS"


@dataclass
class MarginPosition:
    """Compatibility shape used by the current FastEngine until phase 3."""

    side: PositionSide
    margin_mode: MarginMode
    leverage: int
    entry_price: float
    quantity: float
    initial_margin: float
    maintenance_margin_rate: float = 0.005


def calculate_unrealized_pnl(
    side: PositionSide,
    entry_price: float,
    current_price: float,
    quantity: float,
) -> float:
    direction = 1.0 if side is PositionSide.LONG else -1.0
    return direction * (current_price - entry_price) * quantity


def is_liquidated(
    position: MarginPosition,
    current_price: float,
    equity: float,
) -> bool:
    """Legacy flat-rate check retained only until FastEngine integration."""

    notional = position.quantity * current_price
    maintenance_margin = notional * position.maintenance_margin_rate
    unrealized_pnl = calculate_unrealized_pnl(
        position.side,
        position.entry_price,
        current_price,
        position.quantity,
    )
    if position.margin_mode is MarginMode.ISOLATED:
        return position.initial_margin + unrealized_pnl <= maintenance_margin
    return equity + unrealized_pnl <= maintenance_margin


@dataclass(frozen=True)
class MaintenanceTier:
    """One BingX USD-M maintenance-margin bracket.

    ``max_notional`` is inclusive.  The last tier may use ``math.inf``.
    Rates are decimal fractions: 0.004 means 0.4%.
    """

    max_notional: float
    maintenance_margin_rate: float
    maintenance_amount: float = 0.0
    max_leverage: int | None = None

    def __post_init__(self) -> None:
        if self.max_notional <= 0:
            raise MarginModelError("max_notional must be positive")
        if not 0 <= self.maintenance_margin_rate < 1:
            raise MarginModelError("maintenance_margin_rate must be in [0, 1)")
        if self.maintenance_amount < 0:
            raise MarginModelError("maintenance_amount cannot be negative")
        if self.max_leverage is not None and not 1 <= self.max_leverage <= 500:
            raise MarginModelError("tier max_leverage must be between 1 and 500")


@dataclass(frozen=True)
class BingXMarketRiskRules:
    symbol: str
    max_leverage: int
    taker_fee_rate: float
    maintenance_tiers: tuple[MaintenanceTier, ...]

    def __post_init__(self) -> None:
        if not self.symbol:
            raise MarginModelError("symbol is required")
        if self.max_leverage < 1 or self.max_leverage > 500:
            raise MarginModelError("max_leverage must be between 1 and 500")
        if not 0 <= self.taker_fee_rate < 1:
            raise MarginModelError("taker_fee_rate must be in [0, 1)")
        if not self.maintenance_tiers:
            raise MarginModelError("at least one maintenance tier is required")
        limits = [tier.max_notional for tier in self.maintenance_tiers]
        if limits != sorted(limits) or len(set(limits)) != len(limits):
            raise MarginModelError("maintenance tiers must have unique ascending limits")

    def tier_for(self, notional: float) -> MaintenanceTier:
        if not math.isfinite(notional) or notional <= 0:
            raise MarginModelError("notional must be finite and positive")
        for tier in self.maintenance_tiers:
            if notional <= tier.max_notional:
                return tier
        raise MarginModelError("no maintenance tier covers this notional")


@dataclass(frozen=True)
class IsolatedPosition:
    side: PositionSide
    entry_price: float
    quantity: float
    leverage: int
    added_margin: float = 0.0
    funding_paid: float = 0.0
    other_margin_costs: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.entry_price) or self.entry_price <= 0:
            raise MarginModelError("entry_price must be finite and positive")
        if not math.isfinite(self.quantity) or self.quantity <= 0:
            raise MarginModelError("quantity must be finite and positive")
        if self.leverage < 1 or self.leverage > 500:
            raise MarginModelError("leverage must be between 1 and 500")
        for name, value in (
            ("added_margin", self.added_margin),
            ("funding_paid", self.funding_paid),
            ("other_margin_costs", self.other_margin_costs),
        ):
            if not math.isfinite(value) or value < 0:
                raise MarginModelError(f"{name} must be finite and non-negative")

    @property
    def entry_notional(self) -> float:
        return self.entry_price * self.quantity

    @property
    def position_margin(self) -> float:
        return self.entry_notional / self.leverage + self.added_margin


@dataclass(frozen=True)
class PriceRisk:
    price: float
    notional: float
    unrealized_pnl: float
    remaining_margin: float
    maintenance_margin: float
    closing_fee: float
    required_margin: float
    risk_ratio: float
    threshold_reached: bool


@dataclass(frozen=True)
class LiquidationAssessment:
    mark: PriceRisk
    last: PriceRisk
    executable_at_entry: bool
    liquidated: bool
    reason: str | None


class BingXIsolatedMarginModel:
    """Conservative USD-M isolated-margin model for backtests.

    BingX defines forced-liquidation risk using maintenance margin plus the
    estimated taker fee required to close.  Its dual-price mechanism requires
    both mark and last price to reach the threshold.  This class deliberately
    does not approximate missing market brackets or fee rates.
    """

    def __init__(self, rules: BingXMarketRiskRules) -> None:
        self.rules = rules

    def _at_price(self, position: IsolatedPosition, price: float) -> PriceRisk:
        if not math.isfinite(price) or price <= 0:
            raise MarginModelError("price must be finite and positive")
        notional = position.quantity * price
        tier = self.rules.tier_for(notional)
        unrealized = (
            position.side.direction
            * position.quantity
            * (price - position.entry_price)
        )
        remaining = (
            position.position_margin
            + unrealized
            - position.funding_paid
            - position.other_margin_costs
        )
        maintenance = max(
            0.0,
            notional * tier.maintenance_margin_rate - tier.maintenance_amount,
        )
        closing_fee = notional * self.rules.taker_fee_rate
        required = maintenance + closing_fee
        risk_ratio = math.inf if remaining <= 0 else required / remaining
        return PriceRisk(
            price=price,
            notional=notional,
            unrealized_pnl=unrealized,
            remaining_margin=remaining,
            maintenance_margin=maintenance,
            closing_fee=closing_fee,
            required_margin=required,
            risk_ratio=risk_ratio,
            threshold_reached=remaining <= required,
        )

    def assess(
        self,
        position: IsolatedPosition,
        *,
        mark_price: float,
        last_price: float,
    ) -> LiquidationAssessment:
        if position.leverage > self.rules.max_leverage:
            raise MarginModelError(
                f"{position.leverage}x exceeds verified {self.rules.symbol} maximum "
                f"of {self.rules.max_leverage}x"
            )
        # Entry feasibility is evaluated before later funding settlements or
        # other accrued holding costs.  Those costs still reduce current margin
        # below and may legitimately trigger liquidation after the position was
        # executable at opening.
        entry_position = IsolatedPosition(
            side=position.side,
            entry_price=position.entry_price,
            quantity=position.quantity,
            leverage=position.leverage,
            added_margin=position.added_margin,
        )
        entry = self._at_price(entry_position, position.entry_price)
        entry_tier = self.rules.tier_for(position.entry_notional)
        tier_leverage_ok = (
            entry_tier.max_leverage is None
            or position.leverage <= entry_tier.max_leverage
        )
        executable = not entry.threshold_reached and tier_leverage_ok
        mark = self._at_price(position, mark_price)
        last = self._at_price(position, last_price)
        liquidated = executable and mark.threshold_reached and last.threshold_reached
        reason = None
        if not tier_leverage_ok:
            reason = "TIER_LEVERAGE_EXCEEDED"
        elif not executable:
            reason = "INSUFFICIENT_INITIAL_MARGIN"
        elif liquidated:
            reason = "DUAL_PRICE_LIQUIDATION"
        return LiquidationAssessment(mark, last, executable, liquidated, reason)

    def executable_leverages(
        self,
        leverage_tiers: Iterable[int],
        *,
        entry_price: float,
        quantity: float,
        side: PositionSide = PositionSide.LONG,
    ) -> tuple[int, ...]:
        """Filter a campaign staircase without silently relaxing market rules."""

        result: list[int] = []
        for leverage in sorted(set(int(value) for value in leverage_tiers)):
            if leverage < 1 or leverage > self.rules.max_leverage:
                continue
            position = IsolatedPosition(side, entry_price, quantity, leverage)
            if self.assess(
                position,
                mark_price=entry_price,
                last_price=entry_price,
            ).executable_at_entry:
                result.append(leverage)
        return tuple(result)


def build_risk_rules(
    *,
    symbol: str,
    max_leverage: int,
    taker_fee_rate: float,
    maintenance_tiers: Sequence[MaintenanceTier],
) -> BingXMarketRiskRules:
    """Explicit constructor used by adapters after fetching verified BingX rules."""

    return BingXMarketRiskRules(
        symbol=symbol,
        max_leverage=max_leverage,
        taker_fee_rate=taker_fee_rate,
        maintenance_tiers=tuple(maintenance_tiers),
    )


# ---------------------------------------------------------------------------
# CME GLOBEX & MICRO FUTURES SPECIFICATIONS (CANONICAL PROP FIRM MATRIX)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CMEContractSpec:
    symbol: str
    name: str
    is_micro: bool
    point_value_usd: float
    tick_size: float
    tick_value_usd: float
    exchange_fee_per_side_usd: float
    parent_mini_symbol: str | None = None


CME_CONTRACT_SPECS: dict[str, CMEContractSpec] = {
    # Micro E-mini Index Futures
    "MNQ": CMEContractSpec("MNQ", "Micro E-mini Nasdaq 100", True, 2.0, 0.25, 0.50, 0.62, "NQ"),
    "MES": CMEContractSpec("MES", "Micro E-mini S&P 500", True, 5.0, 0.25, 1.25, 0.62, "ES"),
    "MYM": CMEContractSpec("MYM", "Micro E-mini Dow Jones", True, 0.50, 1.0, 0.50, 0.62, "YM"),
    "M2K": CMEContractSpec("M2K", "Micro E-mini Russell 2000", True, 5.0, 0.10, 0.50, 0.62, "RTY"),
    # Micro Commodities
    "MGC": CMEContractSpec("MGC", "Micro Gold", True, 10.0, 0.10, 1.00, 0.85, "GC"),
    "MCL": CMEContractSpec("MCL", "Micro Crude Oil WTI", True, 100.0, 0.01, 1.00, 0.85, "CL"),
    "MSI": CMEContractSpec("MSI", "Micro Silver", True, 1000.0, 0.005, 5.00, 1.25, "SI"),
    # Standard Minis (Reference)
    "NQ": CMEContractSpec("NQ", "E-mini Nasdaq 100", False, 20.0, 0.25, 5.00, 2.45),
    "ES": CMEContractSpec("ES", "E-mini S&P 500", False, 50.0, 0.25, 12.50, 2.45),
    "YM": CMEContractSpec("YM", "E-mini Dow Jones", False, 5.0, 1.0, 5.00, 2.45),
    "RTY": CMEContractSpec("RTY", "E-mini Russell 2000", False, 50.0, 0.10, 5.00, 2.45),
    "GC": CMEContractSpec("GC", "Gold Futures", False, 100.0, 0.10, 10.00, 2.45),
    "CL": CMEContractSpec("CL", "Crude Oil WTI Futures", False, 1000.0, 0.01, 10.00, 2.45),
    "SI": CMEContractSpec("SI", "Silver Futures", False, 5000.0, 0.005, 25.00, 2.45),
}


def calculate_cme_position_sizing(
    symbol: str,
    stop_loss_points: float,
    max_risk_usd: float = 250.0,
    prefer_micros: bool = True,
) -> tuple[str, int, float]:
    """Calculate exact contract count and risk for Prop Firm evaluation.
    
    Returns:
        tuple[resolved_symbol, contract_count, actual_risk_usd]
    """
    sym_clean = symbol.upper().replace("-", "").replace("/", "").replace("=F", "")
    
    # Map mini to micro if preferred
    target_sym = sym_clean
    if prefer_micros:
        micro_map = {"NQ": "MNQ", "ES": "MES", "YM": "MYM", "RTY": "M2K", "GC": "MGC", "CL": "MCL", "SI": "MSI"}
        target_sym = micro_map.get(sym_clean, sym_clean)
        
    spec = CME_CONTRACT_SPECS.get(target_sym)
    if not spec:
        # Fallback to standard 1 contract
        return (target_sym, 1, stop_loss_points * 20.0)
        
    risk_per_contract = max(1.0, stop_loss_points * spec.point_value_usd)
    contracts = max(1, int(math.floor(max_risk_usd / risk_per_contract)))
    actual_risk = round(contracts * risk_per_contract, 2)
    
    return (target_sym, contracts, actual_risk)

