"""Quality Gates for strategy candidates.

Central, auditable thresholds that decide whether a backtested strategy is
allowed to be *ranked*, *validated* and *shown as rentable*. Every layer of the
search engine (evolution fitness, evidence judge, adversarial validation, SQX
ingestion/ranking) consults these constants and helpers so the exact same
"what is acceptable" policy applies everywhere.

The project doctrine distinguishes TWO search modes that do NOT share the same
acceptance logic:

  * ULTRA (kamikaze): we seek extraordinary terminal multiples even if the
    strategy is extremely aggressive. The ONLY hard stop is real ruin:
    drawdown >= 100% (account liquidated / equity <= 0). High but non-ruinous
    drawdown is tolerated; Calmar and sustainable-DD gates do NOT apply.
  * FONDEO (conservative): we seek strategies that could pass prop-firm / funding
    evaluations. Here low drawdown and a healthy return-to-drawdown profile
    matter, so the sustainable-DD and Calmar gates DO apply in addition to ruin.

Mode selection is explicit and backward compatible: functions that decide
rankability / rentability accept an optional `mode` parameter defaulting to
"ultra" so existing callers keep the same behaviour unless they opt into
"fondeo".
"""

from __future__ import annotations

from typing import Mapping


# Hard ruin gate. A drawdown of 100% or more means the equity curve reached zero
# (or below) — the account is gone no matter where it ended. Nothing with this
# signature may ever be validated, ranked or surfaced.
RIVETING_DRAWDOWN_PCT: float = 100.0

# Above this drawdown the candidate is technically solvent but the risk profile
# is deemed too destructive for live capital in FONDEO mode. In ULTRA mode this
# gate is ignored (kamikaze search tolerates aggressive-but-solvent drawdown).
MAX_ACCEPTABLE_DRAWDOWN_PCT: float = 85.0

# Minimum net-return-to-max-drawdown ratio required for a candidate to be
# treated as genuinely rentable in FONDEO mode. net return 20% with drawdown
# 260% has Calmar ~0.08 — far below this gate. In ULTRA mode this gate is
# ignored.
MIN_CALMAR_RATIO: float = 0.5

# Absolute minimum net return (%) for something to be surfaced as rentable, so
# a barely-positive-by-noise result is not marketed as a winner.
MIN_RENTABLE_NET_RETURN_PCT: float = 5.0

# Absolute minimum profit factor for rentable ranking. Below this there is no
# real asymmetric edge (gross wins barely exceed gross losses).
MIN_RENTABLE_PROFIT_FACTOR: float = 1.5


def is_ruinous(drawdown_pct: float) -> bool:
    """True if the (non-negative) drawdown guarantees account ruin.

    Handles None / NaN defensively; an unknown drawdown is treated conservatively
    as NOT ruinous so we never silently blank a candidate, but callers that need
    strictness should use drawdown_acceptable() which defaults to False.
    """
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
    """True if a candidate's drawdown does not indicate ruin.

    Conservative default: if the drawdown is unknown we refuse to bless it.
    """
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
    """True if drawdown is within the sustainable band (below the hard cap).

    In ULTRA mode any non-ruinous drawdown is accepted (kamikaze search).
    In FONDEO mode the MAX_ACCEPTABLE_DRAWDOWN_PCT cap is enforced.
    """
    if not drawdown_acceptable(drawdown_pct):
        return False
    if str(mode).lower() == "fondeo":
        return float(drawdown_pct) <= MAX_ACCEPTABLE_DRAWDOWN_PCT
    return True


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

    In ULTRA mode only minimum net return and minimum profit factor are enforced;
    drawdown sustainability and Calmar are intentionally ignored because the
    search explicitly tolerates aggressive drawdown to maximise terminal multiple.

    In FONDEO mode all gates apply, including real ruin (always rejected).

    NOTE: Real ruin (drawdown >= 100%) is rejected in BOTH modes, even if the
    other gates would otherwise allow the candidate.
    """
    if is_ruinous(drawdown_pct):
        return False
    if net_return_pct < MIN_RENTABLE_NET_RETURN_PCT:
        return False
    if profit_factor < MIN_RENTABLE_PROFIT_FACTOR:
        return False
    if str(mode).lower() == "fondeo":
        if not drawdown_sustainable(drawdown_pct, mode=mode):
            return False
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
    """Multiplier (0..1) applied to fitness to discourage destructive drawdown.

    Unknown drawdown is treated as neutral (1.0) so search callers that do not
    report max drawdown are not artificially zeroed out. Drawdown at/above the
    ruin gate still yields 0.0. Drawdown at/below the sustainable cap yields
    1.0. Between them the penalty grows linearly.

    In ULTRA mode non-ruinous drawdown does NOT penalise fitness: the kamikaze
    search deliberately tolerates aggressive drawdown. Only real ruin zeroes the
    candidate out.
    """
    if drawdown_pct is None:
        return 1.0
    if not drawdown_acceptable(drawdown_pct):
        return 0.0
    if str(mode).lower() == "ultra":
        return 1.0
    dd = float(drawdown_pct)
    if dd <= MAX_ACCEPTABLE_DRAWDOWN_PCT:
        return 1.0
    span = RIVETING_DRAWDOWN_PCT - MAX_ACCEPTABLE_DRAWDOWN_PCT
    frac = (RIVETING_DRAWDOWN_PCT - dd) / span if span > 0 else 0.0
    return max(0.0, min(1.0, frac))


def risk_adjusted_fitness(net_return_pct: float, drawdown_pct: float | None, mode: str = "ultra") -> float:
    """Fitness term that rewards return but multiplies down by drawdown risk.

    Uses the Calmar ratio clamped into [0,1] to keep it comparable with the
    existing evidence/validation terms. Zero when ruinous.

    In ULTRA mode non-ruinous drawdown does NOT reduce this term: the search
    is allowed to surface aggressive-but-solvent candidates.
    """
    if not drawdown_acceptable(drawdown_pct):
        return 0.0
    if str(mode).lower() == "ultra":
        return 1.0
    dd = abs(float(drawdown_pct))
    calmar = calmar_ratio(net_return_pct, drawdown_pct)
    if calmar == float("inf"):
        return 1.0
    # Clamp Calmar into [0,1]; 1.0 means return >= drawdown (good edge).
    return max(0.0, min(1.0, calmar / 1.0))
