"""Deterministic, family-stratified trial selection for Phase 2.

The planner is deliberately deterministic: the dataset hash determines the
starting offset, while round-robin quotas guarantee representation across
strategy families. It never uses wall-clock time or random number generation.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple

PLANNER_VERSION = "phase2-stratified-v1"


def _family_key(params: Dict[str, Any]) -> str:
    if params.get("archetype"):
        return f"archetype:{str(params['archetype']).upper()}"
    risk = params.get("risk_per_trade_pct", "na")
    target = params.get("target_profit_ticks", "na")
    stop = params.get("stop_loss_ticks", "na")
    return f"risk:{risk}|target:{target}|stop:{stop}"


def _stable_key(dataset_hash: str, family: str, index: int) -> bytes:
    return hashlib.sha256(f"{dataset_hash}|{PLANNER_VERSION}|{family}|{index}".encode()).digest()


def budget_space(space: Sequence[Dict[str, Any]], limit: int, dataset_hash: str) -> List[Dict[str, Any]]:
    """Select <= limit trials while preserving deterministic family coverage."""
    if limit <= 0:
        return []
    if len(space) <= limit:
        return list(space)

    groups: Dict[str, List[Tuple[int, Dict[str, Any]]]] = defaultdict(list)
    for index, params in enumerate(space):
        groups[_family_key(params)].append((index, params))

    # Deterministically reshuffle positions inside each family using a hash
    # derived only from immutable dataset identity.
    families: Dict[str, List[Tuple[int, Dict[str, Any]]]] = {}
    for family, items in groups.items():
        families[family] = sorted(
            items,
            key=lambda item: _stable_key(dataset_hash, family, item[0]),
        )

    family_names = sorted(families)
    start = int(hashlib.sha256(dataset_hash.encode()).hexdigest()[:12], 16) % len(family_names)
    ordered_families = family_names[start:] + family_names[:start]

    selected: List[Dict[str, Any]] = []
    cursors = {family: 0 for family in ordered_families}
    while len(selected) < limit:
        progressed = False
        for family in ordered_families:
            cursor = cursors[family]
            items = families[family]
            if cursor >= len(items):
                continue
            selected.append(items[cursor][1])
            cursors[family] += 1
            progressed = True
            if len(selected) >= limit:
                break
        if not progressed:
            break

    return selected
