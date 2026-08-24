"""tests/test_durable_job_queue_and_watchdog.py
Pruebas Unitarias para la Cola Duradera SQLite WAL y el Watchdog de Recuperación.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

import pytest
from contracts.queue_contracts import JobStatus, JobType
from services.queue.durable_job_queue import DurableJobQueue


@pytest.fixture
def queue(tmp_path):
    db_file = tmp_path / "test_queue.db"
    return DurableJobQueue(db_path=str(db_file))


def test_enqueue_and_priority_dispatch(queue):
    """Verifica que los trabajos se despachan estrictamente en orden de prioridad."""
    job_low = queue.enqueue(JobType.PORTFOLIO_SWEEP, {"task": "low"}, priority=2)
    job_high = queue.enqueue(JobType.REVALIDATE_CANDIDATE, {"task": "high"}, priority=9)
    job_mid = queue.enqueue(JobType.REPROGRAM_MUTATION, {"task": "mid"}, priority=5)

    # El primero en despacharse debe ser job_high
    claimed_1 = queue.fetch_next_job()
    assert claimed_1 is not None
    assert claimed_1.job_id == job_high.job_id
    assert claimed_1.status == JobStatus.IN_PROGRESS

    # El segundo debe ser job_mid
    claimed_2 = queue.fetch_next_job()
    assert claimed_2 is not None
    assert claimed_2.job_id == job_mid.job_id

    # El tercero debe ser job_low
    claimed_3 = queue.fetch_next_job()
    assert claimed_3 is not None
    assert claimed_3.job_id == job_low.job_id

    # No quedan más trabajos pendientes
    assert queue.fetch_next_job() is None


def test_job_completion_and_failure_retry_cycle(queue):
    """Verifica el ciclo de reintentos y marcado terminal de fallos."""
    job = queue.enqueue(JobType.FAST_BACKTEST_RUN, {"cand_id": "c1"}, priority=5, max_attempts=2)

    claimed = queue.fetch_next_job()
    assert claimed.attempts == 1

    # Primer fallo -> debe pasar a RETRYING
    st1 = queue.fail_job(claimed.job_id, "Temporary network timeout")
    assert st1 == JobStatus.RETRYING

    # Reclamar nuevamente
    claimed_again = queue.fetch_next_job()
    assert claimed_again is not None
    assert claimed_again.job_id == job.job_id
    assert claimed_again.attempts == 2

    # Segundo fallo -> alcanza max_attempts -> debe pasar a FAILED
    st2 = queue.fail_job(claimed.job_id, "Fatal out of memory error")
    assert st2 == JobStatus.FAILED

    # Ya no debe estar disponible para fetch
    assert queue.fetch_next_job() is None


def test_watchdog_orphaned_job_recovery(queue):
    """Verifica que el Watchdog detecta trabajos bloqueados y los restablece para reintento."""
    job = queue.enqueue(JobType.CANONICAL_AUDIT, {"target": "audit_1"}, priority=8, max_attempts=3)
    claimed = queue.fetch_next_job()
    assert claimed.status == JobStatus.IN_PROGRESS

    # Ejecutar watchdog con max_in_progress_seconds = 0 para simular timeout
    report = queue.recover_orphaned_jobs(max_in_progress_seconds=0)

    assert report.recovered_jobs_count == 1
    assert job.job_id in report.orphaned_jobs_reset

    # Ahora el trabajo debe estar de nuevo en RETRYING y disponible
    reclaimed = queue.fetch_next_job()
    assert reclaimed is not None
    assert reclaimed.job_id == job.job_id
