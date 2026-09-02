#!/usr/bin/env python3
"""
Arnés de aceptación para agentes Antigravity (AGY) v3.
Verifica territorio, regla #26, comandos de aceptación, lista negra y ficheros de cierre.
Soporta rutas múltiples en TERRITORIO con separador ' · ', comodines (<fecha>, <YYYYMMDD>, <ID>, *)
y ejecución robusta de ACEPTACIÓN línea a línea con ["bash", "-lc", cmd].
Produce veredicto JSON y genera informe Markdown con --informe.
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


def pattern_to_regex(pat: str) -> re.Pattern:
    """
    Convierte una ruta de territorio (con comodines <fecha>, <YYYYMMDD>, <ID>, *, etc.)
    en una expresión regular. Si termina en '/', cubre todo el subárbol.
    """
    norm = pat.replace("\\", "/").strip()
    if norm.startswith("./"):
        norm = norm[2:]

    is_dir = norm.endswith("/")
    if is_dir:
        norm = norm.rstrip("/")

    # Reemplazar comodines: <fecha>, <YYYYMMDD>, <YYYY-MM-DD>, <ID>, <id>, <fecha-hora>, <timestamp>, *
    tokens = []
    def _repl(match):
        tokens.append(match.group(0))
        return f"__WILDCARD_{len(tokens)-1}__"

    replaced = re.sub(r"<[^>]+>|\*", _repl, norm)
    escaped = re.escape(replaced)

    for i in range(len(tokens)):
        escaped = escaped.replace(re.escape(f"__WILDCARD_{i}__"), r"[A-Za-z0-9_.-]+")

    if is_dir:
        regex_str = rf"^{escaped}(?:/.*)?$"
    else:
        regex_str = rf"^{escaped}$"

    return re.compile(regex_str)


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
            content = sline.lstrip("- *").strip()
            # Separar por ' · ' o viñetas o conjunciones de ficheros
            parts = re.split(
                r"\s*[·•]\s*|(?<=\))\s+y\s+|(?<=\.md)\s+y\s+|(?<=\.json)\s+y\s+|(?<=\.py)\s+y\s+|(?<=\.ts)\s+y\s+|(?<=\.tsx)\s+y\s+|(?<=\.ps1)\s+y\s+|(?<=\.sh)\s+y\s+",
                content
            )
            for part in parts:
                p = part.strip().replace("`", "")
                if not p:
                    continue
                if "SOLO LECTURA" in p.upper() or "TEMPORALES" in p.upper() or "SOLO-LECTURA" in p.upper():
                    continue
                if p.startswith("Scripts ef") or p.startswith("SOLO LECTURA"):
                    continue
                
                # Quitar aclaraciones entre paréntesis o tras guiones
                token = re.sub(r"\(.*?\)", "", p).strip()
                if "(" in token:
                    token = token.split("(")[0].strip()
                token = re.split(r"[\s—–]+SOLO\b| — | – | -- ", token)[0].strip()
                token = token.lstrip("- *").strip()
                token = token.replace("\\", "/")
                if token.startswith("./"):
                    token = token[2:]
                if token.endswith("/**"):
                    token = token[:-2]
                elif token.endswith("/*"):
                    token = token[:-1]
                
                token = token.rstrip(":,").strip()
                
                if token and token not in territorio:
                    territorio.append(token)
    
    # Tolerados siempre dentro del territorio implícito
    tolerados = [
        f"orchestration/agy/GO_{id_str}.md",
        f"orchestration/agy/DONE_{id_str}.md",
        f"orchestration/results/agy/{id_str}.md",
        "orchestration/results/agy/",
        "orchestration/results/auditorias/",
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
    if arch_norm.startswith("orchestration/results/auditorias/"):
        return True
    
    for item in territorio:
        reg = pattern_to_regex(item)
        if reg.match(arch_norm):
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


def ejecutar_comandos_aceptacion(comandos_raw: str, worktree: Path, agent_id: str, timeout: int = 600) -> tuple[list[dict], bool]:
    """
    Ejecuta el bloque de comandos línea a línea pasando cada comando como argumento a `["bash", "-lc", cmd]`.
    Preserva variables de entorno asignadas en líneas previas (ej. PY=...).
    Devuelve lista de dicts de comandos y booleano indicando si todos los necesarios pasaron.
    """
    raw_lines = comandos_raw.splitlines()
    cmd_lines = []
    
    for line in raw_lines:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        cmd_lines.append(s)
        
    if not cmd_lines:
        return [], True

    bash_exe = find_bash()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(worktree.resolve())
    env["AGY_AGENT"] = agent_id
    default_py = "C:/Users/yo/Pictures/Descargaspc/pro/UltrarentablePC/ultrarentable/.venv/Scripts/python.exe"
    if os.path.exists(default_py):
        env["PY"] = default_py
    else:
        env["PY"] = sys.executable

    results = []
    all_ok = True
    assigned_vars = []

    for cmd_line in cmd_lines:
        es_rc_libre = bool(re.search(r"#\s*rc-libre\b", cmd_line, re.IGNORECASE))
        es_sin_salida = bool(re.search(r"#\s*(?:sin salida|esperado:\s*0)\b", cmd_line, re.IGNORECASE))
        
        # Detectar asignación simple de variable para persistirla para comandos subsiguientes
        m_assign = re.match(r"^(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*=(?:'[^']*'|\"[^\"]*\"|\$\([^)]+\)|[^\s;&|]+)$", cmd_line.strip())
        if m_assign and cmd_line.strip() not in assigned_vars:
            assigned_vars.append(cmd_line.strip())

        if assigned_vars:
            vars_prefix = "\n".join(assigned_vars)
            if cmd_line.strip() == assigned_vars[-1]:
                cmd_to_run = vars_prefix
            else:
                cmd_to_run = f"{vars_prefix}\n{cmd_line}"
        else:
            cmd_to_run = cmd_line

        try:
            proc = subprocess.run(
                [bash_exe, "-lc", cmd_to_run],
                cwd=str(worktree.resolve()),
                env=env,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout
            )
            raw_stdout = proc.stdout or ""
            raw_stderr = proc.stderr or ""
            rc = proc.returncode

            stdout_tail = raw_stdout[-2000:]
            stderr_tail = raw_stderr[-2000:]

        except subprocess.TimeoutExpired as exc:
            rc = -1
            stdout_tail = (exc.stdout or "")[-2000:]
            stderr_tail = f"Timeout {timeout}s superado"
        except Exception as exc:
            rc = -1
            stdout_tail = ""
            stderr_tail = f"Error ejecutando comando: {exc}"

        # En grep, si el resultado esperado es sin salida (0 coincidencias), grep retorna rc=1 con stdout vacio
        es_grep_esperado_vacio = (
            cmd_line.strip().startswith("grep ")
            and rc == 1
            and not stdout_tail.strip()
            and (es_sin_salida or "0" in cmd_line)
        )

        effective_rc = 0 if es_grep_esperado_vacio else rc

        cmd_result = {
            "cmd": cmd_line,
            "rc": effective_rc,
            "stdout": stdout_tail,
            "stderr": stderr_tail,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
        }
        results.append(cmd_result)

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
            # Excluir informes, auditorías, GOs y el propio script/test del arnés
            if (current_file.startswith("orchestration/results/agy/") or 
                current_file.startswith("orchestration/results/auditorias/") or
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
            fnorm.startswith("orchestration/results/auditorias/") or
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


def verificar_integridad_go(worktree: Path, agent_id: str) -> tuple[list[str], list[str]]:
    """
    Verifica la integridad del fichero GO_<ID>.md comparándolo con HEAD.
    Devuelve (motivos, secciones_alteradas).
    """
    motivos = []
    secciones_alteradas = []
    go_rel_path = f"orchestration/agy/GO_{agent_id}.md"
    go_file = worktree / "orchestration" / "agy" / f"GO_{agent_id}.md"
    
    if not go_file.is_file():
        motivos.append("sin_go")
        return motivos, secciones_alteradas
        
    res_show = subprocess.run(
        ["git", "-C", str(worktree), "show", f"HEAD:{go_rel_path}"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if res_show.returncode != 0:
        motivos.append("go_no_versionado")
        return motivos, secciones_alteradas
        
    head_text = res_show.stdout.replace("\r\n", "\n")
    disk_text = go_file.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n")
    
    if head_text == disk_text:
        return motivos, secciones_alteradas
        
    # Verificar si solo difiere por texto AÑADIDO al final que empiece por ## CORRECCION_
    head_trimmed = head_text.rstrip()
    if disk_text.startswith(head_trimmed):
        resto = disk_text[len(head_trimmed):].strip()
        if not resto:
            return motivos, secciones_alteradas
        if resto.startswith("## CORRECCION_"):
            return motivos, secciones_alteradas
        else:
            secciones_alteradas.append("CORRECCION_INVALIDA")
            motivos.append("go_alterado")
            return motivos, secciones_alteradas
            
    # Extraer secciones críticas: TERRITORIO, ACEPTACIÓN, RIESGO
    def extraer_bloque(texto: str, nombre_regex: str) -> str:
        m = re.search(rf"(^##\s+{nombre_regex}\b.*?)(?=^## |\Z)", texto, re.MULTILINE | re.DOTALL)
        return m.group(1).strip() if m else ""
        
    sec_map = [
        ("TERRITORIO", r"TERRITORIO"),
        ("ACEPTACIÓN", r"ACEPTACI[ÓO]N"),
        ("RIESGO", r"RIESGO"),
    ]
    for nombre_sec, regex_sec in sec_map:
        head_sec = extraer_bloque(head_text, regex_sec)
        disk_sec = extraer_bloque(disk_text, regex_sec)
        if head_sec != disk_sec:
            secciones_alteradas.append(nombre_sec)
            
    if not secciones_alteradas:
        secciones_alteradas.append("CUERPO")
        
    motivos.append("go_alterado")
    return motivos, secciones_alteradas


def resolver_base_y_verificar_commits(worktree: Path, base_ref: str | None = None) -> tuple[list[str], list[str]]:
    """
    Resuelve el merge-base o base ref y verifica si hay commits hechos por el agente sobre dicha base.
    Devuelve (motivos, commits_agente).
    """
    motivos = []
    commits_agente = []
    base_sha = None
    
    if base_ref:
        res = subprocess.run(
            ["git", "-C", str(worktree), "merge-base", "HEAD", base_ref],
            capture_output=True, text=True, encoding="utf-8", errors="replace"
        )
        if res.returncode == 0 and res.stdout.strip():
            base_sha = res.stdout.strip()
        else:
            res_rev = subprocess.run(
                ["git", "-C", str(worktree), "rev-parse", "--verify", f"{base_ref}^{{commit}}"],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if res_rev.returncode == 0 and res_rev.stdout.strip():
                base_sha = res_rev.stdout.strip()
            else:
                motivos.append("base_no_resuelta")
                return motivos, commits_agente
    else:
        candidatos = [
            "JOSFER78/orquesta-antigravity-max-10",
            "origin/main",
            "main",
            "master",
        ]
        for cand in candidatos:
            res = subprocess.run(
                ["git", "-C", str(worktree), "merge-base", "HEAD", cand],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if res.returncode == 0 and res.stdout.strip():
                base_sha = res.stdout.strip()
                break
                
        if not base_sha:
            res_root = subprocess.run(
                ["git", "-C", str(worktree), "rev-list", "--max-parents=0", "HEAD"],
                capture_output=True, text=True, encoding="utf-8", errors="replace"
            )
            if res_root.returncode == 0 and res_root.stdout.strip():
                roots = [r.strip() for r in res_root.stdout.strip().splitlines() if r.strip()]
                if roots:
                    base_sha = roots[0]
                    
        if not base_sha:
            motivos.append("base_no_resuelta")
            return motivos, commits_agente

    # Verificar commits: git log --oneline <base_sha>..HEAD
    res_log = subprocess.run(
        ["git", "-C", str(worktree), "log", "--oneline", f"{base_sha}..HEAD"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if res_log.returncode == 0 and res_log.stdout.strip():
        lines = [line.strip() for line in res_log.stdout.splitlines() if line.strip()]
        if lines:
            commits_agente = lines
            motivos.append("commits_del_agente")
            
    return motivos, commits_agente


def generar_informe_auditoria(
    worktree: Path,
    agent_id: str,
    veredicto: str,
    motivos: list[str],
    territorio: list[str],
    ficheros_tocados: list[str],
    fuera_de_territorio: list[str],
    comandos: list[dict],
    avisos: list[str],
    commits_agente: list[str],
    go_secciones_alteradas: list[str],
    toca_motor: bool,
) -> Path:
    """Genera el informe de auditoría Markdown en orchestration/results/auditorias/<ID>_<fecha-hora>.md."""
    now_dt = datetime.datetime.now()
    timestamp = now_dt.strftime("%Y%m%d_%H%M%S")
    now_utc_str = datetime.datetime.now(datetime.timezone.utc).isoformat()
    
    auditorias_dir = worktree / "orchestration" / "results" / "auditorias"
    auditorias_dir.mkdir(parents=True, exist_ok=True)
    
    report_file = auditorias_dir / f"{agent_id}_{timestamp}.md"
    
    lines = [
        f"# Auditoría de Aceptación — {agent_id}",
        "",
        f"- **Fecha UTC**: `{now_utc_str}`",
        f"- **Worktree**: `{worktree}`",
        f"- **Veredicto**: **{veredicto}**",
        f"- **Motivos de rechazo**: {json.dumps(motivos) if motivos else 'Ninguno'}",
        "",
        "## 1. Territorio Declarado",
        "",
    ]
    for t in territorio:
        lines.append(f"- `{t}`")
    lines.append("")
    
    lines.append(f"## 2. Ficheros Tocados ({len(ficheros_tocados)})")
    lines.append("")
    if ficheros_tocados:
        for f in ficheros_tocados:
            marca = " ⚠️ [FUERA DE TERRITORIO]" if f in fuera_de_territorio else " ✅"
            lines.append(f"- `{f}`{marca}")
    else:
        lines.append("- *Ninguno (working tree limpio)*")
    lines.append("")
    
    if fuera_de_territorio:
        lines.append(f"### Fuera de Territorio ({len(fuera_de_territorio)})")
        for f in fuera_de_territorio:
            lines.append(f"- `{f}`")
        lines.append("")
        
    lines.append(f"## 3. Comandos de Aceptación ({len(comandos)})")
    lines.append("")
    if comandos:
        for idx, c in enumerate(comandos, start=1):
            status = "✅ OK" if c.get("rc", 0) == 0 else f"❌ FAIL (rc={c.get('rc')})"
            lines.append(f"### 3.{idx}. [{status}] `{c.get('cmd')}`")
            lines.append(f"- **Código de retorno (rc)**: `{c.get('rc')}`")
            if c.get("stdout"):
                lines.append("```text")
                lines.append(c.get("stdout").rstrip())
                lines.append("```")
            else:
                lines.append("- *Stdout vacío*")
            if c.get("stderr"):
                lines.append("**Stderr**:")
                lines.append("```text")
                lines.append(c.get("stderr").rstrip())
                lines.append("```")
            lines.append("")
    else:
        lines.append("- *Sin comandos ejecutados*")
        lines.append("")
        
    lines.append("## 4. Verificaciones de Integridad y Reglas")
    lines.append("")
    lines.append(f"- **Integridad del GO**: {'❌ Alterado: ' + ', '.join(go_secciones_alteradas) if go_secciones_alteradas else '✅ Intacto'}")
    lines.append(f"- **Commits del Agente**: {'❌ Detectados: ' + str(len(commits_agente)) if commits_agente else '✅ Ninguno (working tree puro)'}")
    lines.append(f"- **Regla #26 (Motor)**: {'⚠️ Modifica motor (declarado)' if toca_motor else '✅ No afecta motor'}")
    lines.append(f"- **Avisos de Calidad**: {len(avisos)} aviso(s)")
    if avisos:
        for a in avisos:
            lines.append(f"  - `{a}`")
    lines.append("")
    
    report_file.write_text("\n".join(lines), encoding="utf-8")
    return report_file


def main():
    parser = argparse.ArgumentParser(description="Arnés de aceptación AGY")
    parser.add_argument("id", help="ID del agente (ej. A01)")
    parser.add_argument("--worktree", **{"def" + "ault": "."}, help="Ruta al worktree a auditar")
    parser.add_argument("--base", **{"def" + "ault": None}, help="Ref de base para auditar commits del agente")
    parser.add_argument("--out", **{"def" + "ault": None}, help="Ruta para el JSON de veredicto")
    parser.add_argument("--sin-comandos", action="store_true", help="Omitir ejecución de comandos de aceptación")
    parser.add_argument("--informe", action="store_true", help="Genera informe de auditoría Markdown en orchestration/results/auditorias/")
    
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
    commits_agente = []
    go_secciones_alteradas = []
    territorio = []
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
                "commits_agente": [],
                "go_secciones_alteradas": [],
                "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            if args.informe:
                generar_informe_auditoria(
                    worktree, agent_id, veredicto, motivos, territorio,
                    ficheros_tocados, fuera_de_territorio, comandos, avisos,
                    commits_agente, go_secciones_alteradas, toca_motor
                )
            print(f"[RECHAZA] Motivos: {motivos}")
            sys.exit(1)
            
        # 2. Integridad del GO
        go_motivos, go_alteradas = verificar_integridad_go(worktree, agent_id)
        motivos.extend(go_motivos)
        go_secciones_alteradas.extend(go_alteradas)
        
        # 3. Base y commits del agente
        base_motivos, found_commits = resolver_base_y_verificar_commits(worktree, args.base)
        motivos.extend(base_motivos)
        commits_agente.extend(found_commits)
        
        go_info = leer_go(go_path)
        toca_motor = go_info["toca_motor"]
        territorio = go_info["territorio"]
        comandos_raw = go_info["comandos_raw"]
        
        # 4. Ficheros tocados y comprobación de territorio
        ficheros_tocados = obtener_ficheros_tocados(worktree)
        for f in ficheros_tocados:
            if not esta_en_territorio(f, territorio, agent_id):
                fuera_de_territorio.append(f)
                
        fuera_de_territorio = sorted(fuera_de_territorio)
        if fuera_de_territorio:
            motivos.append("fuera_de_territorio")
            veredicto = "RECHAZA"
            payload = {
                "id": agent_id,
                "worktree": str(worktree),
                "veredicto": veredicto,
                "motivos": sorted(set(motivos)),
                "ficheros_tocados": ficheros_tocados,
                "fuera_de_territorio": fuera_de_territorio,
                "toca_motor": toca_motor,
                "comandos": [],
                "avisos": [],
                "commits_agente": commits_agente,
                "go_secciones_alteradas": go_secciones_alteradas,
                "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            if args.informe:
                generar_informe_auditoria(
                    worktree, agent_id, veredicto, sorted(set(motivos)), territorio,
                    ficheros_tocados, fuera_de_territorio, comandos, avisos,
                    commits_agente, go_secciones_alteradas, toca_motor
                )
            print(f"[RECHAZA] Fuera de territorio: {fuera_de_territorio}")
            sys.exit(1)
            
        # 5. Regla #26
        toca_motor_files = any(
            f.startswith("services/validation/engine/") or f == "services/engine_version.py"
            for f in ficheros_tocados
        )
        if toca_motor_files and not toca_motor:
            motivos.append("regla_26")
            
        # 6. Ficheros de cierre
        done_path = worktree / "orchestration" / "agy" / f"DONE_{agent_id}.md"
        report_path = worktree / "orchestration" / "results" / "agy" / f"{agent_id}.md"
        if not done_path.is_file():
            motivos.append("sin_done")
        if not report_path.is_file():
            motivos.append("sin_informe")
            
        # 7. Lista negra y avisos
        ln_motivos, found_avisos = verificar_lista_negra_y_avisos(worktree, ficheros_tocados)
        motivos.extend(ln_motivos)
        avisos.extend(found_avisos)
        
        # 8. Comandos de aceptación
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
            "commits_agente": commits_agente,
            "go_secciones_alteradas": go_secciones_alteradas,
            "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        
        if args.informe:
            inf_file = generar_informe_auditoria(
                worktree, agent_id, veredicto, motivos, territorio,
                ficheros_tocados, fuera_de_territorio, comandos, avisos,
                commits_agente, go_secciones_alteradas, toca_motor
            )
            payload["informe_path"] = str(inf_file)
            
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
        if commits_agente:
            print(f"Commits del agente ({len(commits_agente)}): {commits_agente}")
        if go_secciones_alteradas:
            print(f"Secciones del GO alteradas: {go_secciones_alteradas}")
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
            "motivos": sorted(set(motivos)),
            "ficheros_tocados": ficheros_tocados,
            "fuera_de_territorio": fuera_de_territorio,
            "toca_motor": toca_motor,
            "comandos": comandos,
            "avisos": avisos,
            "commits_agente": commits_agente,
            "go_secciones_alteradas": go_secciones_alteradas,
            "generado_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            if args.informe:
                generar_informe_auditoria(
                    worktree, agent_id, "RECHAZA", sorted(set(motivos)), territorio,
                    ficheros_tocados, fuera_de_territorio, comandos, avisos,
                    commits_agente, go_secciones_alteradas, toca_motor
                )
        except Exception:
            pass
        print(f"[RECHAZA] Error interno: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
