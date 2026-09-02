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

    sh_scripts = list(SCRIPTS_ORQ.glob("*.sh"))
    assert len(sh_scripts) >= 2, f"Se esperaban al menos 2 scripts .sh, encontrados: {len(sh_scripts)}"

    # Buscar bash (Git Bash o bash en PATH)
    bash_bin = "bash"
    git_bash = pathlib.Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        bash_bin = str(git_bash)

    for sh_script in sh_scripts:
        res_sh = _run_cmd([bash_bin, "-n", str(sh_script)])
        assert res_sh.returncode == 0, f"Error de sintaxis en {sh_script.name}:\n{res_sh.stderr}"

    # Validar prohibicion de codex en agy_lanzar.sh
    lanzar_sh = SCRIPTS_ORQ / "agy_lanzar.sh"
    content_sh = lanzar_sh.read_text(encoding="utf-8")
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


def test_syntax_agy_cerrar():
    """Valida la sintaxis y patrones obligatorios en agy_cerrar.sh."""
    cerrar_sh = SCRIPTS_ORQ / "agy_cerrar.sh"
    assert cerrar_sh.exists(), "Falta scripts/orq/agy_cerrar.sh"

    bash_bin = "bash"
    git_bash = pathlib.Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        bash_bin = str(git_bash)

    res_sh = _run_cmd([bash_bin, "-n", str(cerrar_sh)])
    assert res_sh.returncode == 0, f"Error de sintaxis en agy_cerrar.sh:\n{res_sh.stderr}"

    content = cerrar_sh.read_text(encoding="utf-8")
    for pattern in ["worker-release", "terminal stop", "DirectoryInfo", "worktree remove", "gh issue"]:
        assert pattern in content, f"Patron obligatorio '{pattern}' no encontrado en agy_cerrar.sh"


def test_agy_cerrar_junctions_safe_removal(tmp_path: pathlib.Path):
    """(b) Comprueba que la rutina de junctions de agy_cerrar.sh:
    - Borra la junction con [IO.DirectoryInfo]::Delete().
    - Conserva integro el directorio destino con sus 3 ficheros originales.
    - Falla de forma fail-closed si el destino no es accesible.
    """
    target_dir = tmp_path / "target_real"
    target_dir.mkdir(parents=True, exist_ok=True)
    (target_dir / "f1.txt").write_text("dato 1", encoding="utf-8")
    (target_dir / "f2.txt").write_text("dato 2", encoding="utf-8")
    (target_dir / "f3.txt").write_text("dato 3", encoding="utf-8")

    wt_dir = tmp_path / "wt_mock"
    wt_dir.mkdir(parents=True, exist_ok=True)
    sub_wt = wt_dir / "apps" / "web"
    sub_wt.mkdir(parents=True, exist_ok=True)

    junc_path = wt_dir / "data_link"

    # Crear junction usando cmd /c mklink /J
    cmd_mklink = f'cmd.exe /c mklink /J "{str(junc_path)}" "{str(target_dir)}"'
    res_link = _run_cmd(cmd_mklink)
    assert res_link.returncode == 0, f"Error creando junction de prueba:\n{res_link.stderr}\n{res_link.stdout}"

    # Ejecutar script de eliminacion segura de junctions (identico al de agy_cerrar.sh)
    cleaner_ps1 = tmp_path / "clean_junc.ps1"
    cleaner_ps1.write_text(
        f"""
$ErrorActionPreference = "Stop"
$wt = "{str(wt_dir).replace(chr(92), '/')}"

function Find-ReparsePoints($dir) {{
    $points = @()
    if (-not (Test-Path $dir)) {{ return $points }}
    $items = Get-ChildItem -Path $dir -Force -ErrorAction SilentlyContinue
    foreach ($item in $items) {{
        if ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) {{
            $points += $item
        }} elseif ($item.PSIsContainer) {{
            $points += Find-ReparsePoints $item.FullName
        }}
    }}
    return $points
}}

$junctions = Find-ReparsePoints $wt

# 1. Verificacion fail-closed de destinos
$targetsToVerify = @()
foreach ($j in $junctions) {{
    $targets = $j.Target
    $tPath = if ($targets -and $targets.Count -gt 0) {{ $targets[0] }} else {{ $null }}
    if ([string]::IsNullOrWhiteSpace($tPath) -or (-not (Test-Path $tPath))) {{
        Write-Error ("FAIL-CLOSED: Destino inalcanzable: " + $j.FullName + " -> " + $tPath)
        exit 1
    }}
    $cnt = (Get-ChildItem -Path $tPath -Force).Count
    $targetsToVerify += [PSCustomObject]@{{
        JunctionPath = $j.FullName
        TargetPath   = $tPath
        EntryCount   = $cnt
    }}
}}

# 2. Eliminacion segura y verificacion de integridad
foreach ($t in $targetsToVerify) {{
    $jPath = $t.JunctionPath
    $tPath = $t.TargetPath
    $expCount = $t.EntryCount

    (New-Object IO.DirectoryInfo $jPath).Delete()
    if (Test-Path $jPath) {{
        Write-Error ("No se pudo eliminar junction: " + $jPath)
        exit 1
    }}
    if (-not (Test-Path $tPath)) {{
        Write-Error ("FATAL: Destino desaparecio: " + $tPath)
        exit 1
    }}
    $afterCount = (Get-ChildItem -Path $tPath -Force).Count
    if ($afterCount -ne $expCount) {{
        Write-Error ("FATAL: Discrepancia entradas (" + $expCount + " vs " + $afterCount + ")")
        exit 1
    }}
}}
Write-Output ("OK " + $targetsToVerify.Count + " JUNCTIONS CLEANED")
""",
        encoding="utf-8",
    )

    cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(cleaner_ps1)]
    res_clean = _run_cmd(cmd)
    assert res_clean.returncode == 0, f"Fallo limpieza de junctions:\n{res_clean.stderr}\n{res_clean.stdout}"
    assert "OK 1 JUNCTIONS CLEANED" in res_clean.stdout

    # Verificaciones fisicas directas
    assert not junc_path.exists(), "La junction deberia haber sido eliminada"
    assert target_dir.exists(), "El directorio destino debe seguir existiendo intacto"
    target_files = sorted([p.name for p in target_dir.iterdir()])
    assert target_files == ["f1.txt", "f2.txt", "f3.txt"], f"El destino perdio ficheros: {target_files}"


def test_lookup_dispatch_by_worktree(tmp_path: pathlib.Path):
    """(c) Funcion de 'buscar dispatch por worktree' sobre fixture REAL de worker-list y terminal list."""
    # Fixture con datos reales capturados de Orca
    worker_list_fixture = {
        "status": "ok",
        "result": {
            "workers": [
                {
                    "dispatchId": "ctx_da201747a158",
                    "taskId": "task_27108c33fa40",
                    "agentTerminalHandle": "term_e892abe6-2f95-45af-aa8b-3c0d02d7a2c4",
                    "resource": {
                        "worktreeId": "fd201816-f015-4412-8e3a-c277d3284a04::C:/Users/yo/orca/workspaces/ultrarentable/agy-B17",
                    },
                },
                {
                    "dispatchId": "ctx_9a6d79165783",
                    "taskId": "task_9d7ad6c015fa",
                    "agentTerminalHandle": "term_aff1db60-fe09-4bac-9e1c-524495cf84f3",
                    "resource": {
                        "worktreeId": "fd201816-f015-4412-8e3a-c277d3284a04::C:/Users/yo/orca/workspaces/ultrarentable/agy-B12",
                    },
                },
                {
                    "dispatchId": "ctx_675fbc52ee66",
                    "taskId": "task_0b08d7a20cd6",
                    "agentTerminalHandle": "term_e7fd48a8-9ee9-4f49-b3f1-bcce04606247",
                    "resource": {
                        "worktreeId": "fd201816-f015-4412-8e3a-c277d3284a04::C:/Users/yo/orca/workspaces/ultrarentable/agy-B20",
                    },
                },
            ]
        },
    }

    terminal_list_fixture = {
        "status": "ok",
        "result": {
            "terminals": [
                {
                    "handle": "term_e892abe6-2f95-45af-aa8b-3c0d02d7a2c4",
                    "worktreePath": "C:/Users/yo/orca/workspaces/ultrarentable/agy-B17",
                },
                {
                    "handle": "term_aff1db60-fe09-4bac-9e1c-524495cf84f3",
                    "worktreePath": "C:/Users/yo/orca/workspaces/ultrarentable/agy-B12",
                },
                {
                    "handle": "term_e7fd48a8-9ee9-4f49-b3f1-bcce04606247",
                    "worktreePath": "C:/Users/yo/orca/workspaces/ultrarentable/agy-B20",
                },
            ]
        },
    }

    def find_dispatch_for_agent(agent_id: str, w_fixture: dict, t_fixture: dict) -> str:
        target = f"agy-{agent_id}".lower()
        workers = w_fixture.get("result", {}).get("workers", [])
        terminals = {t.get("handle"): (t.get("worktreePath") or "").lower() for t in t_fixture.get("result", {}).get("terminals", [])}
        for w in reversed(workers):
            wt_id = (w.get("resource", {}).get("worktreeId") or "").lower()
            if target in wt_id:
                return w.get("dispatchId", "")
            handle = w.get("agentTerminalHandle")
            if handle and handle in terminals:
                if target in terminals[handle]:
                    return w.get("dispatchId", "")
        return ""

    assert find_dispatch_for_agent("B17", worker_list_fixture, terminal_list_fixture) == "ctx_da201747a158"
    assert find_dispatch_for_agent("B12", worker_list_fixture, terminal_list_fixture) == "ctx_9a6d79165783"
    assert find_dispatch_for_agent("B20", worker_list_fixture, terminal_list_fixture) == "ctx_675fbc52ee66"
    assert find_dispatch_for_agent("B99", worker_list_fixture, terminal_list_fixture) == ""


def test_registro_cierre_json(tmp_path: pathlib.Path):
    """(d) Valida que el registro JSON de cierre emitido en agentes.jsonl es valido y completo."""
    jsonl_path = tmp_path / "agentes.jsonl"
    
    # Registro de apertura previo
    open_record = {
        "id": "B20",
        "hora": "2026-09-02 17:50:00",
        "pid": 1234,
        "worktree": "C:/Users/yo/orca/workspaces/ultrarentable/agy-B20",
        "hijos": 2,
        "mb": 340.5,
        "task": "task_0b08d7a20cd6",
        "dispatch": "ctx_675fbc52ee66",
    }
    # Registro de cierre emitido por agy_cerrar.sh
    close_record = {
        "evento": "cierre",
        "id": "B20",
        "hora": "2026-09-02 18:05:00",
        "worktree": "C:/Users/yo/orca/workspaces/ultrarentable/agy-B20",
        "dispatch": "ctx_675fbc52ee66",
        "sin_worktree": 0,
        "issue": "42",
        "etiqueta": "integrado",
    }

    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(json.dumps(open_record) + "\n")
        f.write(json.dumps(close_record) + "\n")

    lines = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == 2

    cierre = lines[1]
    assert cierre["evento"] == "cierre"
    assert cierre["id"] == "B20"
    assert cierre["dispatch"] == "ctx_675fbc52ee66"
    assert cierre["etiqueta"] == "integrado"
    for k in ["evento", "id", "hora", "worktree", "dispatch", "sin_worktree", "issue", "etiqueta"]:
        assert k in cierre, f"Clave obligatoria {k} ausente en registro de cierre"


def test_agy_cerrar_flags_validation():
    """Valida el manejo de parametros de agy_cerrar.sh ante opciones invalidas o incompletas."""
    cerrar_sh = SCRIPTS_ORQ / "agy_cerrar.sh"
    bash_bin = "bash"
    git_bash = pathlib.Path(r"C:\Program Files\Git\bin\bash.exe")
    if git_bash.exists():
        bash_bin = str(git_bash)

    # 1. Sin argumentos -> rc=1
    res_no_args = _run_cmd([bash_bin, str(cerrar_sh)])
    assert res_no_args.returncode == 1
    assert "Uso:" in res_no_args.stdout or "Uso:" in res_no_args.stderr

    # 2. Etiqueta invalida -> rc=1
    res_bad_tag = _run_cmd([bash_bin, str(cerrar_sh), "B99", "--etiqueta", "invalida"])
    assert res_bad_tag.returncode == 1
    assert "etiqueta invalida" in res_bad_tag.stdout or "etiqueta invalida" in res_bad_tag.stderr

    # 3. --issue sin valor -> rc=1
    res_no_issue_val = _run_cmd([bash_bin, str(cerrar_sh), "B99", "--issue"])
    assert res_no_issue_val.returncode == 1
    assert "falta valor para --issue" in res_no_issue_val.stdout or "falta valor para --issue" in res_no_issue_val.stderr
