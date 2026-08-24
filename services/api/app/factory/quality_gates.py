"""Quality Gates for strategy candidates in Ultrarentable V2.

Central, auditable thresholds that decide whether a backtested strategy is
allowed to be *ranked*, *validated* and *shown as rentable*. Every layer of the
search engine (evolution fitness, evidence judge, adversarial validation, SQX
ingestion/ranking) consults these constants and helpers so the exact same
"what is acceptable" policy applies everywhere.

The project doctrine distinguishes TWO search modes that do NOT share the same
acceptance logic:

  * ULTRA (hiperescalado 500x / kamikaze): we seek extraordinary terminal multiples
    via positive asymmetry (fat tails), isolated 1R bullets and Ratchet Vault harvesting.
    Drawdown tolerance is up to 75.0% realized (closed equity) and up to 80.0% floating (intrabar).
    The hard stop is real ruin: drawdown >= 100% (account liquidated / equity <= 0).
  * FONDEO (CME Futures / prop firms): we seek strategies that pass prop-firm / funding
    evaluations (25k to 300k accounts in Topstep, Apex, MFFU, etc.).
    Here strict capital preservation is mandatory: Max Realized Drawdown <= 4.50%,
    Daily Loss Limit <= 2.0%, DSR >= 2.0, WFE >= 0.60, and zero margin calls.
"""

from __future__ import annotations

from typing import Mapping


# Hard ruin gate. A drawdown of 100% or more means the equity curve reached zero
# (or below) — the account is gone no matter where it ended. Nothing with this
# signature may ever be validated, ranked or surfaced.
RIVETING_DRAWDOWN_PCT: float = 100.0

# Max realized drawdown threshold for FONDEO mode (prop firms allow 4.0% - 4.5%)
MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO: float = 4.50

# Max realized drawdown threshold for ULTRA mode (allows up to 75.0% realized on closed balance)
MAX_ACCEPTABLE_DRAWDOWN_PCT_ULTRA: float = 75.0

# Backward compatibility alias (defaults to Fondeo strict threshold)
MAX_ACCEPTABLE_DRAWDOWN_PCT: float = 4.50

# Minimum net-return-to-max-drawdown ratio required for a candidate to be
# treated as genuinely rentable in FONDEO mode. In ULTRA mode this gate is
# replaced by Payoff Ratio and Tail Gain Ratio.
MIN_CALMAR_RATIO: float = 0.5

# Absolute minimum net return (%) for something to be surfaced as rentable, so
# a barely-positive-by-noise result is not marketed as a winner.
MIN_RENTABLE_NET_RETURN_PCT: float = 5.0

# Absolute minimum profit factor for rentable ranking.
MIN_RENTABLE_PROFIT_FACTOR: float = 1.30


def is_ruinous(drawdown_pct: float) -> bool:
    """True if the (non-negative) drawdown guarantees account ruin (DD >= 100%)."""
    if drawdown_pct is None:
        return False
    try:
        value = float(drawdown_pct)
    except (TypeError, ValueError):
        return False
    if value != value:  # NaN
        return False
    return value >= RIVETING_DRAWDOWN_PCT


def drawdown_acceptable(drawdown_pct: float | None) -> bool:
    """True if a candidate's drawdown does not indicate ruin."""
    if drawdown_pct is None:
        return False
    try:
        value = float(drawdown_pct)
    except (TypeError, ValueError):
        return False
    if value != value:  # NaN
        return False
    return value < RIVETING_DRAWDOWN_PCT


def drawdown_sustainable(drawdown_pct: float | None, mode: str = "ultra") -> bool:
    """True if drawdown is within the sustainable band for the specific mode.

    In ULTRA mode: Realized DD < 100.0% (kamikaze / convexity search allows high drawdown if not ruined).
    In FONDEO mode: Realized DD <= MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO (4.50%).
    """
    if not drawdown_acceptable(drawdown_pct):
        return False
    dd = float(drawdown_pct)
    if str(mode).lower() == "fondeo":
        return dd <= MAX_ACCEPTABLE_DRAWDOWN_PCT_FONDEO
    return dd < RIVETING_DRAWDOWN_PCT


def calmar_ratio(net_return_pct: float, drawdown_pct: float | None) -> float:
    """Net-return-to-max-drawdown ratio. Drawdown of ~0 gives a large (good) value."""
    try:
        dd = float(drawdown_pct) if drawdown_pct is not None else 0.0
    except (TypeError, ValueError):
        dd = 0.0
    if dd != dd:  # NaN
        dd = 0.0
    if dd <= 0.0:
        return float("inf")
    try:
        ret = float(net_return_pct or 0.0)
    except (TypeError, ValueError):
        ret = 0.0
    return ret / dd


def rentable(
    net_return_pct: float,
    profit_factor: float,
    drawdown_pct: float | None,
    mode: str = "ultra",
) -> bool:
    """Full rentable gate: sustainable drawdown, positive Calmar, minimum edge.

    In ULTRA mode: Realized DD < 100.0%, net return >= 5% and PF >= 1.30.
    In FONDEO mode: Realized DD <= 4.50%, Calmar >= 0.5, net return >= 5% and PF >= 1.30.
    """
    if is_ruinous(drawdown_pct):
        return False
    if net_return_pct < MIN_RENTABLE_NET_RETURN_PCT:
        return False
    if profit_factor < MIN_RENTABLE_PROFIT_FACTOR:
        return False
    if not drawdown_sustainable(drawdown_pct, mode=mode):
        return False
    if str(mode).lower() == "fondeo":
        if calmar_ratio(net_return_pct, drawdown_pct) < MIN_CALMAR_RATIO:
            return False
    return True


def describe(metrics: Mapping[str, object], mode: str = "ultra") -> str:
    """Human-readable policy summary (for UI/debug)."""
    return (
        f"dd={metrics.get('maxDrawdownPct')} ruin={is_ruinous(float(metrics.get('maxDrawdownPct') or 0))} "
        f"calmar={calmar_ratio(float(metrics.get('netReturnPct') or 0), float(metrics.get('maxDrawdownPct') or 0)):.2f} "
        f"rentable={rentable(float(metrics.get('netReturnPct') or 0), float(metrics.get('profitFactor') or 0), float(metrics.get('maxDrawdownPct') or 0), mode=mode)}"
    )


def drawdown_penalty_factor(drawdown_pct: float | None, mode: str = "ultra") -> float:
    """Multiplier (0..1) applied to fitness to discourage destructive drawdown."""
    if drawdown_pct is None:
        return 1.0
    if not drawdown_acceptable(drawdown_pct):
        return 0.0
    dd = float(drawdown_pct)
    if str(mode).lower() == "ultra":
        return 1.0 if dd < RIVETING_DRAWDOWN_PCT else 0.0
    else:
        if dd <= 20.0:
            return 1.0
        if dd >= RIVETING_DRAWDOWN_PCT:
            return 0.0
        span = RIVETING_DRAWDOWN_PCT - 20.0
        frac = (RIVETING_DRAWDOWN_PCT - dd) / span if span > 0 else 0.0
        return max(0.0, min(1.0, frac))


def risk_adjusted_fitness(net_return_pct: float, drawdown_pct: float | None, mode: str = "ultra") -> float:
    """Fitness term that rewards return and scales with drawdown tolerance."""
    if not drawdown_acceptable(drawdown_pct):
        return 0.0
    if str(mode).lower() == "ultra":
        return 1.0
    calmar = calmar_ratio(net_return_pct, drawdown_pct)
    if calmar == float("inf"):
        return 1.0
    return max(0.0, min(1.0, calmar / 1.0))
