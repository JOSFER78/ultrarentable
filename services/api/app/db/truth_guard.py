"""Runtime truth guard for legacy bootstrap data.

The repository historically seeded demonstration candidates/execution sessions during
DB initialization. Those records are not quantitative evidence and must not survive
into the operational database. This guard removes only the known legacy demo identities.
It does NOT synthesize replacement data.
"""
from __future__ import annotations

from sqlalchemy import delete
from sqlalchemy.orm import Session

from services.api.app.db.database import AuditEventModel, CandidateModel, ExecutionSessionModel

LEGACY_DEMO_CANDIDATE_IDS = {"strat_1_0_54", "strat_1_0_32"}
LEGACY_DEMO_SESSION_IDS = {"session_bingx_demo_01"}
LEGACY_DEMO_EVENT_IDS = {"evt_001_init", "evt_002_reclass_54", "evt_003_reclass_32"}


def purge_legacy_demo_records(db: Session) -> dict[str, int]:
    """Remove only known synthetic bootstrap records; return deletion counts."""
    deleted_candidates = db.execute(
        delete(CandidateModel).where(CandidateModel.candidate_id.in_(LEGACY_DEMO_CANDIDATE_IDS))
    ).rowcount or 0
    deleted_sessions = db.execute(
        delete(ExecutionSessionModel).where(ExecutionSessionModel.session_id.in_(LEGACY_DEMO_SESSION_IDS))
    ).rowcount or 0
    deleted_events = db.execute(
        delete(AuditEventModel).where(AuditEventModel.event_id.in_(LEGACY_DEMO_EVENT_IDS))
    ).rowcount or 0
    db.commit()
    return {
        "deleted_demo_candidates": int(deleted_candidates),
        "deleted_demo_sessions": int(deleted_sessions),
        "deleted_demo_events": int(deleted_events),
    }
