"""StrategyQuant X client — real sqcli HTTP API on :5050, fail-closed source access.

Protocol (verified live against sqcli headless, see skill sqx-headless-workflow):
- GET http://localhost:5050/call?cmd=<cmd with spaces -> %20 only>
- Plain-text responses. `=` and other chars pass through unencoded.
- `-project action=status name=X` / `-databank action=list project=X` /
  `-databank action=count|export project=X name=Y file=/tmp/z.csv` (export writes CSV).
"""
from __future__ import annotations

import csv
import os
import re
import tempfile
from typing import Any, Dict, List, Optional

import requests


class SQXMCPError(Exception):
    pass


DEFAULT_SQX_API_URL = os.getenv("SQX_API_URL", "http://localhost:5050")
SQX_TIMEOUT = int(os.getenv("SQX_TIMEOUT", "10"))


class SQXMCPClient:
    """Minimal real client for the sqcli HTTP API (`/call?cmd=...`)."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = SQX_TIMEOUT):
        raw = base_url or os.getenv("SQX_MCP_URL", "") or DEFAULT_SQX_API_URL
        # Legacy MCP URLs are dead; map any /mcp host:port to the real sqcli API.
        if raw.rstrip("/").endswith("/mcp"):
            raw = raw.rstrip("/")[: -len("/mcp")]
        self.base_url = raw.rstrip("/")
        self.timeout = timeout

    # ── transport ────────────────────────────────────────────────
    def call(self, cmd: str, timeout: Optional[int] = None) -> str:
        url = f"{self.base_url}/call?cmd=" + cmd.replace(" ", "%20")
        try:
            resp = requests.get(url, timeout=timeout or self.timeout)
        except requests.RequestException as exc:
            raise SQXMCPError(f"SQX unreachable at {self.base_url}: {exc}") from exc
        if resp.status_code != 200:
            raise SQXMCPError(f"SQX HTTP {resp.status_code}: {resp.text[:200]}")
        return resp.text

    def check_connection(self) -> Dict[str, Any]:
        try:
            text = self.call("-project action=list")
        except SQXMCPError as exc:
            return {"status": "OFFLINE", "base_url": self.base_url, "error": str(exc)}
        return {
            "status": "ONLINE",
            "base_url": self.base_url,
            "projects": re.findall(r"^(.+)$", text, re.M)[:0] or self._parse_project_list(text),
        }

    # ── parsing helpers (plain text, simple regex) ───────────────
    @staticmethod
    def _parse_project_list(text: str) -> List[str]:
        names: List[str] = []
        started = False
        for line in text.splitlines():
            if "-" * 20 in line:
                if started:
                    break
                started = True
                continue
            if started and line.strip():
                names.append(line.strip())
        return names

    @staticmethod
    def _parse_databank_list(text: str) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for line in text.splitlines():
            m = re.match(r"^(.*?),\s*Records:\s*(\d+)\s*$", line.strip())
            if m:
                out.append({"name": m.group(1).strip(), "records": int(m.group(2))})
        return out

    # ── commands ─────────────────────────────────────────────────
    def list_projects(self) -> List[str]:
        return self._parse_project_list(self.call("-project action=list"))

    def project_exists(self, project_name: str) -> bool:
        return project_name in self.list_projects()

    def list_databanks(self, project_name: str) -> List[Dict[str, Any]]:
        return self._parse_databank_list(self.call(f"-databank action=list project={project_name}"))

    def databank_count(self, project_name: str, databank_name: str) -> int:
        text = self.call(f"-databank action=count project={project_name} name={databank_name}")
        m = re.search(r"Records:\s*(\d+)", text)
        return int(m.group(1)) if m else 0

    def export_databank(self, project_name: str, databank_name: str, max_rows: int = 500) -> List[Dict[str, Any]]:
        """Export databank to a temp CSV and parse rows (semicolon-separated, quoted)."""
        fd, path = tempfile.mkstemp(prefix="sqx_export_", suffix=".csv")
        os.close(fd)
        try:
            text = self.call(
                f"-databank action=export project={project_name} name={databank_name} file={path}",
                timeout=60,
            )
            if "exported" not in text.lower():
                raise SQXMCPError(f"SQX export failed: {text[:200]}")
            if not os.path.exists(path) or os.path.getsize(path) == 0:
                return []
            with open(path, newline="", encoding="utf-8-sig", errors="replace") as fh:
                sample = fh.read(4096)
                fh.seek(0)
                delim = ";" if sample.count(";") >= sample.count(",") else ","
                rows = list(csv.DictReader(fh, delimiter=delim))
            return rows[:max_rows]
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

    def list_strategies(self, project_name: str, databank_name: str) -> List[Dict[str, Any]]:
        return self.export_databank(project_name, databank_name)

    def get_strategy_stats(self, project_name: str, databank_name: str, strategy_name: str) -> Dict[str, Any]:
        for row in self.export_databank(project_name, databank_name):
            if str(row.get("Strategy Name", "")).strip() == strategy_name:
                return row
        raise SQXMCPError(f"Strategy '{strategy_name}' not found in {project_name}/{databank_name}")

    def run_project(self, project_name: str) -> Dict[str, Any]:
        return {"output": self.call(f"-project action=start name={project_name}")}

    def stop_project(self, project_name: str) -> Dict[str, Any]:
        return {"output": self.call(f"-project action=stop name={project_name}")}

    def initialize(self) -> Dict[str, Any]:
        return self.check_connection()

    def list_tools(self) -> List[Dict[str, Any]]:
        return []

    def get_strategy_source(self, project_name: str, databank_name: str, strategy_name: str) -> Dict[str, Any]:
        return {
            "status": "SOURCE_RULES_UNAVAILABLE",
            "reason": "sqcli HTTP API does not expose strategy source export",
            "project": project_name,
            "databank": databank_name,
            "strategy": strategy_name,
        }
