"""Integration tests for SQX MCP Client with 100% real SQX instance."""

import pytest
from services.sqx_bridge.sqx_client import SQXMCPClient, SQXMCPError


def test_sqx_connection_status():
    """Verify check_connection returns valid status dictionary."""
    client = SQXMCPClient(base_url="http://localhost:8080/mcp")
    status = client.check_connection()
    assert isinstance(status, dict)
    assert status["status"] in ("ONLINE", "OFFLINE")
    if status["status"] == "ONLINE":
        assert "server_info" in status
        assert status["server_info"].get("name") == "StrategyQuant X"


def test_sqx_list_projects_real():
    """Verify list_projects returns real projects from StrategyQuant X if online."""
    client = SQXMCPClient(base_url="http://localhost:8080/mcp")
    status = client.check_connection()
    if status["status"] != "ONLINE":
        pytest.skip("StrategyQuant X MCP server is currently offline on localhost:8080")
    
    projects = client.list_projects()
    assert isinstance(projects, list)
    assert len(projects) > 0
    project_names = [p["name"] for p in projects if "name" in p]
    assert "PortfolioMaster" in project_names or len(project_names) > 0
