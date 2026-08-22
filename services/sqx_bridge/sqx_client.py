"""StrategyQuant X MCP Client for Ultra Rentable V2.

100% Real HTTP JSON-RPC Client connecting directly to StrategyQuant X MCP Server.

SQX RUNS ON THE VPS (24/7): installed at /home/ubuntu/StrategyQuantX, managed
as systemd user service `strategyquantx.service` (DISPLAY=:99 / Xvfb), MCP
listening at http://127.0.0.1:8080/mcp. NO SSH tunnel needed — same machine.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error
from typing import Any, Dict, List, Optional


class SQXMCPError(Exception):
    """Exception raised for errors during SQX MCP server interaction."""
    pass


import os


class SQXMCPClient:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 15):
        self.base_url = (base_url or os.getenv("SQX_MCP_URL", "http://127.0.0.1:8081/mcp")).rstrip("/")
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _parse_sse_body(self, body: str) -> Dict[str, Any]:
        clean_body = body
        if "data: " in body:
            for line in body.split("\n"):
                if line.startswith("data: "):
                    clean_body = line[6:].strip()
                    break
        try:
            return json.loads(clean_body)
        except json.JSONDecodeError as e:
            raise SQXMCPError(f"Invalid JSON from SQX MCP: {clean_body}") from e

    def initialize(self) -> Dict[str, Any]:
        """Establish MCP session with StrategyQuant X server."""
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "Antigravity-UltraRentableV2", "version": "2.0.0"}
            }
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            self.base_url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "Accept": "text/event-stream, application/json"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                self.session_id = resp.headers.get("mcp-session-id")
                body = resp.read().decode("utf-8")
                parsed = self._parse_sse_body(body)
                if "error" in parsed:
                    raise SQXMCPError(f"Initialization error: {parsed['error']}")
                return parsed.get("result", {})
        except urllib.error.URLError as e:
            raise SQXMCPError(f"Failed to connect to SQX MCP at {self.base_url}: {e.reason}") from e

    def _call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None, retry: bool = True) -> Any:
        """Call an MCP tool on StrategyQuant X with auto-session initialization."""
        if not self.session_id:
            self.initialize()

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json"
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        req = urllib.request.Request(self.base_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                parsed = self._parse_sse_body(body)
                if "error" in parsed:
                    if retry and "session" in str(parsed.get("error", "")).lower():
                        self.session_id = None
                        return self._call_tool(tool_name, arguments, retry=False)
                    raise SQXMCPError(f"Tool {tool_name} returned RPC error: {parsed['error']}")
                
                result = parsed.get("result", {})
                content_list = result.get("content", [])
                if content_list and isinstance(content_list, list):
                    first_text = content_list[0].get("text", "")
                    try:
                        return json.loads(first_text)
                    except json.JSONDecodeError:
                        return first_text
                return result
        except urllib.error.URLError as e:
            if retry:
                self.session_id = None
                return self._call_tool(tool_name, arguments, retry=False)
            raise SQXMCPError(f"Error calling {tool_name}: {e.reason}") from e

    def check_connection(self) -> Dict[str, Any]:
        """Verify connection status with SQX MCP server with fast 200ms socket probe."""
        import socket
        from urllib.parse import urlparse
        try:
            parsed = urlparse(self.base_url)
            host = parsed.hostname or "127.0.0.1"
            port = parsed.port or 8081

            # Fast socket probe (200ms)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.2)
            res = sock.connect_ex((host, port))
            sock.close()
            if res != 0:
                return {"status": "OFFLINE", "base_url": self.base_url, "error": "Port unreachable"}

            info = self.initialize()
            return {
                "status": "ONLINE",
                "base_url": self.base_url,
                "session_id": self.session_id,
                "server_info": info.get("serverInfo", {}),
                "capabilities": info.get("capabilities", {})
            }
        except Exception as e:
            return {
                "status": "OFFLINE",
                "base_url": self.base_url,
                "error": str(e)
            }

    def list_tools(self) -> List[Dict[str, Any]]:
        """Discover available MCP tools on the StrategyQuant X server."""
        if not self.session_id:
            self.initialize()

        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/list",
            "params": {}
        }
        data = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Accept": "text/event-stream, application/json"
        }
        if self.session_id:
            headers["mcp-session-id"] = self.session_id

        req = urllib.request.Request(self.base_url, data=data, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                body = resp.read().decode("utf-8")
                parsed = self._parse_sse_body(body)
                if "error" in parsed:
                    raise SQXMCPError(f"tools/list error: {parsed['error']}")
                result = parsed.get("result", {})
                return result.get("tools", [])
        except urllib.error.URLError as e:
            raise SQXMCPError(f"Error listing tools: {e.reason}") from e

    def list_projects(self) -> List[Dict[str, Any]]:
        """List all available projects in StrategyQuant X."""
        res = self._call_tool("list_projects")
        if isinstance(res, dict) and "projects" in res:
            return res["projects"]
        return res if isinstance(res, list) else []

    def list_databanks(self, project_name: str) -> List[Dict[str, Any]]:
        """List all databanks in a StrategyQuant X project."""
        res = self._call_tool("list_databanks", {"name": project_name})
        if isinstance(res, dict) and "databanks" in res:
            return res["databanks"]
        return res if isinstance(res, list) else []

    def list_strategies(self, project_name: str, databank_name: str) -> List[Dict[str, Any]]:
        """List all strategies in a specific databank of a project."""
        res = self._call_tool("list_strategies", {"name": project_name, "databank": databank_name})
        if isinstance(res, dict) and "strategies" in res:
            return res["strategies"]
        return res if isinstance(res, list) else []

    def get_strategy_stats(self, project_name: str, databank_name: str, strategy_name: str) -> Dict[str, Any]:
        """Get statistics and metrics for a specific strategy in a databank."""
        return self._call_tool("get_strategy_stats", {
            "name": project_name,
            "databank": databank_name,
            "strategy": strategy_name
        })

    def run_project(self, project_name: str) -> Dict[str, Any]:
        """Start a project execution in StrategyQuant X."""
        return self._call_tool("run_project", {"name": project_name})

    def stop_project(self, project_name: str) -> Dict[str, Any]:
        """Stop a running project in StrategyQuant X."""
        return self._call_tool("stop_project", {"name": project_name})
