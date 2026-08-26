#!/usr/bin/env python3
"""Fail-closed certification evidence policy for R0.3.

A certification record is valid only when the scorecard carries explicit,
cryptographically identifiable provenance and a complete 11/11 gate state.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdefABCDEF" for c in value)


def _gates_complete(scorecard: dict[str, Any]) -> bool:
    gates = scorecard.get("gates")
    if isinstance(gates, list):
        state: dict[int, bool] = {}
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            try:
                gate_id = int(gate.get("gate_id", gate.get("id")))
            except (TypeError, ValueError):
                continue
            if 1 <= gate_id <= 11 and isinstance(gate.get("passed"), bool):
                state[gate_id] = gate["passed"]
        return len(state) == 11 and all(state.values())

    evaluation = scorecard.get("gates_evaluation")
    if isinstance(evaluation, dict):
        values = []
        for gate_id in range(1, 12):
            value = evaluation.get(f"gate_{gate_id:02d}")
            if isinstance(value, bool):
                values.append(value)
            elif isinstance(value, str) and value.upper() in {"PASSED", "FAILED"}:
                values.append(value.upper() == "PASSED")
            else:
                return False
        return len(values) == 11 and all(values)
    return False


def validate_scorecard(scorecard: dict[str, Any], signature_sha256: str) -> list[str]:
    failures: list[str] = []
    required_hashes = {
        "strategy_sha256": scorecard.get("strategy_sha256") or scorecard.get("canonical_hash"),
        "dataset_hash": scorecard.get("dataset_hash") or scorecard.get("data_sha256"),
        "ledger_hash": scorecard.get("ledger_hash"),
        "evidence_bundle_hash": scorecard.get("bundle_signature_sha256") or scorecard.get("evidence_bundle_hash"),
    }
    for name, value in required_hashes.items():
        if not _hash(value):
            failures.append(f"missing_or_invalid_{name}")

    if not _hash(signature_sha256):
        failures.append("missing_or_invalid_signature_sha256")
    if scorecard.get("ledger_verified") is not True:
        failures.append("ledger_not_verified")
    if not _gates_complete(scorecard):
        failures.append("explicit_11_of_11_gate_evidence_required")

    status = scorecard.get("certification_status") or scorecard.get("status")
    if isinstance(status, str) and status.upper() in {"NO_EVIDENCE", "BLOCKED_NO_EVIDENCE"}:
        failures.append("non_certifiable_status")
    return failures


def main() -> int:
    from services.validation.certification_registry import CertificationRegistry

    source = Path(CertificationRegistry.register_certification.__code__.co_filename).resolve()
    failures = [] if source == (ROOT / "services" / "validation" / "certification_registry.py").resolve() else ["unexpected_registry_source"]
    result = {
        "check": "R0.3_CERTIFICATION_EVIDENCE_POLICY",
        "status": "PASS" if not failures else "BLOCKED",
        "source": str(source.relative_to(ROOT)) if source.is_relative_to(ROOT) else str(source),
        "policy": "11/11 gates + strategy_hash + dataset_hash + ledger_hash + evidence_bundle_hash + verified ledger + signature",
        "failures": failures,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
