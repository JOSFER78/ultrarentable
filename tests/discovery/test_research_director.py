from services.discovery.research_director import ResearchDirector


def test_research_director_is_deterministic_and_real_only():
    director = ResearchDirector()
    a = director.next_campaigns("c" * 64, [], campaign_budget=10, trials_per_campaign=10000)
    b = director.next_campaigns("c" * 64, [], campaign_budget=10, trials_per_campaign=10000)
    assert a == b
    assert len(a) == 10
    director.validate_campaigns(a)
    assert all(c.dataset_scope == "REAL_DATASET_ONLY" for c in a)
    assert all(c.search_intensity == 10000 for c in a)
