from scripts.phase2_trial_planner import PLANNER_VERSION, budget_space


def test_budget_is_deterministic_and_bounded():
    space = [
        {"archetype": "A", "x": i} for i in range(10)
    ] + [
        {"archetype": "B", "x": i} for i in range(10)
    ]
    first = budget_space(space, 8, "abc123")
    second = budget_space(space, 8, "abc123")
    assert first == second
    assert len(first) == 8
    assert PLANNER_VERSION == "phase2-stratified-v1"


def test_budget_preserves_family_representation():
    space = (
        [{"archetype": "A", "x": i} for i in range(10)]
        + [{"archetype": "B", "x": i} for i in range(10)]
        + [{"archetype": "C", "x": i} for i in range(10)]
    )
    selected = budget_space(space, 6, "dataset-hash")
    families = {item["archetype"] for item in selected}
    assert families == {"A", "B", "C"}


def test_budget_has_no_duplicates():
    space = [
        {"archetype": "A", "x": i} for i in range(12)
    ] + [
        {"archetype": "B", "x": i} for i in range(12)
    ]
    selected = budget_space(space, 12, "dataset-hash-2")
    assert len(selected) == len({tuple(sorted(item.items())) for item in selected})
