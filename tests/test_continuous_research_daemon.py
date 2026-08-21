"""tests/test_continuous_research_daemon.py
Test de verificación del Demonio Autónomo de Refinamiento 24/7 y la Cola de Estrategias.
Doctrina Zero-Mocks & Real-Only.
"""

import pytest
from services.optimization.continuous_research_daemon import (
    ContinuousResearchDaemon,
    continuous_research_daemon,
)


def test_research_daemon_initialization():
    status = continuous_research_daemon.get_status()
    assert "is_running" in status
    assert "queue" in status
    assert "stats" in status
    assert "queue_summary" in status
    assert status["queue_summary"]["total_in_queue"] >= 0


def test_research_daemon_queue_refresh():
    queue = continuous_research_daemon.refresh_queue_from_db()
    assert isinstance(queue, list)
    if len(queue) > 0:
        first = queue[0]
        assert "candidate_id" in first
        assert "tier" in first
        assert "initial_gates" in first
        assert first["initial_gates"] >= 7


def test_research_daemon_single_refinement_execution():
    status = continuous_research_daemon.get_status()
    if status["queue"]:
        target_cid = status["queue"][0]["candidate_id"]
        res = continuous_research_daemon.refine_single_now(target_cid, max_iterations=1)
        assert "candidate_id" in res
        assert res["candidate_id"] == target_cid
        assert "gates_passed_count" in res
        assert "iteration_history" in res
