"""Closed-loop research director for SQX -> ULTRARENTABLE.

The director is the control plane for intelligent discovery. It consumes only
historical research evidence and emits deterministic next-campaign instructions
for SQX and the local canonical validator. It deliberately does not fabricate
strategy performance, does not consume blind OOS during discovery, and does not
change certification gates.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Dict, Iterable, List

from services.discovery.adaptive_hypothesis_engine import AdaptiveHypothesisEngine, HypothesisPlan


@dataclass(frozen=True)
class SQXCampaign:
    campaign_id: str
    signal_family: str
    exit_family: str
    search_intensity: int
    rationale: str
    dataset_scope: str


class ResearchDirector:
    """Turns evidence history into the next deterministic SQX search agenda."""

    def __init__(self, version: str = "research-director-v1") -> None:
        self.version = version
        self.adaptive = AdaptiveHypothesisEngine(planner_version=f"{version}|adaptive")

    def next_campaigns(
        self,
        dataset_sha256: str,
        history: Iterable[Dict[str, Any]],
        campaign_budget: int = 12,
        trials_per_campaign: int = 10000,
    ) -> List[SQXCampaign]:
        plans: List[HypothesisPlan] = self.adaptive.plan(
            dataset_sha256=dataset_sha256,
            history=history,
            budget=max(1, int(campaign_budget)),
        )
        result: List[SQXCampaign] = []
        for plan in plans:
            material = f"{self.version}|{dataset_sha256}|{plan.plan_id}|{trials_per_campaign}"
            campaign_id = sha256(material.encode()).hexdigest()[:24]
            result.append(
                SQXCampaign(
                    campaign_id=campaign_id,
                    signal_family=plan.signal_family,
                    exit_family=plan.exit_family,
                    search_intensity=max(1, int(trials_per_campaign)),
                    rationale=plan.rationale,
                    dataset_scope="REAL_DATASET_ONLY",
                )
            )
        return result

    @staticmethod
    def validate_campaigns(campaigns: Iterable[SQXCampaign]) -> None:
        seen: set[str] = set()
        for campaign in campaigns:
            if campaign.dataset_scope != "REAL_DATASET_ONLY":
                raise ValueError("NON_REAL_DATASET_SCOPE")
            if campaign.search_intensity <= 0:
                raise ValueError("INVALID_SEARCH_INTENSITY")
            if campaign.campaign_id in seen:
                raise ValueError("DUPLICATE_CAMPAIGN_ID")
            seen.add(campaign.campaign_id)
