"""services/api/app/api/research_router.py
Router FastAPI para el Laboratorio de Refinamiento Cuantitativo & Demonio 24/7.
Provee streaming SSE de logs físicos, control de la cola y estado del visor en vivo.
"""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, AsyncGenerator, Dict
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from services.optimization.continuous_research_daemon import (
    continuous_research_daemon,
    RefinementProgressEvent,
)
from services.core.event_bus import event_bus

router = APIRouter(prefix="/api/v1/research", tags=["Research & Refinement Lab"])


class RefineSingleRequest(BaseModel):
    max_iterations: int = 3


@router.get("/status")
async def get_research_status() -> Dict[str, Any]:
    """Retorna el estado completo del visor, la cola y los logs en vivo."""
    return continuous_research_daemon.get_status()


@router.post("/start")
async def start_research_daemon() -> Dict[str, Any]:
    """Inicia el bucle continuo 24/7 de refinamiento."""
    continuous_research_daemon.start_autonomous()
    return {"status": "SUCCESS", "message": "Demonio de refinamiento 24/7 iniciado."}


@router.post("/pause")
async def pause_research_daemon() -> Dict[str, Any]:
    """Pausa el bucle de refinamiento continuo."""
    continuous_research_daemon.pause()
    return {"status": "SUCCESS", "message": "Demonio de refinamiento pausado."}


@router.post("/process-next")
async def process_next_candidate() -> Dict[str, Any]:
    """Fuerza el procesamiento inmediato del siguiente candidato en la cola."""
    continuous_research_daemon.refresh_queue_from_db()
    status = continuous_research_daemon.get_status()
    pending = [q for q in status["queue"] if q["status"] in ("EN_COLA", "REINTENTO")]
    if not pending:
        raise HTTPException(status_code=400, detail="No hay candidatos pendientes en la cola.")
    
    cid = pending[0]["candidate_id"]
    # Ejecutar en hilo asíncrono para no bloquear la respuesta HTTP
    asyncio.create_task(asyncio.to_thread(continuous_research_daemon.refine_single_now, cid, 3))
    return {"status": "PROCESSING", "candidate_id": cid, "message": f"Iniciado refinamiento para {cid}."}


@router.post("/refine/{candidate_id}")
async def refine_specific_candidate(candidate_id: str, body: RefineSingleRequest = RefineSingleRequest()) -> Dict[str, Any]:
    """Inicia el refinamiento interactivo de un candidato específico."""
    result = await asyncio.to_thread(continuous_research_daemon.refine_single_now, candidate_id, body.max_iterations)
    return result


async def research_event_generator(request: Request) -> AsyncGenerator[str, None]:
    """Generador SSE para streaming continuo de telemetría y logs del visor."""
    # Handshake inicial
    init_frame = {
        "event_type": "CONNECTED_ACK",
        "status": "ONLINE",
        "timestamp_ms": int(time.time() * 1000),
    }
    yield f"data: {json.dumps(init_frame)}\n\n"

    last_log_count = len(continuous_research_daemon.live_logs)

    while True:
        if await request.is_disconnected():
            break

        current_logs = continuous_research_daemon.live_logs
        if len(current_logs) > last_log_count:
            for log_entry in current_logs[last_log_count:]:
                payload = {
                    "event_type": "LOG_ENTRY",
                    "data": log_entry,
                    "status_snapshot": continuous_research_daemon.get_status(),
                }
                yield f"data: {json.dumps(payload)}\n\n"
            last_log_count = len(current_logs)
        else:
            # Enviar actualización periódica de estado cada 2 segundos
            status_payload = {
                "event_type": "STATUS_UPDATE",
                "status_snapshot": continuous_research_daemon.get_status(),
            }
            yield f"data: {json.dumps(status_payload)}\n\n"

        await asyncio.sleep(1.0)


@router.get("/stream")
async def stream_research_events(request: Request) -> StreamingResponse:
    """Canal SSE para alimentar el visor en tiempo real de Next.js."""
    return StreamingResponse(
        research_event_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
