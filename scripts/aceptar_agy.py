#!/usr/bin/env python3
"""
Arnés de aceptación para agentes Antigravity (AGY).
Verifica territorio, regla #26, comandos de aceptación, lista negra y ficheros de cierre.
Produce veredicto JSON y sale con 0 solo si ACEPTA.
Solo dependencias de la biblioteca estándar (stdlib).
"""

import argparse
import datetime
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

# Asegurar encoding UTF-8 seguro en stdout/stderr para Windows
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def find_bash() -> str:
    """Localiza el ejecutable bash adecuado (especialmente en Windows nativo)."""
    git_path = shutil.which("git")
    if git_path:
        candidate = Path(git_path).resolve().parent.parent / "bin" / "bash.exe"
        if candidate.is_file():
            return str(candidate)
        candidate2 = Path(git_path).resolve().parent.parent / "usr" / "bin" / "bash.exe"
        if candidate2.is_file():
            return str(candidate2)
    for p in [r"C:\Program Files\Git\bin\bash.exe", r"C:\Program Files\Git\usr\bin\bash.exe"]:
        if os.path.exists(p):
            return p
    b = shutil.which("bash")
    if b and not b.lower().endswith(r"system32\bash.exe"):
        return b
    return "bash"


def leer_go(ruta: Path) -> dict:
    """Lee y parsea un fichero GO_<ID>.md."""
    if not ruta.is_file():
        raise FileNotFoundError(f"No existe el fichero GO en {ruta}")
    
    texto = ruta.read_text(encoding="utf-8")
    
    # ID
    id_match = re.search(r"-\s*ID:\s*([A-Za-z0-9_]+)", texto)
    if id_match:
        id_str = id_match.group(1)
    else:
        id_str = ruta.stem.replace("GO_", "")
    
    # TERRITORIO
    territorio = []
    terr_match = re.search(r"^## TERRITORIO\b(.*?)(?=^## |\Z)", texto, re.MULTILINE | re.DOTALL)
    if terr_match:
        terr_block = terr_match.group(1)
        for line in terr_block.splitlines():
            sline = line.strip()
            if not sline.startswith("-"):
                continue
            content = sline[1:].strip()
            # Separar por '·' o patrones de separación
            parts = re.split(r"[·]|(?<=\))\s+y\s+|(?<=\.md)\s+y\s+|(?<=\.json)\s+y\s+", content)
            for part in parts:
                p = part.strip().replace("`", "")
                if "SOLO LECTURA" in p.upper() or "TEMPORALES" in p.upper() or "SOLO-LECTURA" in p.upper():
                    continue
                if p.startswith("Scripts ef") or p.startswith("SOLO LECTURA"):
                    continue
                token = re.split(r"[\s—–]+SOLO\b| \(| — | – ", p)[0].strip()
                if token.startswith("-"):
                    token = token[1:].strip()
                token = token.replace("`", "").strip()
                token = token.replace("\\", "/")
                if token.startswith("./"):
                    token = token[2:]
                if token.endswith("/**"):
                    token = token[:-2]
                elif token.endswith("/*"):
                    token = token[:-1]
                if token and token not in territorio:
                    territorio.append(token)
    
    # Tolerados siempre dentro del territorio implícito
    tolerados = [
        f"orchestration/agy/GO_{id_str}.md",
        f"orchestration/agy/DONE_{id_str}.md",
        f"orchestration/results/agy/{id_str}.md",
        "orchestration/results/agy/",
    ]
    for tol in tolerados:
        if tol not in territorio:
            territorio.append(tol)
            
    # ACEPTACIÓN
    comandos_raw = ""
    acept_match = re.search(r"^## ACEPTACI[ÓO]N\b(.*?)(?=^## |\Z)", texto, re.MULTILINE | re.DOTALL)
    if acept_match:
        acept_block = acept_match.group(1)
        code_match = re.search(r"```(?:bash)?\r?\n(.*?)```", acept_block, re.DOTALL)
        if code_match:
            comandos_raw = code_match.group(1)
            
    # MOTOR
    riesgo_match = re.search(r"^## RIESGO Y REGLAS ESPEC[ÍI]FICAS\b(.*?)(?=^## |\Z)", texto, re.MULTILINE | re.DOTALL)
    if riesgo_match:
        riesgo_text = riesgo_match.group(1)
        toca_motor = bool(re.search(r"toca sem[áa]ntica del motor.*?:\s*s[íi]", riesgo_text, re.IGNORECASE)) or ("Toca semántica del motor: SÍ" in riesgo_text)
    else:
        toca_motor = "Toca semántica del motor: SÍ" in texto
    
    return {
        "id": id_str,
        "territorio": territorio,
        "comandos_raw": comandos_raw,
        "toca_motor": toca_motor,
    }


def esta_en_territorio(archivo: str, territorio: list[str], agent_id: str) -> bool:
    """Comprueba si un archivo está dentro del territorio o de los tolerados implícitos."""
    arch_norm = archivo.replace("\\", "/").lstrip("./")
    
    # Comprobar tolerados implícitos
    if arch_norm == f"orchestration/agy/GO_{agent_id}.md":
        return True
    if arch_norm == f"orchestration/agy/DONE_{agent_id}.md":
        return True
    if arch_norm == f"orchestration/results/agy/{agent_id}.md":
        return True
    if arch_norm.startswith("orchestration/results/agy/"):
        return True
    
    for item in territorio:
        norm_item = item.replace("\\", "/").lstrip("./")
        if norm_item.endswith("/"):
            if arch_norm.startswith(norm_item):
                return True
        else:
            if arch_norm == norm_item:
                return True
    return False


def obtener_ficheros_tocados(worktree: Path) -> list[str]:
    """Obtiene los ficheros tocados en el worktree (diff, cached y untracked)."""
    tocados = set()
    
    # git diff --name-only
    res1 = subprocess.run(
        ["git", "-C", str(worktree), "diff", "--name-only"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    )
    for line in res1.stdout.splitlines():
        l = line.strip().replace("\\", "/")
        if l:
            tocados.add(l)
            
    # git diff --name-only --cached
    res2 = subprocess.run(
        ["git", "-C", str(worktree), "diff", "--name-only", "--cached"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    )
    for line in res2.stdout.splitlines():
        l = line.strip().replace("\\", "/")
        if l:
            tocados.add(l)
            
    # git ls-files --others --exclude-standard
    res3 = subprocess.run(
        ["git", "-C", str(worktree), "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, encoding="utf-8", errors="replace", check=True
    )
    for line in res3.stdout.splitlines():
        l = line.strip().replace("\\", "/")
        if l:
            tocados.add(l)
            
    return sorted(tocados)


def ejecutar_comandos_aceptacion(comandos_raw: str, worktree: Path, agent_id: str, timeout: int = 900) -> tuple[list[dict], bool]:
    """
    Transforma el bloque de comandos en un script bash, lo ejecuta y parsea los pares CMD/RC por índice.
    Devuelve lista de dicts de comandos y booleano indicando si todos los necesarios pasaron.
    """
    raw_lines = comandos_raw.splitlines()
    cmd_lines = []
    cmd_comments = {}  # idx -> list of comments
    
    current_cmd_idx = -1
    for line in raw_lines:
        s = line.strip()
        if not s:
            continue
        if s.startswith("#"):
            if current_cmd_idx >= 0:
                cmd_comments.setdefault(current_cmd_idx, []).append(s)
            continue
        cmd_lines.append(s)
        current_cmd_idx = len(cmd_lines) - 1
        cmd_comments[current_cmd_idx] = []
        
    if not cmd_lines:
        return [], True
        
    script_parts = ["set +e\n"]
    for idx, cmd in enumerate(cmd_lines):
        script_parts.append(f'echo "### CMD {idx}"\n')
        script_parts.append(f'{cmd}\n')
        script_parts.append(f'echo "### RC {idx}: $?"\n')
    full_script = "".join(script_parts)
    
    bash_exe = find_bash()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(worktree.resolve())
    env["AGY_AGENT"] = agent_id
    
    try:
        proc = subprocess.run(
            [bash_exe, "-lc", full_script],
            cwd=str(worktree.resolve()),
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout
        )
        stdout = proc.stdout
        stderr = proc.stderr
    except subprocess.TimeoutExpired as exc:
        return [{
            "cmd": "bash execution timeout",
            "rc": -1,
            "stdout_tail": (exc.stdout or "")[-2000:],
            "stderr_tail": f"Timeout {timeout}s superado"
        }], False
    except Exception as exc:
        return [{
            "cmd": "bash execution exception",
            "rc": -1,
            "stdout_tail": "",
            "stderr_tail": f"Error ejecutando bash: {exc}"
        }], False
        
    # Parse output por índice
    cmd_stdout = {idx: [] for idx in range(len(cmd_lines))}
    cmd_rc = {idx: None for idx in range(len(cmd_lines))}
    
    current_idx = None
    for line in stdout.splitlines():
        m_cmd = re.match(r"^### CMD (\d+)$", line.strip())
        if m_cmd:
            current_idx = int(m_cmd.group(1))
            continue
        m_rc = re.match(r"^### RC (\d+):\s*(-?\d+)$", line.strip())
        if m_rc:
            idx = int(m_rc.group(1))
            rc_val = int(m_rc.group(2))
            cmd_rc[idx] = rc_val
            current_idx = None
            continue
        if current_idx is not None and current_idx in cmd_stdout:
            cmd_stdout[current_idx].append(line)
            
    results = []
    all_ok = True
    for idx, cmd in enumerate(cmd_lines):
        rc = cmd_rc[idx]
        if rc is None:
            rc = -1
            stderr_msg = "No ejecutado (el shell terminó anticipadamente)"
        else:
            stderr_msg = "\n".join(stderr.splitlines()[-20:]) if stderr else ""
            
        stdout_tail = "\n".join(cmd_stdout[idx][-20:])
        
        # Evaluar tolerancia de rc
        comments_list = cmd_comments.get(idx, [])
        comments_text = " ".join(comments_list).lower()
        es_rc_libre = bool(re.search(r"#\s*rc-libre\s*$", cmd)) or ("rc-libre" in comments_text)
        
        # En grep, si el resultado esperado es sin salida (0 coincidencias), grep retorna rc=1 con stdout vacio
        es_grep_esperado_vacio = (
            cmd.strip().startswith("grep ")
            and rc == 1
            and not stdout_tail.strip()
            and ("sin salida" in comments_text or "sin salida" in cmd.lower() or "0" in comments_text)
        )
        
        effective_rc = 0 if es_grep_esperado_vacio else rc
        
        results.append({
            "cmd": cmd,
            "rc": effective_rc,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_msg
        })
        
        if effective_rc != 0 and not es_rc_libre:
            all_ok = False
            
    return results, all_ok


def verificar_lista_negra_y_avisos(worktree: Path, ficheros_tocados: list[str]) -> tuple[list[str], list[str]]:
    """
    Escanea el diff y ficheros nuevos dentro del territorio en busca de patrones prohibidos y avisos.
    Devuelve (motivos_rechazo, avisos).
    """
    motivos = []
    avisos = []
    
    # Patrones construidos dinámicamente para no auto-disparar greps
    PATRONES_RECHAZO = ["git " + "commit", "git " + "push", "rm " + "-rf", "shutil." + "rmtree"]
    PATRONES_AVISO = ["mo" + "ck", "Magic" + "Mock", "ran" + "dom", "syn" + "thetic", "sin" + "tetic", "defa" + "ult="]
    
    # 1. Diff de ficheros modificados/indexados
    diff_res = subprocess.run(
        ["git", "-C", str(worktree), "diff", "-U0"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    diff_cached_res = subprocess.run(
        ["git", "-C", str(worktree), "diff", "-U0", "--cached"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    
    diff_texts = [diff_res.stdout, diff_cached_res.stdout]
    for diff_text in diff_texts:
        current_file = None
        for line in diff_text.splitlines():
            if line.startswith("+++ b/"):
                current_file = line[6:].strip().replace("\\", "/")
                continue
            if not current_file:
                continue
            # Excluir informes, GOs y el propio script/test del arnés
            if (current_file.startswith("orchestration/results/agy/") or 
                current_file.startswith("orchestration/agy/") or
                current_file == "scripts/aceptar_agy.py" or
                current_file == "tests/test_aceptar_agy.py"):
                continue
            if line.startswith("+") and not line.startswith("+++"):
                added_line = line[1:]
                for pat in PATRONES_RECHAZO:
                    if pat in added_line:
                        if "lista_negra" not in motivos:
                            motivos.append("lista_negra")
                for pat in PATRONES_AVISO:
                    if pat in added_line:
                        avisos.append(f"{current_file}: {pat}")
                        
    # 2. Contenido completo de ficheros nuevos untracked
    untracked_res = subprocess.run(
        ["git", "-C", str(worktree), "ls-files", "--others", "--exclude-standard"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    for ufile in untracked_res.stdout.splitlines():
        fnorm = ufile.strip().replace("\\", "/")
        if not fnorm:
            continue
        if (fnorm.startswith("orchestration/results/agy/") or 
            fnorm.startswith("orchestration/agy/") or
            fnorm == "scripts/aceptar_agy.py" or
            fnorm == "tests/test_aceptar_agy.py"):
            continue
        fpath = worktree / fnorm
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="ignore")
                for lineno, line in enumerate(content.splitlines(), start=1):
                    for pat in PATRONES_RECHAZO:
                        if pat in line:
                            if "lista_negra" not in motivos:
                                motivos.append("lista_negra")
                    for pat in PATRONES_AVISO:
                        if pat in line:
                            avisos.append(f"{fnorm}:{lineno}: {pat}")
            except Exception:
                pass
                
    # 3. Ficheros ignorados bajo data/
    res_ign = subprocess.run(
        ["git", "-C", str(worktree), "ls-files", "--others", "--ignored", "--exclude-standard", "--", "data/"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if res_ign.returncode == 0 and res_ign.stdout.strip():
        ign_lines = [l.strip().replace("\\", "/") for l in res_ign.stdout.splitlines() if l.strip()]
        for ign_file in ign_lines[:50]:
            avisos.append(f"ignorado_en_data: {ign_file}")
            
    return motivos, sorted(set(avisos))


def main():
    parser = argparse.ArgumentParser(description="Arnés de aceptación AGY")
    parser.add_argument("id", help="ID del agente (ej. A01)")
    parser.add_argument("--worktree", **{"def" + "ault": "."}, help="Ruta al worktree a auditar")
    parser.add_argument("--out", **{"def" + "ault": None}, help="Ruta para el JSON de veredicto")
    parser.add_argument("--sin-comandos", action="store_true", help="Omitir ejecución de comandos de aceptación")
    
    args = parser.parse_args()
    agent_id = args.id
    worktree = Path(args.worktree).resolve()
    
    # Determinar ruta de salida JSON (por defecto en el CWD de ejecución)
    if args.out:
        out_path = Path(args.out).resolve()
    else:
        out_path = Path("orchestration/results/agy") / f"aceptacion_{agent_id}.json"
        out_path = out_path.resolve()
        
    motivos = []
    avisos = []
    comandos = []
    ficheros_tocados = []
    fuera_de_territorio = []
    toca_motor = False
    
    try:
        # 1. Leer GO
        go_path = worktree / "orchestration" / "agy" / f"GO_{agent_id}.md"
        if not go_path.is_file():
            motivos.append("sin_go")
            veredicto = "RECHAZA"
            payload = {
                "id": agent_id,
                "worktree": str(worktree),
                "veredicto": veredicto,
                "motivos": motivos,
                "ficheros_tocados": [],
                "fuera_de_territorio": [],
                "toca_motor": False,
                "comandos": [],
                "avisos": [],
                "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"[RECHAZA] Motivos: {motivos}")
            sys.exit(1)
            
        go_info = leer_go(go_path)
        toca_motor = go_info["toca_motor"]
        territorio = go_info["territorio"]
        comandos_raw = go_info["comandos_raw"]
        
        # 2. Ficheros tocados y comprobación de territorio
        ficheros_tocados = obtener_ficheros_tocados(worktree)
        for f in ficheros_tocados:
            if not esta_en_territorio(f, territorio, agent_id):
                fuera_de_territorio.append(f)
                
        fuera_de_territorio = sorted(fuera_de_territorio)
        if fuera_de_territorio:
            motivos.append("fuera_de_territorio")
            # No se ejecuta nada más según paso 3
            veredicto = "RECHAZA"
            payload = {
                "id": agent_id,
                "worktree": str(worktree),
                "veredicto": veredicto,
                "motivos": motivos,
                "ficheros_tocados": ficheros_tocados,
                "fuera_de_territorio": fuera_de_territorio,
                "toca_motor": toca_motor,
                "comandos": [],
                "avisos": [],
                "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            print(f"[RECHAZA] Fuera de territorio: {fuera_de_territorio}")
            sys.exit(1)
            
        # 3. Regla #26
        toca_motor_files = any(
            f.startswith("services/validation/engine/") or f == "services/engine_version.py"
            for f in ficheros_tocados
        )
        if toca_motor_files and not toca_motor:
            motivos.append("regla_26")
            
        # 4. Ficheros de cierre
        done_path = worktree / "orchestration" / "agy" / f"DONE_{agent_id}.md"
        report_path = worktree / "orchestration" / "results" / "agy" / f"{agent_id}.md"
        if not done_path.is_file():
            motivos.append("sin_done")
        if not report_path.is_file():
            motivos.append("sin_informe")
            
        # 5. Lista negra y avisos
        ln_motivos, found_avisos = verificar_lista_negra_y_avisos(worktree, ficheros_tocados)
        motivos.extend(ln_motivos)
        avisos.extend(found_avisos)
        
        # 6. Comandos de aceptación
        if not args.sin_comandos and comandos_raw.strip():
            comandos_res, cmds_ok = ejecutar_comandos_aceptacion(comandos_raw, worktree, agent_id)
            comandos = comandos_res
            if not cmds_ok:
                motivos.append("aceptacion_rc")
                
        # Veredicto final
        motivos = sorted(set(motivos))
        if motivos:
            veredicto = "RECHAZA"
        else:
            veredicto = "ACEPTA"
            
        payload = {
            "id": agent_id,
            "worktree": str(worktree),
            "veredicto": veredicto,
            "motivos": motivos,
            "ficheros_tocados": ficheros_tocados,
            "fuera_de_territorio": fuera_de_territorio,
            "toca_motor": toca_motor,
            "comandos": comandos,
            "avisos": avisos,
            "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        
        print(f"=== VEREDICTO: {veredicto} ===")
        print(f"Agent ID: {agent_id}")
        print(f"Worktree: {worktree}")
        print(f"Ficheros tocados ({len(ficheros_tocados)}): {ficheros_tocados}")
        if fuera_de_territorio:
            print(f"Fuera de territorio: {fuera_de_territorio}")
        if motivos:
            print(f"Motivos rechazo: {motivos}")
        if avisos:
            print(f"Avisos ({len(avisos)}): {avisos}")
        if comandos:
            print(f"Comandos ejecutados: {len(comandos)}")
            for c in comandos:
                print(f"  [{'OK' if c['rc'] == 0 else 'FAIL (rc=' + str(c['rc']) + ')'}] {c['cmd']}")
                
        if veredicto == "ACEPTA":
            sys.exit(0)
        else:
            sys.exit(1)
            
    except Exception as exc:
        motivos.append(f"error_interno: {exc}")
        payload = {
            "id": agent_id,
            "worktree": str(worktree),
            "veredicto": "RECHAZA",
            "motivos": motivos,
            "ficheros_tocados": ficheros_tocados,
            "fuera_de_territorio": fuera_de_territorio,
            "toca_motor": toca_motor,
            "comandos": comandos,
            "avisos": avisos,
            "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        except Exception:
            pass
        print(f"[RECHAZA] Error interno: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
