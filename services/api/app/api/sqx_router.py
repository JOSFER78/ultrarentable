"""StrategyQuant X connectivity surface.

Limited to real SQX source inspection/control. Strategy extraction is handled by
``/api/v2/strategy-lab`` and never fabricates backtest/certification evidence.
"""
from __future__ import annotations

import os
import zipfile
import xml.etree.ElementTree as ET
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from services.sqx_bridge.sqx_client import SQXMCPClient, SQXMCPError

sqx_router = APIRouter(prefix="/sqx", tags=["StrategyQuant X MCP Integration"])
DEFAULT_SQX_MCP_URL = os.getenv("SQX_MCP_URL", "http://127.0.0.1:8080/mcp")


def _client(url: Optional[str]) -> SQXMCPClient:
    return SQXMCPClient(base_url=(url or DEFAULT_SQX_MCP_URL).strip())


@sqx_router.get("/status")
def get_sqx_status(url: Optional[str] = Query(None)) -> Dict[str, Any]:
    return _client(url).check_connection()


@sqx_router.get("/tools")
def list_sqx_tools(url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        tools = client.list_tools()
        return {"status": "SUCCESS", "url": client.base_url, "count": len(tools), "tools": tools}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects")
def list_sqx_projects(url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        projects = client.list_projects()
        return {"status": "SUCCESS", "url": client.base_url, "count": len(projects), "projects": projects}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/databanks")
def list_sqx_databanks(project_name: str, url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        databanks = client.list_databanks(project_name)
        return {"status": "SUCCESS", "project": project_name, "count": len(databanks), "databanks": databanks}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/databanks/{databank_name}/strategies")
def list_sqx_strategies(project_name: str, databank_name: str, url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        strategies = client.list_strategies(project_name, databank_name)
        return {"status": "SUCCESS", "project": project_name, "databank": databank_name, "count": len(strategies), "strategies": strategies}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/databanks/{databank_name}/strategies/{strategy_name}")
def get_sqx_strategy_stats(project_name: str, databank_name: str, strategy_name: str, url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        stats = client.get_strategy_stats(project_name, databank_name, strategy_name)
        return {"status": "SUCCESS", "project": project_name, "databank": databank_name, "strategy": strategy_name, "stats": stats}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.get("/projects/{project_name}/config-summary")
def get_sqx_project_config_summary(project_name: str) -> Dict[str, Any]:
    cfx_path = f"/home/ubuntu/StrategyQuantX/user/projects/{project_name}/project.cfx"
    if not os.path.exists(cfx_path):
        return {"status": "NOT_FOUND", "project": project_name, "message": "project.cfx not available on the configured SQX host"}
    summary: Dict[str, Any] = {"status": "SUCCESS", "project": project_name, "symbol": None, "timeframe": None, "dataset_name": None, "fitness_function": None, "session_filter": None, "min_conditions": None, "max_conditions": None, "sl_required": None}
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
                        if key in {"Session", "MinConditions", "MaxConditions", "SLRequired"}:
                            summary[{"Session":"session_filter", "MinConditions":"min_conditions", "MaxConditions":"max_conditions", "SLRequired":"sl_required"}[key]] = elem.text
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"SQX_CONFIG_PARSE_ERROR: {exc}") from exc
    return summary


@sqx_router.post("/projects/{project_name}/run")
def run_sqx_project(project_name: str, url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        return {"status": "SUCCESS", "project": project_name, "result": client.run_project(project_name)}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.post("/projects/{project_name}/stop")
def stop_sqx_project(project_name: str, url: Optional[str] = Query(None)) -> Dict[str, Any]:
    client = _client(url)
    try:
        return {"status": "SUCCESS", "project": project_name, "result": client.stop_project(project_name)}
    except SQXMCPError as exc:
        raise HTTPException(status_code=502, detail=f"SQX_MCP_ERROR: {exc}") from exc


@sqx_router.post("/projects/{project_name}/ingest")
def legacy_sqx_ingest_disabled(project_name: str) -> Dict[str, Any]:
    raise HTTPException(status_code=410, detail={"code": "LEGACY_SQX_INGEST_DISABLED", "message": "Use /api/v2/strategy-lab/extract/{project_name}.", "project": project_name})


@sqx_router.get("/rentable")
def legacy_sqx_rentable_disabled() -> Dict[str, Any]:
    raise HTTPException(status_code=410, detail={"code": "LEGACY_SQX_RENTABLE_DISABLED", "message": "Profitability filtering belongs to the canonical dataset/backtest/evidence pipeline."})


@sqx_router.post("/sync")
def legacy_sqx_sync_disabled() -> Dict[str, Any]:
    raise HTTPException(status_code=410, detail={"code": "LEGACY_SQX_SYNC_DISABLED", "message": "Bulk SQX sync is disabled; use Strategy Lab extraction."})


@sqx_router.get("/feedback-loop")
def get_sqx_feedback_loop() -> Dict[str, Any]:
    from services.semantic_ai.sqx_feedback_loop import SQXFeedbackLoop
    return SQXFeedbackLoop().analyze_learning_curve()
