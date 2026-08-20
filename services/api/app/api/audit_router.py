"""FastAPI Router for Audit Events and Persistent Timeline."""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from services.api.app.db.database import get_db, AuditEventModel

audit_router = APIRouter(prefix="/audit", tags=["Audit Events & Timeline"])


class AuditEventCreateSchema(BaseModel):
    category: str = Field("SYSTEM", description="CAMPAIGN, GATE, EXPORT, PAPER, LIVE, KILL_SWITCH, SYSTEM, RULE_CHANGE")
    route: str = Field("SYSTEM", description="ULTRA, FONDEO, SYSTEM")
    title: str
    description: str
    severity: str = Field("INFO", description="INFO, WARNING, CRITICAL, SUCCESS")


@audit_router.get("/events")
def list_audit_events(
    route: Optional[str] = Query(None, description="ULTRA, FONDEO, SYSTEM"),
    category: Optional[str] = Query(None, description="CAMPAIGN, GATE, EXPORT, PAPER, LIVE, KILL_SWITCH, SYSTEM, RULE_CHANGE"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
) -> List[Dict[str, Any]]:
    """List timeline of system and operational audit events."""
    query = db.query(AuditEventModel)
    if route:
        query = query.filter(AuditEventModel.route == route.upper())
    if category:
        query = query.filter(AuditEventModel.category == category.upper())
        
    results = []
    for e in query.order_by(AuditEventModel.created_at.desc(), AuditEventModel.event_id.desc()).limit(limit).all():
        results.append({
            "event_id": e.event_id,
            "category": e.category,
            "route": e.route,
            "title": e.title,
            "description": e.description,
            "severity": e.severity,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    return results


@audit_router.post("/events")
def create_audit_event(payload: AuditEventCreateSchema, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Create a new audit event."""
    import uuid
    event_id = f"evt_{int(datetime.utcnow().timestamp() * 1000)}_{uuid.uuid4().hex[:6]}_{payload.category.lower()}"
    evt = AuditEventModel(
        event_id=event_id,
        category=payload.category.upper(),
        route=payload.route.upper(),
        title=payload.title,
        description=payload.description,
        severity=payload.severity.upper(),
        created_at=datetime.utcnow(),
    )
    db.add(evt)
    db.commit()
    db.refresh(evt)
    return {"status": "SUCCESS", "event_id": event_id}
