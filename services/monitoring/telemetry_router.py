"""services/monitoring/telemetry_router.py
Router FastAPI de Telemetría en Tiempo Real y Server-Sent Events (SSE) para Next.js.
Permite a la interfaz web consumir artefactos inmutables y eventos en vivo sin inventar datos en el cliente.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncGenerator, Dict, List
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from services.core.event_bus import DomainEvent, event_bus
from services.monitoring.supervisor import SystemSupervisor

router = APIRouter()
supervisor_instance = SystemSupervisor()


@router.get("/health")
async def get_system_health() -> Dict[str, Any]:
    """Retorna el estado de salud en tiempo real de los 8 workers del sistema."""
    return supervisor_instance.get_system_health()


@router.get("/history")
async def get_event_history(limit: int = 50) -> List[Dict[str, Any]]:
    """Obtiene los últimos N eventos del bus de eventos."""
    events = event_bus.get_history(limit=limit)
    return [
        {
            "event_type": type(e).__name__,
            "event_id": e.event_id,
            "timestamp_utc_ms": e.timestamp_utc_ms,
        }
        for e in events
    ]


async def event_generator(request: Request) -> AsyncGenerator[str, None]:
    """Generador asíncrono para Server-Sent Events (SSE)."""
    last_sent_idx = len(event_bus.history)

    while True:
        if await request.is_disconnected():
            break

        current_history = event_bus.history
        if len(current_history) > last_sent_idx:
            for event in current_history[last_sent_idx:]:
                payload = {
                    "event_type": type(event).__name__,
                    "event_id": event.event_id,
                    "timestamp_utc_ms": event.timestamp_utc_ms,
                }
                yield f"data: {json.dumps(payload)}\n\n"
            last_sent_idx = len(current_history)

        await asyncio.sleep(0.5)


@router.get("/stream")
async def stream_telemetry_events(request: Request) -> StreamingResponse:
    """Endpoint SSE para streaming continuo de telemetría a la UI de Next.js."""
    return StreamingResponse(
        event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
