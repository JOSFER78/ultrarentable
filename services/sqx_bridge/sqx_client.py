"""StrategyQuant X MCP client — real HTTP JSON-RPC, fail-closed source access."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional


class SQXMCPError(Exception):
    pass


class SQXMCPClient:
    def __init__(self, base_url: Optional[str] = None, timeout: int = 15):
        self.base_url = (base_url or os.getenv("SQX_MCP_URL", "http://127.0.0.1:8080/mcp")).rstrip("/")
        self.timeout = timeout
        self.session_id: Optional[str] = None
        self._request_id = 0

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _parse_sse_body(self, body: str) -> Dict[str, Any]:
        clean_body = body
        for line in body.split("\n"):
            if line.startswith("data: "):
                clean_body = line[6:].strip()
                break
        try:
            return json.loads(clean_body)
        except json.JSONDecodeError as exc:
            raise SQXMCPError(f"Invalid JSON from SQX MCP: {clean_body}") from exc

    def initialize(self) -> Dict[str, Any]:
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "UltrarentableStrategyLab", "version": "1.0.0"},
            },
        }
        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "text/event-stream, application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                self.session_id = resp.headers.get("mcp-session-id")
                parsed = self._parse_sse_body(resp.read().decode("utf-8"))
                if "error" in parsed:
                    raise SQXMCPError(f"Initialization error: {parsed['error']}")
                return parsed.get("result", {})
        except urllib.error.URLError as exc:
            raise SQXMCPError(f"Failed to connect to SQX MCP at {self.base_url}: {exc.reason}") from exc

    def _call_tool(self, tool_name: str, arguments: Optional[Dict[str, Any]] = None, retry: bool = True) -> Any:
        if not self.session_id:
            self.initialize()
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
        }
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream, application/json"}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        req = urllib.request.Request(self.base_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                parsed = self._parse_sse_body(resp.read().decode("utf-8"))
                if "error" in parsed:
                    if retry and "session" in str(parsed.get("error", "")).lower():
                        self.session_id = None
                        return self._call_tool(tool_name, arguments, retry=False)
                    raise SQXMCPError(f"Tool {tool_name} returned RPC error: {parsed['error']}")
                result = parsed.get("result", {})
                content_list = result.get("content", [])
                if isinstance(content_list, list) and content_list:
                    first_text = content_list[0].get("text", "")
                    try:
                        return json.loads(first_text)
                    except json.JSONDecodeError:
                        return first_text
                return result
        except urllib.error.URLError as exc:
            if retry:
                self.session_id = None
                return self._call_tool(tool_name, arguments, retry=False)
            raise SQXMCPError(f"Error calling {tool_name}: {exc.reason}") from exc

    def check_connection(self) -> Dict[str, Any]:
        import socket
        from urllib.parse import urlparse
        try:
            parsed = urlparse(self.base_url)
            host, port = parsed.hostname or "127.0.0.1", parsed.port or 8080
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            res = sock.connect_ex((host, port))
            sock.close()
            if res != 0:
                return {"status": "OFFLINE", "base_url": self.base_url, "error": "Port unreachable"}
            info = self.initialize()
            return {"status": "ONLINE", "base_url": self.base_url, "session_id": self.session_id, "server_info": info.get("serverInfo", {}), "capabilities": info.get("capabilities", {})}
        except Exception as exc:
            return {"status": "OFFLINE", "base_url": self.base_url, "error": str(exc)}

    def list_tools(self) -> List[Dict[str, Any]]:
        if not self.session_id:
            self.initialize()
        payload = {"jsonrpc": "2.0", "id": self._next_id(), "method": "tools/list", "params": {}}
        headers = {"Content-Type": "application/json", "Accept": "text/event-stream, application/json"}
        if self.session_id:
            headers["mcp-session-id"] = self.session_id
        req = urllib.request.Request(self.base_url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                parsed = self._parse_sse_body(resp.read().decode("utf-8"))
                if "error" in parsed:
                    raise SQXMCPError(f"tools/list error: {parsed['error']}")
                return parsed.get("result", {}).get("tools", [])
        except urllib.error.URLError as exc:
            raise SQXMCPError(f"Error listing tools: {exc.reason}") from exc

    def _find_tool(self, candidates: List[str]) -> Optional[str]:
        available = {str(item.get("name")) for item in self.list_tools() if isinstance(item, dict) and item.get("name")}
        for name in candidates:
            if name in available:
                return name
        return None

    def get_strategy_source(self, project_name: str, databank_name: str, strategy_name: str) -> Dict[str, Any]:
        """Return source only when SQX explicitly advertises a source-export tool."""
        tool = self._find_tool(["get_strategy_source", "get_strategy_xml", "export_strategy", "get_strategy_code"])
        if not tool:
            return {"status": "SOURCE_RULES_UNAVAILABLE", "reason": "SQX MCP does not advertise a strategy-source export tool", "project": project_name, "databank": databank_name, "strategy": strategy_name}
        result = self._call_tool(tool, {"name": project_name, "databank": databank_name, "strategy": strategy_name})
        if not result:
            return {"status": "SOURCE_RULES_UNAVAILABLE", "reason": "SQX returned no source payload", "project": project_name, "databank": databank_name, "strategy": strategy_name}
        payload = result if isinstance(result, (dict, list, str)) else str(result)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) if not isinstance(payload, str) else payload
        import hashlib
        return {"status": "SUCCESS", "tool": tool, "project": project_name, "databank": databank_name, "strategy": strategy_name, "source": payload, "source_sha256": hashlib.sha256(encoded.encode("utf-8")).hexdigest()}

    def list_projects(self) -> List[Dict[str, Any]]:
        res = self._call_tool("list_projects")
        return res.get("projects", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])

    def list_databanks(self, project_name: str) -> List[Dict[str, Any]]:
        res = self._call_tool("list_databanks", {"name": project_name})
        return res.get("databanks", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])

    def list_strategies(self, project_name: str, databank_name: str) -> List[Dict[str, Any]]:
        res = self._call_tool("list_strategies", {"name": project_name, "databank": databank_name})
        return res.get("strategies", []) if isinstance(res, dict) else (res if isinstance(res, list) else [])

    def get_strategy_stats(self, project_name: str, databank_name: str, strategy_name: str) -> Dict[str, Any]:
        return self._call_tool("get_strategy_stats", {"name": project_name, "databank": databank_name, "strategy": strategy_name})

    def run_project(self, project_name: str) -> Dict[str, Any]:
        return self._call_tool("run_project", {"name": project_name})

    def stop_project(self, project_name: str) -> Dict[str, Any]:
        return self._call_tool("stop_project", {"name": project_name})
