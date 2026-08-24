from contracts.meta_strategy import CompensationMethod, MetaConstituent, MetaStrategyDefinition, MetaStrategyPolicy


def _h(char: str) -> str:
    return char * 64


def test_meta_strategy_requires_traceable_constituents_and_joint_evidence():
    constituents = [
        MetaConstituent(
            strategy_id="STR-A",
            strategy_version="1.0.0",
            strategy_hash=_h("a"),
            route="ULTRA",
            symbol="NQ",
            timeframe="5m",
            allocation_cap_pct=50.0,
            risk_budget_pct=10.0,
        ),
        MetaConstituent(
            strategy_id="STR-B",
            strategy_version="2.0.0",
            strategy_hash=_h("b"),
            route="ULTRA",
            symbol="GC",
            timeframe="15m",
            allocation_cap_pct=50.0,
            risk_budget_pct=10.0,
        ),
    ]
    meta = MetaStrategyDefinition(
        meta_strategy_id="META-1",
        version="1.0.0",
        route="ULTRA",
        constituents=constituents,
        policy=MetaStrategyPolicy(
            compensation_methods=[CompensationMethod.CORRELATION, CompensationMethod.RISK_PARITY]
        ),
        joint_dataset_hash=_h("c"),
        joint_evidence_hash=_h("d"),
        provenance_hash=_h("e"),
        created_at_utc="2026-08-25T00:00:00+00:00",
    )
    assert meta.composition_hash()
