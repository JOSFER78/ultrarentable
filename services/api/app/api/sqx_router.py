"""StrategyQuant X connectivity surface.

This router is limited to *source inspection and control*.
Canonical extraction now lives in ``/api/v2/strategy-lab``. The former
SQX ingest/rentable shortcuts are deliberately disabled because they created
synthetic backtest rows, default capital, inferred datasets and hard-coded
profitability gates.
"""

from __future__ import annotations

import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.sqx_bridge.sqx_client import SQXMCPClient, SQXMCPError

sqx_router = APIRouter(prefix="/sqx", tags=["StrategyQuant X MCP Integration"])


class ProjectRunRequest(BaseModel):
    name: str = Field(..., description="Project name in StrategyQuant X")


@sqx_router.get("/status")
def get_sqx_status(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    return client.check_connection()


@sqx_router.get("/tools")
def list_sqx_tools(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        tools = client.list_tools()
        return {"status": "SUCCESS", "url": url, "count": len(tools), "tools": tools}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects")
def list_sqx_projects(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        projects = client.list_projects()
        return {"status": "SUCCESS", "url": url, "count": len(projects), "projects": projects}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/databanks")
def list_sqx_databanks(project_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        databanks = client.list_databanks(project_name)
        return {"status": "SUCCESS", "project": project_name, "count": len(databanks), "databanks": databanks}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/databanks/{databank_name}/strategies")
def list_sqx_strategies(project_name: str, databank_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        strategies = client.list_strategies(project_name, databank_name)
        return {
            "status": "SUCCESS",
            "project": project_name,
            "databank": databank_name,
            "count": len(strategies),
            "strategies": strategies,
        }
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/databanks/{databank_name}/strategies/{strategy_name}")
def get_sqx_strategy_stats(project_name: str, databank_name: str, strategy_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        stats = client.get_strategy_stats(project_name, databank_name, strategy_name)
        return {
            "status": "SUCCESS",
            "project": project_name,
            "databank": databank_name,
            "strategy": strategy_name,
            "stats": stats,
        }
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/config-summary")
def get_sqx_project_config_summary(project_name: str) -> Dict[str, Any]:
    """Read the actual project configuration without fabricating missing values."""
    cfx_path = f"/home/ubuntu/StrategyQuantX/user/projects/{project_name}/project.cfx"
    if not os.path.exists(cfx_path):
        return {"status": "NOT_FOUND", "project": project_name, "message": "project.cfx not available on the configured SQX host"}

    summary: Dict[str, Any] = {
        "status": "SUCCESS",
        "project": project_name,
        "symbol": None,
        "timeframe": None,
        "dataset_name": None,
        "fitness_function": None,
        "session_filter": None,
        "min_conditions": None,
        "max_conditions": None,
        "sl_required": None,
    }
    try:
        with zipfile.ZipFile(cfx_path, "r") as archive:
            if "Build-Task1.xml" in archive.namelist():
                root = ET.fromstring(archive.read("Build-Task1.xml").decode("utf-8", errors="strict"))
                for elem in root.iter():
                    if elem.tag == "Chart" and "symbol" in elem.attrib:
                        summary["symbol"] = elem.attrib.get("symbol")
                        summary["timeframe"] = elem.attrib.get("timeframe")
                    elif elem.tag == "Ranking" and "type" in elem.attrib:
                        summary["fitness_function"] = elem.attrib.get("type")
                    elif elem.tag == "Param":
                        key = elem.attrib.get("key")
                        if key == "Session":
                            summary["session_filter"] = elem.text
                        elif key == "MinConditions":
                            summary["min_conditions"] = elem.text
                        elif key == "MaxConditions":
                            summary["max_conditions"] = elem.text
                        elif key == "SLRequired":
                            summary["sl_required"] = elem.text
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SQX_CONFIG_PARSE_ERROR: {exc}") from exc
    return summary


@sqx_router.post("/projects/{project_name}/run")
def run_sqx_project(project_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        return {"status": "SUCCESS", "project": project_name, "result": client.run_project(project_name)}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.post("/projects/{project_name}/stop")
def stop_sqx_project(project_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    client = SQXMCPClient(base_url=url)
    try:
        return {"status": "SUCCESS", "project": project_name, "result": client.stop_project(project_name)}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.post("/projects/{project_name}/ingest")
def legacy_sqx_ingest_disabled(project_name: str) -> Dict[str, Any]:
    """Legacy route intentionally disabled to prevent synthetic backtest creation."""
    raise HTTPException(
        status_code=410,
        detail={
            "code": "LEGACY_SQX_INGEST_DISABLED",
            "message": "Use /api/v2/strategy-lab/extract/{project_name}. Extraction does not create backtests or certifications.",
            "project": project_name,
        },
    )


@sqx_router.get("/rentable")
def legacy_sqx_rentable_disabled() -> Dict[str, Any]:
    raise HTTPException(
        status_code=410,
        detail={
            "code": "LEGACY_SQX_RENTABLE_DISABLED",
            "message": "Profitability filtering is no longer performed by the SQX adapter. Use the canonical dataset + backtest + evidence pipeline.",
        },
    )


@sqx_router.post("/sync")
def legacy_sqx_sync_disabled() -> Dict[str, Any]:
    raise HTTPException(
        status_code=410,
        detail={
            "code": "LEGACY_SQX_SYNC_DISABLED",
            "message": "Bulk SQX sync is disabled until the canonical extraction/data-binding pipeline is used.",
        },
    )


@sqx_router.get("/feedback-loop")
def get_sqx_feedback_loop() -> Dict[str, Any]:
    from services.semantic_ai.sqx_feedback_loop import SQXFeedbackLoop
    return SQXFeedbackLoop().analyze_learning_curve()
