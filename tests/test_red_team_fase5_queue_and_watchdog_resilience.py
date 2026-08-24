"""tests/test_red_team_fase5_queue_and_watchdog_resilience.py
Auditoría Adversarial y Red-Team para FASE 5:
1. Resiliencia y Concurrencia de la Cola Persistente bajo estrés multi-hilo.
2. Idempotencia y Cero-Duplicación en el despacho de trabajos concurrentes.
3. Inmunidad del Watchdog ante reinicios forzados y caídas abruptas.
"""

import concurrent.futures
import pytest
from contracts.queue_contracts import JobStatus, JobType
from services.queue.durable_job_queue import DurableJobQueue


@pytest.fixture
def queue(tmp_path):
    db_file = tmp_path / "red_team_queue.db"
    return DurableJobQueue(db_path=str(db_file))


def test_red_team_concurrent_enqueuing_and_no_race_conditions(queue):
    """Red-Team: 20 hilos concurrentes encolando y reclamando trabajos sin colisiones ni duplicados."""
    total_jobs = 40

    def worker_enqueue(i):
        queue.enqueue(
            job_type=JobType.REVALIDATE_CANDIDATE,
            payload={"cand_index": i},
            priority=(i % 10) + 1,
            max_attempts=3,
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        list(executor.map(worker_enqueue, range(total_jobs)))

    # Verificar que exactamente 40 jobs existen
    all_jobs = queue.list_jobs(limit=100)
    assert len(all_jobs) == total_jobs

    claimed_ids = []

    def worker_claim(_):
        job = queue.fetch_next_job()
        if job:
            return job.job_id
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(worker_claim, range(total_jobs)))

    claimed_non_none = [r for r in results if r is not None]
    # Cada trabajo reclamado debe ser único (cero colisiones ni doble despacho)
    assert len(claimed_non_none) == len(set(claimed_non_none))


def test_red_team_watchdog_crash_recovery_idempotence(queue):
    """Red-Team: Recuperación repetida del Watchdog es idempotente y no corrompe estados finalizados."""
    j1 = queue.enqueue(JobType.FAST_BACKTEST_RUN, {"target": "c1"}, priority=5)
    j2 = queue.enqueue(JobType.FAST_BACKTEST_RUN, {"target": "c2"}, priority=5)

    # Reclamar ambos
    c1 = queue.fetch_next_job()
    c2 = queue.fetch_next_job()

    # Completar c1
    queue.complete_job(c1.job_id)

    # Dejar c2 colgado en IN_PROGRESS y simular caída
    report1 = queue.recover_orphaned_jobs(max_in_progress_seconds=0)
    assert report1.recovered_jobs_count == 1
    assert report1.orphaned_jobs_reset == [c2.job_id]

    # Ejecutar watchdog de nuevo inmediatamente -> debe reportar 0 jobs (idempotencia)
    report2 = queue.recover_orphaned_jobs(max_in_progress_seconds=0)
    assert report2.recovered_jobs_count == 0

    # c1 debe seguir completado intacto
    job1_after = queue.get_job(c1.job_id)
    assert job1_after.status == JobStatus.COMPLETED
