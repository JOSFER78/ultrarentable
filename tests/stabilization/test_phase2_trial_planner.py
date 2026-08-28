from scripts.phase2_trial_planner import PLANNER_VERSION, budget_space


def _family_key(item):
    signal = item.get("archetype", item.get("family", "UNKNOWN"))
    exit_family = item.get("exit_family") or "DEFAULT"
    return f"{signal.upper()}|{str(exit_family).upper()}"


def test_budget_is_deterministic_and_bounded():
    space = [
        {"archetype": "A", "exit_family": "X", "x": i} for i in range(10)
    ] + [
        {"archetype": "B", "exit_family": "Y", "x": i} for i in range(10)
    ]
    first = budget_space(space, 8, "abc123")
    second = budget_space(space, 8, "abc123")
    assert first == second
    assert len(first) == 8
    assert PLANNER_VERSION == "phase2-stratified-v3"


def test_budget_preserves_signal_and_exit_family_representation():
    space = (
        [{"archetype": "A", "exit_family": "X", "x": i} for i in range(10)]
        + [{"archetype": "A", "exit_family": "Y", "x": i} for i in range(10)]
        + [{"archetype": "B", "exit_family": "X", "x": i} for i in range(10)]
    )
    selected = budget_space(space, 6, "dataset-hash")
    families = {_family_key(item) for item in selected}
    assert len(families) == 3


def test_budget_removes_canonical_duplicates_before_selection():
    space = [
        {"archetype": "A", "exit_family": "X", "x": 1},
        {"x": 1, "exit_family": "X", "archetype": "A"},
        {"archetype": "B", "exit_family": "Y", "x": 2},
    ]
    selected = budget_space(space, 10, "dataset-hash-dedup")
    assert len(selected) == 2


def test_budget_has_no_duplicates():
    space = [
        {"archetype": "A", "exit_family": "X", "x": i} for i in range(12)
    ] + [
        {"archetype": "B", "exit_family": "Y", "x": i} for i in range(12)
    ]
    selected = budget_space(space, 12, "dataset-hash-2")
    keys = {str(sorted(item.items())) for item in selected}
    assert len(selected) == len(keys)
