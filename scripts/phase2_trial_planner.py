"""Deterministic, signal×exit-family stratified trial selection for Phase 2."""
from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from typing import Any, Dict, List, Sequence, Tuple

PLANNER_VERSION = "phase2-stratified-v3"


def _family_key(params: Dict[str, Any]) -> str:
    signal = str(params.get("archetype") or params.get("family") or "UNKNOWN").upper()
    exit_family = str(params.get("exit_family") or "DEFAULT").upper()
    return f"signal:{signal}|exit:{exit_family}"


def _canonical_key(params: Dict[str, Any]) -> str:
    return json.dumps(params, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _stable_key(dataset_hash: str, family: str, index: int, canonical_key: str) -> bytes:
    material = f"{dataset_hash}|{PLANNER_VERSION}|{family}|{index}|{canonical_key}"
    return hashlib.sha256(material.encode("utf-8")).digest()


def budget_space(space: Sequence[Dict[str, Any]], limit: int, dataset_hash: str) -> List[Dict[str, Any]]:
    """Select <= limit distinct trials while preserving deterministic signal×exit coverage."""
    if limit <= 0:
        return []

    unique: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for params in space:
        key = _canonical_key(params)
        if key in seen:
            continue
        seen.add(key)
        unique.append(params)

    if len(unique) <= limit:
        return list(unique)

    groups: Dict[str, List[Tuple[int, Dict[str, Any]]]] = defaultdict(list)
    for index, params in enumerate(unique):
        groups[_family_key(params)].append((index, params))

    families = {
        family: sorted(
            items,
            key=lambda item: _stable_key(
                dataset_hash, family, item[0], _canonical_key(item[1])
            ),
        )
        for family, items in groups.items()
    }
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
