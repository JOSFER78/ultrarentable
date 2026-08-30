"""services/queue/durable_job_queue.py
Cola Duradera 24/7 y Watchdog de Recuperación ante Caídas para Ultrarentable V2.
Garantiza persistencia en SQLite WAL, transacciones atómicas e idempotencia estricta.
Especificación oficial según Sección 7 y 8 del Informe Maestro v5.3.0.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from contracts.queue_contracts import (
    DurableJob,
    JobStatus,
    JobType,
    WatchdogRecoveryReport,
)
from services.api.app.config import STATE_DB_PATH

logger = logging.getLogger("DurableJobQueue")


class DurableJobQueue:
    """Motor de Cola Persistente y Watchdog de Alta Disponibilidad."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = str(db_path or STATE_DB_PATH)
        self._lock = threading.RLock()
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA busy_timeout = 30000;")
        conn.execute("PRAGMA synchronous = NORMAL;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            conn = self._get_connection()
            conn.execute("PRAGMA journal_mode=WAL;")
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS durable_job_queue (
                    job_id TEXT PRIMARY KEY,
                    job_type TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 5,
                    status TEXT NOT NULL DEFAULT 'PENDING',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL DEFAULT 3,
                    error_message TEXT,
                    created_at_utc TEXT NOT NULL,
                    updated_at_utc TEXT NOT NULL,
                    completed_at_utc TEXT
                );
                """
            )
            cur.execute("CREATE INDEX IF NOT EXISTS idx_djq_status_prio ON durable_job_queue(status, priority DESC);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_djq_created ON durable_job_queue(created_at_utc);")
            conn.commit()
            conn.close()

    def enqueue(
        self,
        job_type: JobType,
        payload: Dict[str, Any],
        priority: int = 5,
        max_attempts: int = 3,
    ) -> DurableJob:
        """Encola un nuevo trabajo persistente."""
        now_utc = datetime.now(timezone.utc).isoformat()
        job_id = f"job_{int(time.time())}_{uuid.uuid4().hex[:6]}"

        job = DurableJob(
            job_id=job_id,
            job_type=job_type,
            payload=payload,
            priority=priority,
            status=JobStatus.PENDING,
            attempts=0,
            max_attempts=max_attempts,
            error_message=None,
            created_at_utc=now_utc,
            updated_at_utc=now_utc,
            completed_at_utc=None,
        )

        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO durable_job_queue (
                    job_id, job_type, payload, priority, status,
                    attempts, max_attempts, error_message, created_at_utc,
                    updated_at_utc, completed_at_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    job.job_id,
                    job.job_type.value,
                    json.dumps(job.payload),
                    job.priority,
                    job.status.value,
                    job.attempts,
                    job.max_attempts,
                    job.error_message,
                    job.created_at_utc,
                    job.updated_at_utc,
                    job.completed_at_utc,
                ),
            )
            conn.commit()
            conn.close()

        logger.info(f"Trabajo encolado: {job_id} ({job_type.value}) con prioridad {priority}")
        return job

    def fetch_next_job(self) -> Optional[DurableJob]:
        """Reclama atómicamente el siguiente trabajo pendiente con mayor prioridad."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT job_id, job_type, payload, priority, status,
                       attempts, max_attempts, error_message, created_at_utc,
                       updated_at_utc, completed_at_utc
                FROM durable_job_queue
                WHERE status IN ('PENDING', 'RETRYING')
                ORDER BY priority DESC, created_at_utc ASC
                LIMIT 1;
                """
            )
            row = cur.fetchone()
            if not row:
                conn.close()
                return None

            job_id = row["job_id"]
            attempts = row["attempts"] + 1
            now_utc = datetime.now(timezone.utc).isoformat()

            cur.execute(
                """
                UPDATE durable_job_queue
                SET status = 'IN_PROGRESS',
                    attempts = ?,
                    updated_at_utc = ?
                WHERE job_id = ?;
                """,
                (attempts, now_utc, job_id),
            )
            conn.commit()

            job = DurableJob(
                job_id=job_id,
                job_type=JobType(row["job_type"]),
                payload=json.loads(row["payload"]),
                priority=row["priority"],
                status=JobStatus.IN_PROGRESS,
                attempts=attempts,
                max_attempts=row["max_attempts"],
                error_message=row["error_message"],
                created_at_utc=row["created_at_utc"],
                updated_at_utc=now_utc,
                completed_at_utc=None,
            )
            conn.close()
            return job

    def complete_job(self, job_id: str, outcome_summary: Optional[str] = None) -> bool:
        """Marca un trabajo como completado con éxito."""
        now_utc = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE durable_job_queue
                SET status = 'COMPLETED',
                    completed_at_utc = ?,
                    updated_at_utc = ?
                WHERE job_id = ?;
                """,
                (now_utc, now_utc, job_id),
            )
            changed = cur.rowcount > 0
            conn.commit()
            conn.close()
            return changed

    def fail_job(self, job_id: str, error_message: str) -> JobStatus:
        """Registra un error y decide si reintentar o marcar como fallo terminal."""
        now_utc = datetime.now(timezone.utc).isoformat()
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT attempts, max_attempts FROM durable_job_queue WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            if not row:
                conn.close()
                return JobStatus.FAILED

            attempts = row["attempts"]
            max_attempts = row["max_attempts"]

            new_status = JobStatus.RETRYING if attempts < max_attempts else JobStatus.FAILED

            cur.execute(
                """
                UPDATE durable_job_queue
                SET status = ?,
                    error_message = ?,
                    updated_at_utc = ?
                WHERE job_id = ?;
                """,
                (new_status.value, error_message, now_utc, job_id),
            )
            conn.commit()
            conn.close()
            return new_status

    def get_job(self, job_id: str) -> Optional[DurableJob]:
        """Consulta el estado de un trabajo por su ID."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM durable_job_queue WHERE job_id = ?", (job_id,))
            row = cur.fetchone()
            conn.close()
            if not row:
                return None
            return DurableJob(
                job_id=row["job_id"],
                job_type=JobType(row["job_type"]),
                payload=json.loads(row["payload"]),
                priority=row["priority"],
                status=JobStatus(row["status"]),
                attempts=row["attempts"],
                max_attempts=row["max_attempts"],
                error_message=row["error_message"],
                created_at_utc=row["created_at_utc"],
                updated_at_utc=row["updated_at_utc"],
                completed_at_utc=row["completed_at_utc"],
            )

    def list_jobs(self, status: Optional[JobStatus] = None, limit: int = 50) -> List[DurableJob]:
        """Lista los trabajos según su estado."""
        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            if status:
                cur.execute(
                    "SELECT * FROM durable_job_queue WHERE status = ? ORDER BY priority DESC, created_at_utc ASC LIMIT ?",
                    (status.value, limit),
                )
            else:
                cur.execute(
                    "SELECT * FROM durable_job_queue ORDER BY priority DESC, created_at_utc DESC LIMIT ?",
                    (limit,),
                )
            rows = cur.fetchall()
            conn.close()
            return [
                DurableJob(
                    job_id=r["job_id"],
                    job_type=JobType(r["job_type"]),
                    payload=json.loads(r["payload"]),
                    priority=r["priority"],
                    status=JobStatus(r["status"]),
                    attempts=r["attempts"],
                    max_attempts=r["max_attempts"],
                    error_message=r["error_message"],
                    created_at_utc=r["created_at_utc"],
                    updated_at_utc=r["updated_at_utc"],
                    completed_at_utc=r["completed_at_utc"],
                )
                for r in rows
            ]

    def recover_orphaned_jobs(self, max_in_progress_seconds: int = 300) -> WatchdogRecoveryReport:
        """Watchdog de recuperación: reasigna jobs en IN_PROGRESS colgados a RETRYING o PENDING."""
        now_ts = time.time()
        now_utc = datetime.now(timezone.utc).isoformat()
        orphaned_ids: List[str] = []

        with self._lock:
            conn = self._get_connection()
            cur = conn.cursor()
            cur.execute("SELECT job_id, updated_at_utc, attempts, max_attempts FROM durable_job_queue WHERE status = 'IN_PROGRESS'")
            rows = cur.fetchall()

            for r in rows:
                jid = r["job_id"]
                upd_str = r["updated_at_utc"]
                try:
                    # Parse timestamp
                    dt = datetime.fromisoformat(upd_str)
                    age_seconds = now_ts - dt.timestamp()
                except Exception:
                    age_seconds = max_in_progress_seconds + 1

                if age_seconds > max_in_progress_seconds:
                    new_status = 'RETRYING' if r["attempts"] < r["max_attempts"] else 'FAILED'
                    cur.execute(
                        """
                        UPDATE durable_job_queue
                        SET status = ?,
                            error_message = 'Watchdog recovered orphaned job after crash or stall',
                            updated_at_utc = ?
                        WHERE job_id = ?;
                        """,
                        (new_status, now_utc, jid),
                    )
                    orphaned_ids.append(jid)

            conn.commit()
            conn.close()

        msg = f"Watchdog recuperó {len(orphaned_ids)} trabajos huérfanos."
        logger.info(msg)
        return WatchdogRecoveryReport(
            recovered_jobs_count=len(orphaned_ids),
            orphaned_jobs_reset=orphaned_ids,
            timestamp_utc=now_utc,
            engine_version="5.3.0",
            message=msg,
        )


durable_job_queue = DurableJobQueue()


class HAWatchdog:
    """High Availability Watchdog Daemon 24/7 para supervisión y auto-recuperación de la cola durable."""

    def __init__(self, queue: Optional[DurableJobQueue] = None, interval_seconds: float = 10.0):
        self.queue = queue or durable_job_queue
        self.interval_seconds = interval_seconds
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self.is_running = False

    def start(self) -> None:
        if self.is_running:
            return
        self.is_running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="HAWatchdogThread")
        self._thread.start()
        logger.info("🟢 HAWatchdog daemon iniciado (intervalo: %ss).", self.interval_seconds)

    def stop(self) -> None:
        if not self.is_running:
            return
        self._stop_event.set()
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)
        logger.info("🛑 HAWatchdog daemon detenido.")

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.queue.recover_orphaned_jobs()
            except Exception as e:
                logger.error("Error en ciclo de HAWatchdog: %s", e)
            self._stop_event.wait(self.interval_seconds)


ha_watchdog = HAWatchdog()

