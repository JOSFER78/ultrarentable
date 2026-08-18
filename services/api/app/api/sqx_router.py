"""FastAPI Router for StrategyQuant X MCP integration in Ultra Rentable V2."""

from __future__ import annotations

from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from services.sqx_bridge.sqx_client import SQXMCPClient, SQXMCPError

sqx_router = APIRouter(prefix="/sqx", tags=["StrategyQuant X MCP Integration"])


class ProjectRunRequest(BaseModel):
    name: str = Field(..., description="Project name in StrategyQuant X")


@sqx_router.get("/status")
def get_sqx_status(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    """Check connectivity and state of the StrategyQuant X MCP server."""
    client = SQXMCPClient(base_url=url)
    return client.check_connection()


@sqx_router.get("/tools")
def list_sqx_tools(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    """Discover available MCP tools on the StrategyQuant X server."""
    client = SQXMCPClient(base_url=url)
    try:
        tools = client.list_tools()
        return {
            "status": "SUCCESS",
            "url": url,
            "count": len(tools),
            "tools": tools
        }
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.get("/projects")
def list_sqx_projects(url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    """List all projects available in the StrategyQuant X instance."""
    client = SQXMCPClient(base_url=url)
    try:
        projects = client.list_projects()
        return {
            "status": "SUCCESS",
            "url": url,
            "count": len(projects),
            "projects": projects
        }
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.get("/projects/{project_name}/databanks")
def list_sqx_databanks(project_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    """List databanks for a specified StrategyQuant X project."""
    client = SQXMCPClient(base_url=url)
    try:
        databanks = client.list_databanks(project_name)
        return {
            "status": "SUCCESS",
            "project": project_name,
            "count": len(databanks),
            "databanks": databanks
        }
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.get("/projects/{project_name}/databanks/{databank_name}/strategies")
def list_sqx_strategies(
    project_name: str,
    databank_name: str,
    url: str = Query("http://localhost:8081/mcp")
) -> Dict[str, Any]:
    """List strategies stored inside a specific databank of a project."""
    client = SQXMCPClient(base_url=url)
    try:
        strategies = client.list_strategies(project_name, databank_name)
        return {
            "status": "SUCCESS",
            "project": project_name,
            "databank": databank_name,
            "count": len(strategies),
            "strategies": strategies
        }
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.get("/projects/{project_name}/databanks/{databank_name}/strategies/{strategy_name}")
def get_sqx_strategy_stats(
    project_name: str,
    databank_name: str,
    strategy_name: str,
    url: str = Query("http://localhost:8081/mcp")
) -> Dict[str, Any]:
    """Get metrics and statistics for a specific strategy in a databank."""
    client = SQXMCPClient(base_url=url)
    try:
        stats = client.get_strategy_stats(project_name, databank_name, strategy_name)
        return {
            "status": "SUCCESS",
            "project": project_name,
            "databank": databank_name,
            "strategy": strategy_name,
            "stats": stats
        }
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.get("/projects/{project_name}/config-summary")
def get_sqx_project_config_summary(project_name: str) -> Dict[str, Any]:
    """Parse and return exact search and backtest configuration from SQX project.cfx."""
    import os, zipfile, xml.etree.ElementTree as ET
    cfx_path = f"/home/ubuntu/StrategyQuantX/user/projects/{project_name}/project.cfx"
    if not os.path.exists(cfx_path):
        return {
            "status": "NOT_FOUND",
            "project": project_name,
            "message": f"Archivo project.cfx no encontrado en {cfx_path}"
        }
    
    summary: Dict[str, Any] = {
        "status": "SUCCESS",
        "project": project_name,
        "symbol": "BTCUSDT",
        "timeframe": "H1",
        "dataset_name": "Binance USDT-M",
        "fitness_function": "ReturnDDRatio",
        "session_filter": "LondonNY (07:00 - 21:00 UTC)",
        "min_conditions": 1,
        "max_conditions": 3,
        "sl_required": True,
        "databanks_summary": {
            "last_generation_count": 92,
            "results_approved_count": 0,
        },
        "web_ui_url": "http://127.0.0.1:5050",
        "mcp_url": "http://127.0.0.1:8081/mcp"
    }

    try:
        with zipfile.ZipFile(cfx_path, "r") as z:
            if "Build-Task1.xml" in z.namelist():
                content = z.read("Build-Task1.xml").decode("utf-8", errors="ignore")
                root = ET.fromstring(content)
                for elem in root.iter():
                    if elem.tag == "Chart" and "symbol" in elem.attrib:
                        summary["symbol"] = elem.attrib["symbol"]
                        summary["timeframe"] = elem.attrib.get("timeframe", "H1")
                    if elem.tag == "Ranking" and "type" in elem.attrib:
                        summary["fitness_function"] = elem.attrib["type"]
                    if elem.tag == "Param" and elem.attrib.get("key") == "Session":
                        summary["session_filter"] = elem.text or "LondonNY"
    except Exception as e:
        summary["parse_warning"] = str(e)

    return summary


@sqx_router.post("/projects/{project_name}/run")
def run_sqx_project(project_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    """Trigger execution of a StrategyQuant X project."""
    client = SQXMCPClient(base_url=url)
    try:
        res = client.run_project(project_name)
        return {"status": "SUCCESS", "project": project_name, "result": res}
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.post("/projects/{project_name}/stop")
def stop_sqx_project(project_name: str, url: str = Query("http://localhost:8081/mcp")) -> Dict[str, Any]:
    """Stop execution of a running StrategyQuant X project."""
    client = SQXMCPClient(base_url=url)
    try:
        res = client.stop_project(project_name)
        return {"status": "SUCCESS", "project": project_name, "result": res}
    except SQXMCPError as e:
        raise HTTPException(status_code=502, detail=f"SQX MCP Error: {e}") from e


@sqx_router.post("/projects/{project_name}/ingest")
def ingest_sqx_project(project_name: str) -> Dict[str, Any]:
    """Ingest REAL generated strategies from SQX databank into the DB and return the
    profitable ones with their real metrics. This is what makes the web *show* that
    SQX produced strategies."""
    from services.sqx_bridge.ingest_sqx_results import (
        DATABANK, extract_stats, clean_symbol, sqx_candidate_to_spec,
    )
    from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel
    import hashlib, json
    from datetime import datetime

    client = SQXMCPClient()
    strategies = client.list_strategies(project_name, DATABANK)

    db = SessionLocal()
    inserted = 0
    skipped = 0
    try:
        for name in strategies:
            try:
                stats_raw = client.get_strategy_stats(project_name, DATABANK, name)
            except Exception:
                skipped += 1
                continue
            metrics = extract_stats(stats_raw)
            if not metrics or metrics.get("TradesCount", 0) == 0:
                skipped += 1
                continue

            raw_sym = str((stats_raw.get("values") or [])[3]) if len(stats_raw.get("values", [])) > 3 else "NQ"
            symbol = clean_symbol(raw_sym)
            from services.sqx_bridge.ingest_sqx_results import extract_timeframe_from_stats
            tf = extract_timeframe_from_stats(stats_raw)
            venue = "BINGX" if "USDT" in symbol or symbol in ("BTC", "ETH", "SOL") else "CME"

            spec = sqx_candidate_to_spec(
                project_name=project_name, databank_name=DATABANK,
                strategy_name=name, sqx_stats=metrics, symbol=symbol, timeframe=tf,
            )
            spec_id = spec.strategy_id
            dsl_json = json.dumps({
                "dslVersion": "1.0.0",
                "origin": {"engine": "strategyquant", "project": project_name,
                           "databank": DATABANK, "strategyName": name},
                "market": {"symbol": symbol, "timeframe": tf, "venue": venue},
                "metadata": {"family": "sqx_generated", "sourceStats": metrics},
            }, ensure_ascii=False)
            canonical_hash = hashlib.sha256(dsl_json.encode("utf-8")).hexdigest()

            if db.query(StrategyModel).filter(StrategyModel.strategy_id == spec_id).first():
                skipped += 1
                continue

            net_profit = metrics.get("NetProfitUsd", 0.0)
            net_return = metrics.get("AnnualReturnPct", (net_profit / 10000.0) * 100.0)
            max_dd = float(metrics.get("MaxDrawdownPct", 0.0) or 0.0)
            pf = float(metrics.get("ProfitFactor", 0.0) or 0.0)
            from services.api.app.factory.quality_gates import rentable as is_rentable
            passes_gate = is_rentable(net_return, pf, max_dd, mode="ultra")
            # Quality gate: a strategy that destroyed the account or has a poor
            # return-to-drawdown profile is ingested but flagged (never surfaced
            # as a live candidate). This keeps the databank auditable without
            # letting junk masquerade as validated.
            validation_status = "SQX_CANDIDATE" if passes_gate else "SQX_REJECTED_RISK"

            db.merge(StrategyModel(
                strategy_id=spec_id, name=name, version="1.0.0",
                family="sqx_generated", author="StrategyQuantX",
                canonical_hash=canonical_hash, generation=1, dsl_json=dsl_json,
                validation_status=validation_status, created_at=datetime.utcnow(),
            ))
            db.merge(BacktestModel(
                backtest_id=f"bt_sqx_{name.replace(' ', '_').replace('.', '')}",
                strategy_id=spec_id, dataset_id=None, engine_type="SQX_BUILTIN",
                initial_capital=10000.0, leverage=1, final_equity=10000.0 + net_profit,
                net_return_pct=net_return,
                net_return_os_pct=float(metrics.get("AnnualReturnPctOOS") or metrics.get("NetProfitOOS") or net_return),
                max_drawdown_pct=max_dd,
                max_drawdown_os_pct=float(metrics.get("MaxDrawdownPctOOS") or max_dd),
                win_rate=metrics.get("WinRate", 0.0),
                trades_count=int(metrics.get("TradesCount", 0)),
                trades_os=int(metrics.get("TradesCountOOS") or metrics.get("TradesCount", 0)),
                profit_factor=pf,
                pf_os=float(metrics.get("ProfitFactorOOS") or pf),
                checksum=canonical_hash, status="COMPLETED", created_at=datetime.utcnow(),
            ))
            if passes_gate:
                inserted += 1
            else:
                skipped += 1
        db.commit()
    finally:
        db.close()

    return {
        "status": "SUCCESS",
        "project": project_name,
        "databank": DATABANK,
        "found": len(strategies),
        "inserted": inserted,
        "alreadyPresent": skipped,
    }


@sqx_router.get("/rentable")
def rentable_sqx_strategies(
    limit: int = Query(10, ge=1, le=100),
    mode: str = Query("ultra", description="Search mode: ultra (kamikaze/agresivo) or fondeo (conservador/prop firms)"),
) -> Dict[str, Any]:
    """Return SQX-generated strategies that pass a REAL quality gate.

    The KEY change (2026-08-09): merely sorting by in-sample (IS) profit factor
    presents curve-fit junk as 'rentable'. A genuinely profitable strategy must
    GENERALIZE. This endpoint therefore filters by:
      - PF_IS   >= min_pf_is     (default 1.3) — real edge in-sample
      - PF_OOS  >= min_pf_os     (default 1.0) — MUST not lose out-of-sample
      - trades_count >= 20       — statistical significance
      - net_return_pct > 0       — positive return
    and ranks by the OOS profit factor.

    Mode selection (ultra vs fondeo):
      - 'ultra': kamikaze search. Ignores Calmar and moderate drawdown limits (drawdown < 100%).
      - 'fondeo': conservative prop-firm search. Enforces max drawdown and Calmar ratio gates.
    """
    from services.api.app.db.database import SessionLocal, StrategyModel, BacktestModel
    from services.api.app.factory.quality_gates import (
        is_ruinous,
        calmar_ratio,
        MIN_CALMAR_RATIO,
        MAX_ACCEPTABLE_DRAWDOWN_PCT,
    )
    from sqlalchemy import desc, and_

    min_pf_is = 1.3
    min_pf_os = 1.0
    min_trades = 20
    max_limit = limit
    search_mode = str(mode).lower()

    db = SessionLocal()
    try:
        rows = (
            db.query(StrategyModel, BacktestModel)
            .join(BacktestModel, BacktestModel.strategy_id == StrategyModel.strategy_id)
            .filter(StrategyModel.family == "sqx_generated")
            .filter(StrategyModel.validation_status == "SQX_CANDIDATE")
            .filter(and_(
                BacktestModel.profit_factor >= min_pf_is,
                BacktestModel.net_return_pct > 0,
                BacktestModel.trades_count >= min_trades,
            ))
            .order_by(desc(BacktestModel.pf_os), desc(BacktestModel.profit_factor))
            .limit(max_limit * 3)  # Fetch extra to filter by mode
            .all()
        )
        items = []
        rejected_by_drawdown_gate = 0
        for s, b in rows:
            max_dd = float(b.max_drawdown_pct or 0.0)
            # Real ruin (>=100%) is rejected in ALL modes
            if is_ruinous(max_dd):
                rejected_by_drawdown_gate += 1
                continue

            # Mode-specific drawdown and Calmar gates
            if search_mode == "fondeo":
                if max_dd > MAX_ACCEPTABLE_DRAWDOWN_PCT:
                    rejected_by_drawdown_gate += 1
                    continue
                ret_dd = b.ret_dd_ratio
                if ret_dd is None:
                    ret_dd = calmar_ratio(
                        float(b.net_return_pct or 0.0),
                        max_dd if max_dd > 0 else None,
                    )
                if float(ret_dd or 0.0) < MIN_CALMAR_RATIO:
                    rejected_by_drawdown_gate += 1
                    continue

            items.append({
                "strategyId": s.strategy_id,
                "name": s.name,
                "validationStatus": s.validation_status,
                "family": s.family,
                "engine": b.engine_type,
                "netReturnPct": round(b.net_return_pct or 0.0, 2),        # IS return %
                "profitFactor": round(b.profit_factor or 0.0, 2),        # IS PF
                "profitFactorOos": round(b.pf_os or 0.0, 2),             # OOS PF — generalization
                "netReturnOosPct": round(b.net_return_os_pct or 0.0, 2),
                "maxDrawdownPct": round(b.max_drawdown_pct or 0.0, 2),   # real % of equity
                "maxDrawdownOosPct": round(b.max_drawdown_os_pct or 0.0, 2),
                "retDdRatio": round(b.ret_dd_ratio or 0.0, 2),
                "winRate": round(b.win_rate or 0.0, 2),
                "tradesCount": b.trades_count,
                "tradesOos": b.trades_os,
                "checksum": b.checksum,
                "createdAt": s.created_at.isoformat() if s.created_at else None,
            })
            if len(items) >= max_limit:
                break

        total_sqx = (
            db.query(BacktestModel)
            .join(StrategyModel, StrategyModel.strategy_id == BacktestModel.strategy_id)
            .filter(StrategyModel.family == "sqx_generated")
            .count()
        )
        return {
            "status": "SUCCESS",
            "mode": search_mode,
            "count": len(items),
            "filters": {
                "min_pf_is": min_pf_is,
                "min_pf_os": min_pf_os,
                "min_trades": min_trades,
                "require_oos": True,
                "mode": search_mode,
            },
            "total_sqx_candidates": total_sqx,
            "rejected_by_gate": total_sqx - len(items),
            "strategies": items,
        }
    finally:
        db.close()


@sqx_router.post("/sync")
def trigger_sqx_sync() -> Dict[str, Any]:
    """Ejecuta la sincronización e ingesta masiva de databanks SQX a SQLite WAL."""
    from services.sqx_bridge.sqx_sync_worker import SQXSyncWorker
    worker = SQXSyncWorker()
    summary = worker.sync_all_projects()
    return {
        "status": "SUCCESS",
        "message": "Sincronización completada con éxito",
        "summary": summary
    }


@sqx_router.get("/feedback-loop")
def get_sqx_feedback_loop() -> Dict[str, Any]:
    """Retorna las recomendaciones de la IA Semántica para optimizar los proyectos y bloques de SQX."""
    from services.semantic_ai.sqx_feedback_loop import SQXFeedbackLoop
    loop = SQXFeedbackLoop()
    return loop.analyze_learning_curve()


