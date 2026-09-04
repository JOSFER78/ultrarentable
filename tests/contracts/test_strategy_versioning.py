from contracts.certification_snapshot import CertificationSnapshot
from contracts.strategy_version import CertificationState, StrategyVersion


def _h(char: str) -> str:
    return char * 64


def test_strategy_version_is_immutable_and_lineage_is_stable():
    version = StrategyVersion(
        strategy_id="STR-1",
        version="1.0.0",
        strategy_hash=_h("a"),
        engine_version="5.3.0",
        compiler_version="1.0.0",
        dataset_policy_version="1.0.0",
        execution_policy_version="1.0.0",
        risk_policy_version="1.0.0",
        gate_policy_version="1.0.0",
        created_by="test",
        change_reason="initial",
    )
    before = version.lineage_hash()
    assert before == version.lineage_hash()
    assert version.certification_state == CertificationState.UNTESTED
    try:
        version.version = "2.0.0"
        raise AssertionError("StrategyVersion must be immutable")
    except (TypeError, ValueError):
        pass


def test_stale_certification_is_not_current():
    version = StrategyVersion(
        strategy_id="STR-1",
        version="1.0.0",
        strategy_hash=_h("a"),
        engine_version="5.2.0",
        compiler_version="1.0.0",
        dataset_policy_version="1.0.0",
        execution_policy_version="1.0.0",
        risk_policy_version="1.0.0",
        gate_policy_version="10.0.0",
        certification_state=CertificationState.STALE,
        created_by="test",
        change_reason="engine changed",
    )
    assert not version.is_currently_certified()
    assert version.is_stale()


def test_certification_snapshot_requires_exact_current_versions():
    snapshot = CertificationSnapshot(
        certification_id="CERT-1",
        strategy_id="STR-1",
        strategy_version="1.0.0",
        strategy_hash=_h("a"),
        dataset_hash=_h("b"),
        execution_hash=_h("c"),
        risk_policy_hash=_h("d"),
        engine_version="5.3.0",
        compiler_version="1.0.0",
        gate_policy_version="11.0.0",
        evidence_bundle_hash=_h("e"),
        ledger_hash=_h("f"),
        verdict="CERTIFIED_CURRENT",
        gate_verdicts={"G1": "PASS", "G11": "PASS"},
    )
    assert snapshot.is_current(engine_version="5.3.0", compiler_version="1.0.0", gate_policy_version="11.0.0")
    assert not snapshot.is_current(engine_version="5.4.0", compiler_version="1.0.0", gate_policy_version="11.0.0")
