"""StrategyQuant X client — real sqcli HTTP API on :5050, fail-closed source access.

Protocol (verified live against sqcli headless, see skill sqx-headless-workflow):
- GET http://localhost:5050/call?cmd=<cmd with spaces -> %20 only>
- Plain-text responses. `=` and other chars pass through unencoded.
- `-project action=status name=X` / `-databank action=list project=X` /
  `-databank action=count|export project=X name=Y file=/tmp/z.csv` (export writes CSV).
"""
from __future__ import annotations

import csv
import io
import os
import re
import tempfile
from typing import Any, Dict, List, Optional

import requests


class SQXMCPError(Exception):
    pass


DEFAULT_SQX_API_URL = os.getenv("SQX_API_URL", "http://127.0.0.1:5051")
DEFAULT_SQX_RESULTS_URL = os.getenv("SQX_RESULTS_URL", "http://127.0.0.1:5052")
SQX_TIMEOUT = int(os.getenv("SQX_TIMEOUT", "10"))


class SQXMCPClient:
    """Minimal real client for the sqcli HTTP API (`/call?cmd=...`)."""

    def __init__(self, base_url: Optional[str] = None, timeout: int = SQX_TIMEOUT, results_url: Optional[str] = None):
        raw = base_url or os.getenv("SQX_MCP_URL", "") or os.getenv("SQX_API_URL", "") or DEFAULT_SQX_API_URL
        # Legacy MCP URLs are dead; map any /mcp host:port to the real sqcli API.
        if raw.rstrip("/").endswith("/mcp"):
            raw = raw.rstrip("/")[: -len("/mcp")]
        self.base_url = raw.rstrip("/")
        self.results_url = (results_url or os.getenv("SQX_RESULTS_URL", "") or DEFAULT_SQX_RESULTS_URL).rstrip("/")
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

    def call_cli(self, cmd: str, timeout: Optional[int] = None) -> str:
        """Execute command via temporary script file `-run file=<path>` on sqcli.

        This bypasses the URL tokenizer limitation in sqcli HTTP servlet,
        allowing parameters with spaces in quotes (e.g. name="Last generation").
        """
        fd, path = tempfile.mkstemp(prefix="sqx_cmd_", suffix=".txt")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                f.write(cmd + "\n")
            return self.call(f"-run file={path}", timeout=timeout or 120)
        finally:
            try:
                os.remove(path)
            except OSError:
                pass

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
        for db in self.list_databanks(project_name):
            if db.get("name") == databank_name:
                return int(db.get("records", 0))
        return 0

    def export_databank(self, project_name: str, databank_name: str, max_rows: int = 500) -> List[Dict[str, Any]]:
        """Export databank and parse rows (semicolon-separated, quoted).

        Uses direct HTTP serving via port 5052 from /opt/SQX-headless/import/fondeo/resultados/,
        supporting pre-calculated M1 runner CSVs and ad-hoc remote exports with 0 cross-OS path failures.
        """
        # 1. Si es el banco 'Results' y existe un CSV de rondas M1 ya consolidado, leerlo directamente
        if databank_name == "Results":
            for r in [4, 3, 2, 1]:
                candidate_url = f"{self.results_url}/resultados/{project_name}_r{r}.csv"
                try:
                    head_resp = requests.head(candidate_url, timeout=3)
                    if head_resp.status_code == 200:
                        resp = requests.get(candidate_url, timeout=60)
                        if resp.status_code == 200 and len(resp.text) > 50:
                            sample = resp.text[:4096]
                            delim = ";" if sample.count(";") >= sample.count(",") else ","
                            rows = list(csv.DictReader(io.StringIO(resp.text), delimiter=delim))
                            if rows:
                                return rows[:max_rows]
                except Exception:
                    pass

        # 2. Exportación bajo demanda en el servidor remoto
        safe_db = re.sub(r"[^a-zA-Z0-9_-]", "_", databank_name)
        filename = f"sqx_export_{project_name}_{safe_db}.csv"
        remote_path = f"/opt/SQX-headless/import/fondeo/resultados/{filename}"

        if " " in databank_name or '"' in databank_name:
            cmd_content = f'-databank action=export project={project_name} name="{databank_name}" file={remote_path}'
            ssh_cmd = f"echo '{cmd_content}' > /tmp/sqx_cmd.txt && curl -s 'http://127.0.0.1:5051/call?cmd=-run%20file=/tmp/sqx_cmd.txt'"
            try:
                import subprocess
                subprocess.check_output(['ssh', '-o', 'BatchMode=yes', '-o', 'ConnectTimeout=10', 'sqx-hetzner', ssh_cmd], timeout=120)
            except Exception as exc:
                raise SQXMCPError(f"Error al ejecutar exportación remota en SQX: {exc}") from exc
        else:
            cmd = f"-databank action=export project={project_name} name={databank_name} file={remote_path}"
            out = self.call(cmd, timeout=120)
            if "exported" not in out.lower():
                raise SQXMCPError(f"SQX export failed: {out[:200]}")

        # 3. Descarga y parsing vía puerto 5052
        download_url = f"{self.results_url}/resultados/{filename}"
        try:
            dl_resp = requests.get(download_url, timeout=60)
            if dl_resp.status_code != 200:
                raise SQXMCPError(f"No se pudo descargar CSV exportado desde {download_url}: HTTP {dl_resp.status_code}")
            sample = dl_resp.text[:4096]
            delim = ";" if sample.count(";") >= sample.count(",") else ","
            rows = list(csv.DictReader(io.StringIO(dl_resp.text), delimiter=delim))
            return rows[:max_rows]
        except Exception as exc:
            if isinstance(exc, SQXMCPError):
                raise
            raise SQXMCPError(f"Error descargando datos exportados de SQX: {exc}") from exc

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
