from __future__ import annotations

import hashlib

import pytest

from services.validation.certification_registry import CertificationRegistry


def _hash(seed: str) -> str:
    return hashlib.sha256(seed.encode()).hexdigest()


def _valid_scorecard() -> dict:
    return {
        "strategy_sha256": _hash("strategy"),
        "dataset_hash": _hash("dataset"),
        "ledger_hash": _hash("ledger"),
        "evidence_bundle_hash": _hash("bundle"),
        "ledger_verified": True,
        "gates": [{"gate_id": i, "passed": True} for i in range(1, 12)],
    }


def test_certification_registry_accepts_complete_evidence() -> None:
    record = CertificationRegistry().register_certification(
        strategy_id="TEST",
        engine_version="test-engine",
        scorecard=_valid_scorecard(),
        signature_sha256=_hash("signature"),
    )
    assert record["evidence_policy_status"] == "PASS"


def test_certification_registry_blocks_missing_provenance() -> None:
    scorecard = _valid_scorecard()
    scorecard.pop("dataset_hash")
    with pytest.raises(ValueError, match="CERTIFICATION_BLOCKED_NO_EVIDENCE"):
        CertificationRegistry().register_certification(
            strategy_id="TEST",
            engine_version="test-engine",
            scorecard=scorecard,
            signature_sha256=_hash("signature"),
        )


def test_certification_registry_blocks_incomplete_gates() -> None:
    scorecard = _valid_scorecard()
    scorecard["gates"][-1]["passed"] = False
    with pytest.raises(ValueError, match="explicit_11_of_11_gate_evidence_required"):
        CertificationRegistry().register_certification(
            strategy_id="TEST",
            engine_version="test-engine",
            scorecard=scorecard,
            signature_sha256=_hash("signature"),
        )
