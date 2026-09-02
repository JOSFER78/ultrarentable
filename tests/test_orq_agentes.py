"""Tests for scripts/orq agent governance tools."""
from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys
import time
import pytest

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS_ORQ = REPO_ROOT / "scripts" / "orq"


def _run_cmd(cmd: list[str] | str, shell: bool = False) -> subprocess.CompletedProcess[str]:
    """Helper to run command and return UTF-8 decoded output."""
    return subprocess.run(
        cmd,
        shell=shell,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def test_syntax_ps1_and_sh():
    """(a) Validates PowerShell 5.1 syntax for all .ps1 and bash -n for .sh."""
    ps1_files = list(SCRIPTS_ORQ.glob("*.ps1"))
    assert len(ps1_files) >= 4, f"Se esperaban al menos 4 scripts .ps1, encontrados: {len(ps1_files)}"

    for ps1 in ps1_files:
        cmd = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            f"[scriptblock]::Create((Get-Content -Raw '{ps1}')) | Out-Null; $LASTEXITCODE",
        ]
        res = _run_cmd(cmd)
        assert res.returncode == 0, f"Error de sintaxis en {ps1.name}:\n{res.stderr}\n{res.stdout}"

    sh_script = SCRIPTS_ORQ / "agy_lanzar.sh"
    assert sh_script.exists(), "Falta scripts/orq/agy_lanzar.sh"

    # Buscar bash (Git Bash o bash en PATH)
    bash_bin = "bash"
    git_bash = pathlib.Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        bash_bin = str(git_bash)

    res_sh = _run_cmd([bash_bin, "-n", str(sh_script)])
    assert res_sh.returncode == 0, f"Error de sintaxis en {sh_script.name}:\n{res_sh.stderr}"

    # Validar prohibicion de codex
    content_sh = sh_script.read_text(encoding="utf-8")
    assert "codex" in content_sh.lower(), "El script agy_lanzar.sh debe contener la prohibicion explicita de codex"


def test_mcp_vacio(tmp_path: pathlib.Path):
    """(c) mcp_vacio.ps1 -ConfigDir <tmp> sobre copias con servidores previos."""
    config_dir = tmp_path / "gemini_mock"
    cfg_file = config_dir / "config" / "mcp_config.json"
    ide_file = config_dir / "antigravity-ide" / "mcp_config.json"

    cfg_file.parent.mkdir(parents=True, exist_ok=True)
    ide_file.parent.mkdir(parents=True, exist_ok=True)

    # 1. Crear ficheros mock con servidores
    cfg_file.write_text(
        json.dumps({"mcpServers": {"serverA": {"command": "cmd.exe"}, "serverB": {"command": "node.exe"}}}),
        encoding="utf-8",
    )
    ide_file.write_text(
        json.dumps({"mcpServers": {"serverC": {"command": "python.exe"}}}),
        encoding="utf-8",
    )

    script_path = SCRIPTS_ORQ / "mcp_vacio.ps1"
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-ConfigDir",
        str(config_dir),
    ]

    # Primera ejecucion: debe vaciar y crear backups
    res = _run_cmd(cmd)
    assert res.returncode == 0, f"mcp_vacio.ps1 fallo:\n{res.stderr}\n{res.stdout}"
    assert "3 servidores encontrados antes -> 0 servidores tras vaciar" in res.stdout

    # Comprobar que los ficheros ahora estan vacios
    data_cfg = json.loads(cfg_file.read_text(encoding="utf-8-sig"))
    data_ide = json.loads(ide_file.read_text(encoding="utf-8-sig"))
    assert data_cfg == {"mcpServers": {}}
    assert data_ide == {"mcpServers": {}}

    # Comprobar que existen backups fechados
    backups = list(config_dir.glob("**/mcp_config.backup_*.json"))
    assert len(backups) == 2, f"Se esperaban 2 backups, encontrados: {len(backups)}"

    # Segunda ejecucion: debe reportar 0 servidores y no fallar
    res2 = _run_cmd(cmd)
    assert res2.returncode == 0
    assert "0 servidores encontrados antes -> 0 servidores tras vaciar" in res2.stdout


def test_agy_censo_json():
    """(d) agy_censo.ps1 -Json devuelve JSON valido (lista, puede estar vacia)."""
    script_path = SCRIPTS_ORQ / "agy_censo.ps1"
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-Json",
    ]
    res = _run_cmd(cmd)
    assert res.returncode == 0, f"agy_censo.ps1 -Json fallo:\n{res.stderr}\n{res.stdout}"

    out_clean = res.stdout.strip()
    assert len(out_clean) > 0, "Salida vacia de agy_censo.ps1 -Json"

    data = json.loads(out_clean)
    assert isinstance(data, list), f"Se esperaba un list, se obtuvo {type(data).__name__}"

    if len(data) > 0:
        item = data[0]
        for key in ["pid", "hora_arranque", "worktree", "descendientes", "mb", "protegidos"]:
            assert key in item, f"Falta clave obligatoria {key} en item de censo: {item}"


def test_agy_censo_text():
    """Valida la salida legible para humanos de agy_censo.ps1."""
    script_path = SCRIPTS_ORQ / "agy_censo.ps1"
    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
    ]
    res = _run_cmd(cmd)
    assert res.returncode == 0, f"agy_censo.ps1 fallo:\n{res.stderr}\n{res.stdout}"
    assert "=== CENSO AGY" in res.stdout


def test_agy_matar_protection_tree(tmp_path: pathlib.Path):
    """(b) agy_matar.ps1 sobre un arbol real con nieto protegido (mine.py):
    - El protegido, sus descendientes y sus ancestros sobreviven.
    - Sin -Forzar, se niega a matar el arbol.
    - Con -Forzar, mata unicamente los procesos no protegidos.
    - Limpieza final de procesos de prueba.
    """
    matar_script = (SCRIPTS_ORQ / "agy_matar.ps1").resolve()

    runner_ps1 = tmp_path / "run_matar_test.ps1"
    runner_ps1.write_text(
        f"""
$ErrorActionPreference = "Stop"
$matarScript = "{str(matar_script).replace(chr(92), '/')}"

# 1. Crear script para nieto y padre
$tmpDir = "{str(tmp_path).replace(chr(92), '/')}"
$fatherScript = Join-Path $tmpDir "father.ps1"
Set-Content -Path $fatherScript -Value "
    `$n = Start-Process powershell.exe -ArgumentList '-NoProfile','-Command','Start-Sleep -Seconds 120; # mine.py' -PassThru
    Start-Sleep -Seconds 120
"

$unprotScript = Join-Path $tmpDir "unprot.ps1"
Set-Content -Path $unprotScript -Value "Start-Sleep -Seconds 120; # unprotected_brother"

# Lanzar arbol: Father (con Nieto) y Hermano no protegido
$fatherProc = Start-Process powershell.exe -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",$fatherScript -PassThru
$unprotProc = Start-Process powershell.exe -ArgumentList "-NoProfile","-ExecutionPolicy","Bypass","-File",$unprotScript -PassThru

# Esperar a que el nieto este activo en Win32_Process
$nietoPid = 0
for ($i = 0; $i -lt 15; $i++) {{
    Start-Sleep -Seconds 1
    $all = Get-CimInstance Win32_Process
    $found = $all | Where-Object {{ $_.ParentProcessId -eq $fatherProc.Id -and $_.CommandLine -match "mine\\.py" }}
    if ($found) {{
        $nietoPid = $found.ProcessId
        break
    }}
}}

if ($nietoPid -eq 0) {{
    Stop-Process -Id $fatherProc.Id, $unprotProc.Id -Force -ErrorAction SilentlyContinue
    throw "No se pudo levantar el proceso nieto con mine.py"
}}

Write-Output ("PIDS: FATHER={{0}} NIETO={{1}} UNPROT={{2}}" -f $fatherProc.Id, $nietoPid, $unprotProc.Id)

# PRUEBA 1: Sin -Forzar sobre Father -> Debe negarse por tener nieto protegido (mine.py)
$resNoForce = & $matarScript -ProcesoId $fatherProc.Id
Write-Output ("RES_NO_FORCE: " + $resNoForce)
if ($resNoForce -notmatch "Se niega a matar el arbol PID") {{
    Stop-Process -Id $fatherProc.Id, $nietoPid, $unprotProc.Id -Force -ErrorAction SilentlyContinue
    throw ("Guardarrail fallo: se esperaba negativa pero se obtuvo: " + $resNoForce)
}}

# Comprobar que Father y Nieto siguen vivos
if (-not (Get-Process -Id $fatherProc.Id -ErrorAction SilentlyContinue)) {{
    throw "Father murio en prueba sin forzar"
}}
if (-not (Get-Process -Id $nietoPid -ErrorAction SilentlyContinue)) {{
    throw "Nieto murio en prueba sin forzar"
}}

# PRUEBA 2: Matar proceso no protegido
$resUnprot = & $matarScript -ProcesoId $unprotProc.Id
Write-Output ("RES_UNPROT: " + $resUnprot)
Start-Sleep 1
if (Get-Process -Id $unprotProc.Id -ErrorAction SilentlyContinue) {{
    throw "Proceso no protegido debio morir"
}}

# PRUEBA 3: Con -Forzar sobre Father -> Nieto y Father deben sobrevivir
$resForce = & $matarScript -ProcesoId $fatherProc.Id -Forzar
Write-Output ("RES_FORCE: " + $resForce)
if ($resForce -notmatch "Aviso: Se encontraron procesos protegidos") {{
    throw ("Fallo aviso de procesos protegidos: " + $resForce)
}}

if (-not (Get-Process -Id $fatherProc.Id -ErrorAction SilentlyContinue)) {{
    throw "Father (ancestro) murio indebidamente con -Forzar"
}}
if (-not (Get-Process -Id $nietoPid -ErrorAction SilentlyContinue)) {{
    throw "Nieto (protegido) murio indebidamente con -Forzar"
}}

# Limpieza final
Stop-Process -Id $fatherProc.Id, $nietoPid -Force -ErrorAction SilentlyContinue
Write-Output "TODO_CORRECTO"
""",
        encoding="utf-8",
    )

    cmd = [
        "powershell.exe",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(runner_ps1),
    ]
    res = _run_cmd(cmd)
    assert res.returncode == 0, f"Fallo test_agy_matar_protection_tree:\n{res.stderr}\n{res.stdout}"
    assert "TODO_CORRECTO" in res.stdout


def _get_bash() -> str:
    """Helper to find bash executable."""
    git_bash = pathlib.Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        return str(git_bash)
    return "bash"


def test_esperar_worktree_success(tmp_path: pathlib.Path):
    """(3b) Valida que esperar_worktree devuelve 0 cuando .git aparece a los 4s con AGY_LANZAR_MAX_ESPERA=6."""
    import threading
    wt_test = tmp_path / "test_wt_ok"
    wt_test.mkdir(parents=True, exist_ok=True)
    git_marker = wt_test / ".git"

    def _create_git():
        time.sleep(4)
        git_marker.mkdir(parents=True, exist_ok=True)

    t = threading.Thread(target=_create_git, daemon=True)
    t.start()

    sh_script = SCRIPTS_ORQ / "agy_lanzar.sh"
    bash_bin = _get_bash()
    env = os.environ.copy()
    env["AGY_LANZAR_MAX_ESPERA"] = "6"

    cmd = [bash_bin, str(sh_script), "--test-esperar-worktree", str(wt_test).replace("\\", "/")]
    t0 = time.time()
    res = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - t0
    assert res.returncode == 0, f"esperar_worktree debio retornar 0 al aparecer .git a los 4s:\n{res.stderr}\n{res.stdout}"
    assert elapsed >= 3.5, f"La espera debio durar al menos ~4s, duro {elapsed:.2f}s"
    assert git_marker.exists()


def test_esperar_worktree_timeout(tmp_path: pathlib.Path):
    """(3b) Valida que esperar_worktree devuelve rc!=0 cuando .git no aparece en 6s con AGY_LANZAR_MAX_ESPERA=6."""
    wt_test = tmp_path / "test_wt_timeout"
    wt_test.mkdir(parents=True, exist_ok=True)

    sh_script = SCRIPTS_ORQ / "agy_lanzar.sh"
    bash_bin = _get_bash()
    env = os.environ.copy()
    env["AGY_LANZAR_MAX_ESPERA"] = "6"

    cmd = [bash_bin, str(sh_script), "--test-esperar-worktree", str(wt_test).replace("\\", "/")]
    t0 = time.time()
    res = subprocess.run(
        cmd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - t0
    assert res.returncode != 0, f"esperar_worktree debio retornar rc!=0 por timeout, retorno {res.returncode}"
    assert elapsed >= 5.0, f"La espera debio durar al menos ~6s antes de fallar por timeout, duro {elapsed:.2f}s"


def test_registrar_agente_json(tmp_path: pathlib.Path):
    """(3c) Valida que registrar_agente_json genera un registro JSON valido con todas las claves de telemetria."""
    out_file = tmp_path / "agentes.jsonl"
    sh_script = SCRIPTS_ORQ / "agy_lanzar.sh"
    bash_bin = _get_bash()

    cmd = [
        bash_bin,
        str(sh_script),
        "--test-registrar-json",
        str(out_file).replace("\\", "/"),
        "B19",
        "2026-09-02 18:00:00",
        "12345",
        "C:/Users/yo/orca/workspaces/ultrarentable/agy-B19",
        "10",
        "2",
        "8",
        "12",
        "1",
        "33",
        "3",
        "320",
        "false",
        "task_c79771f2d5b7",
        "ctx_cc6db4af99f7",
        "term_8b4cb2c1-dfa5-40bc-b2fb-cf91c777032d",
        "0",
    ]
    res = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    assert res.returncode == 0, f"Error al ejecutar registrar_agente_json:\n{res.stderr}\n{res.stdout}"
    assert out_file.exists(), "No se creo el fichero agentes.jsonl"

    content = out_file.read_text(encoding="utf-8").strip()
    assert len(content) > 0, "El fichero agentes.jsonl esta vacio"
    data = json.loads(content)

    required_keys = [
        "id",
        "hora",
        "pid",
        "worktree",
        "t_worktree",
        "t_terminal",
        "t_banner",
        "t_idle",
        "t_start",
        "t_total",
        "hijos",
        "mb",
        "reintento_prompt",
        "task",
        "dispatch",
        "terminal",
        "hijos_no_shell",
    ]
    for k in required_keys:
        assert k in data, f"Falta clave obligatoria '{k}' en registro JSON: {data}"

    assert data["id"] == "B19"
    assert data["pid"] == 12345
    assert data["t_total"] == 33
    assert data["reintento_prompt"] is False
    assert isinstance(data["reintento_prompt"], bool), "reintento_prompt debe ser tipo bool nativo en JSON"
    assert data["hijos_no_shell"] == 0


def test_lanzar_patrones_endurecidos():
    """Valida la presencia de patrones de endurecimiento clave en agy_lanzar.sh."""
    sh_script = SCRIPTS_ORQ / "agy_lanzar.sh"
    content = sh_script.read_text(encoding="utf-8")
    for pattern in ["How's the CLI experience", "task-update", "t_total", ".git"]:
        assert pattern in content, f"Falta patron clave '{pattern}' en {sh_script.name}"

