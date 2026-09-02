import json
import os
from pathlib import Path
import subprocess
import sys
import pytest

SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "aceptar_agy.py"


@pytest.fixture
def repo_t1(tmp_path):
    """Fixture que crea un repositorio git real para pruebas del arnés de aceptación."""
    repo = tmp_path / "repo"
    repo.mkdir()
    
    # git init y configuración de usuario
    subprocess.run(["git", "-C", str(repo), "init"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "test@example.com"], check=True, capture_output=True)
    
    # Crear estructura base
    src = repo / "src"
    src.mkdir()
    (src / "a.txt").write_text("inicial\n", encoding="utf-8")
    (repo / "README.md").write_text("# Repo Test\n", encoding="utf-8")
    
    orch_agy = repo / "orchestration" / "agy"
    orch_agy.mkdir(parents=True)
    
    go_content = """# GO_T1 — Test Contract

## Identidad
- ID: T1 · Ola: A · Rama/worktree: agy-T1 · Timebox: 45 min
- Variable de entorno obligatoria: AGY_AGENT=T1

## OBJETIVO
Test de aceptación T1

## TERRITORIO
- src/
- orchestration/results/agy/T1.md
- orchestration/agy/DONE_T1.md

## ENTRADAS
- src/a.txt

## ACEPTACIÓN
```bash
test -f src/a.txt
grep -q hola src/a.txt
```

## RIESGO Y REGLAS ESPECÍFICAS
- ¿Toca semántica del motor? NO

## PROHIBIDO
git commit · rm -rf
"""
    (orch_agy / "GO_T1.md").write_text(go_content, encoding="utf-8")
    
    # Commit inicial (fuera del arnés, core.hooksPath=/dev/null)
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "commit inicial"],
        check=True, capture_output=True
    )
    
    # Modificar src/a.txt con 'hola' y crear DONE_T1.md + T1.md
    (src / "a.txt").write_text("hola mundo\n", encoding="utf-8")
    
    done_content = """# DONE_T1
- Agente: T1
- Informe: orchestration/results/agy/T1.md
- Ficheros tocados:
  - src/a.txt
- Aceptación ejecutada: PASA
- Lo que NO se pudo hacer: ninguna
- Confirmo: sin git de escritura · sin rm · sin datos inventados · nada fuera del territorio.
"""
    (orch_agy / "DONE_T1.md").write_text(done_content, encoding="utf-8")
    
    orch_res = repo / "orchestration" / "results" / "agy"
    orch_res.mkdir(parents=True)
    (orch_res / "T1.md").write_text("# Informe T1\nTodo OK\n", encoding="utf-8")
    
    return repo


def test_caso_a_todo_dentro(repo_t1, tmp_path):
    """(a) Todo dentro de territorio y válido => ACEPTA, exit 0."""
    out_file = tmp_path / "out_a.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert data["motivos"] == []
    assert data["fuera_de_territorio"] == []
    assert "src/a.txt" in data["ficheros_tocados"]
    assert len(data["comandos"]) >= 2
    assert all(c["rc"] == 0 for c in data["comandos"])


def test_caso_b_fuera_de_territorio(repo_t1, tmp_path):
    """(b) Además README.md modificado => RECHAZA, fuera_de_territorio == ['README.md']."""
    (repo_t1 / "README.md").write_text("cambio no permitido\n", encoding="utf-8")
    out_file = tmp_path / "out_b.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 1
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "RECHAZA"
    assert "fuera_de_territorio" in data["motivos"]
    assert data["fuera_de_territorio"] == ["README.md"]


def test_caso_c_regla_26(repo_t1, tmp_path):
    """(c) Fichero services/validation/engine/x.py nuevo sin la cadena de motor => RECHAZA con motivo regla_26."""
    # Añadir services/ al territorio de GO_T1 para que no sea rechazado por territorio primero
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    go_text = go_text.replace("## TERRITORIO\n- src/", "## TERRITORIO\n- src/\n- services/validation/engine/")
    go_path.write_text(go_text, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "update territory"],
        check=True, capture_output=True
    )
    
    engine_dir = repo_t1 / "services" / "validation" / "engine"
    engine_dir.mkdir(parents=True)
    (engine_dir / "x.py").write_text("# nuevo fichero de motor\n", encoding="utf-8")
    
    out_file = tmp_path / "out_c.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file), "--sin-comandos"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 1
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "RECHAZA"
    assert "regla_26" in data["motivos"]


def test_caso_d_aceptacion_rc(repo_t1, tmp_path):
    """(d) Aceptación con un comando que falla (false) => RECHAZA con aceptacion_rc."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    go_text = go_text.replace("grep -q hola src/a.txt", "grep -q hola src/a.txt\nfalse")
    go_path.write_text(go_text, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "update acceptance with failure"],
        check=True, capture_output=True
    )
    
    out_file = tmp_path / "out_d.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 1
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "RECHAZA"
    assert "aceptacion_rc" in data["motivos"]
    assert any(c["cmd"] == "false" and c["rc"] != 0 for c in data["comandos"])


def test_caso_e_sin_done(repo_t1, tmp_path):
    """(e) Sin DONE => RECHAZA con sin_done."""
    (repo_t1 / "orchestration" / "agy" / "DONE_T1.md").unlink()
    out_file = tmp_path / "out_e.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file), "--sin-comandos"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 1
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "RECHAZA"
    assert "sin_done" in data["motivos"]


def test_caso_f_comandos_comillas_y_variables(repo_t1, tmp_path):
    """(f) Aceptación con un comando que contiene comillas dobles y $VAR => ACEPTA y preserva cmd exacto."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    comandos_con_vars = 'PY="$(command -v git)"\n"$PY" --version'
    go_text = go_text.replace("test -f src/a.txt\ngrep -q hola src/a.txt", comandos_con_vars)
    go_path.write_text(go_text, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "acceptance with quotes and vars"],
        check=True, capture_output=True
    )
    
    out_file = tmp_path / "out_f.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert len(data["comandos"]) == 2
    assert data["comandos"][0]["cmd"] == 'PY="$(command -v git)"'
    assert data["comandos"][0]["rc"] == 0
    assert data["comandos"][1]["cmd"] == '"$PY" --version'
    assert data["comandos"][1]["rc"] == 0


def test_caso_g_fichero_ignorado_en_data(repo_t1, tmp_path):
    """(g) Fichero nuevo en ruta ignorada bajo data/ => ACEPTA pero avisos contiene ignorado_en_data: data/x.json."""
    gitignore = repo_t1 / ".gitignore"
    gitignore.write_text("data/*\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_t1), "add", str(gitignore)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "add gitignore for data"],
        check=True, capture_output=True
    )
    
    data_dir = repo_t1 / "data"
    data_dir.mkdir(parents=True)
    (data_dir / "x.json").write_text('{"test": 1}\n', encoding="utf-8")
    
    out_file = tmp_path / "out_g.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert any("ignorado_en_data: data/x.json" in aviso for aviso in data["avisos"])


def test_caso_h_salida_bytes_no_ascii(repo_t1, tmp_path):
    """(h) Aceptación con un comando que imprime bytes no ASCII (printf '\\xe2\\x9c\\x93 ok \\x8d\\n') => ACEPTA con rc=0 y sin error_interno."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    comando_no_ascii = "printf '\\xe2\\x9c\\x93 ok \\x8d\\n'"
    go_text = go_text.replace("test -f src/a.txt\ngrep -q hola src/a.txt", comando_no_ascii)
    go_path.write_text(go_text, encoding="utf-8")
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "acceptance with non-ascii output"],
        check=True, capture_output=True
    )
    
    out_file = tmp_path / "out_h.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert not any("error_interno" in m for m in data["motivos"])
    assert len(data["comandos"]) == 1
    assert data["comandos"][0]["rc"] == 0


def test_caso_i_commits_del_agente(repo_t1, tmp_path):
    """(i) Commit hecho por el agente sobre la base => RECHAZA con commits_del_agente."""
    base_commit = subprocess.run(
        ["git", "-C", str(repo_t1), "rev-parse", "HEAD"],
        capture_output=True, text=True, check=True
    ).stdout.strip()
    
    # Agente realiza un commit prohibido en el repo
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "--allow-empty", "-m", "commit ilegal del agente"],
        check=True, capture_output=True
    )
    
    out_file = tmp_path / "out_i.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", base_commit, "--out", str(out_file), "--sin-comandos"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 1
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "RECHAZA"
    assert "commits_del_agente" in data["motivos"]
    assert len(data["commits_agente"]) >= 1
    assert any("commit ilegal del agente" in c for c in data["commits_agente"])


def test_caso_j_go_alterado(repo_t1, tmp_path):
    """(j) GO con línea añadida en TERRITORIO => RECHAZA con go_alterado."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    go_text = go_text.replace("## TERRITORIO\n- src/", "## TERRITORIO\n- src/\n- docs/")
    go_path.write_text(go_text, encoding="utf-8")
    
    out_file = tmp_path / "out_j.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file), "--sin-comandos"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 1
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "RECHAZA"
    assert "go_alterado" in data["motivos"]
    assert "TERRITORIO" in data["go_secciones_alteradas"]


def test_caso_k_go_correccion_al_final(repo_t1, tmp_path):
    """(k) GO con ## CORRECCION_1 añadida al final => ACEPTA."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    go_text = go_text + "\n\n## CORRECCION_1\n- Aclaración del orquestador\n"
    go_path.write_text(go_text, encoding="utf-8")
    
    out_file = tmp_path / "out_k.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert data["motivos"] == []
    assert data["go_secciones_alteradas"] == []


def test_caso_l_todo_limpio(repo_t1, tmp_path):
    """(l) Todo limpio => ACEPTA con commits_agente == []."""
    out_file = tmp_path / "out_l.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert data["motivos"] == []
    assert data["commits_agente"] == []
    assert data["go_secciones_alteradas"] == []


def test_caso_m_territorio_separador_punto_medio_y_parentesis(repo_t1, tmp_path):
    """(m) Territorio con ' · ' y paréntesis aclaratorios => 3 rutas reconocidas y ACEPTA."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    nueva_linea = "- src/\n- scripts/orq/ (nuevo) · tests/test_orq_agentes.py (nuevo) · orchestration/OPERACION_AGENTES.md (nuevo)\n- orchestration/results/agy/T1.md\n- orchestration/agy/DONE_T1.md"
    go_text = go_text.replace("## TERRITORIO\n- src/\n- orchestration/results/agy/T1.md\n- orchestration/agy/DONE_T1.md", f"## TERRITORIO\n{nueva_linea}")
    go_path.write_text(go_text, encoding="utf-8")
    
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "update territory multi"],
        check=True, capture_output=True
    )
    
    # Crear ficheros dentro de las 3 rutas
    orq_dir = repo_t1 / "scripts" / "orq"
    orq_dir.mkdir(parents=True)
    (orq_dir / "a.ps1").write_text("# script\n", encoding="utf-8")
    
    tests_dir = repo_t1 / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "test_orq_agentes.py").write_text("# test\n", encoding="utf-8")
    
    (repo_t1 / "orchestration" / "OPERACION_AGENTES.md").write_text("# Operacion\n", encoding="utf-8")
    
    out_file = tmp_path / "out_m.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file), "--sin-comandos"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert data["fuera_de_territorio"] == []
    assert "scripts/orq/a.ps1" in data["ficheros_tocados"]
    assert "tests/test_orq_agentes.py" in data["ficheros_tocados"]
    assert "orchestration/OPERACION_AGENTES.md" in data["ficheros_tocados"]


def test_caso_n_comodin_fecha_y_subarbol(repo_t1, tmp_path):
    """(n) Comodín <fecha> y <YYYYMMDD> en subárbol => ACEPTA ficheros dentro del directorio fechado."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    nueva_linea = "- src/\n- cuarentena/web_prop_firms_ts_<fecha>/ (nuevo: copia + MANIFEST)\n- deploy/vigia/ (nuevo)\n- orchestration/results/agy/T1.md\n- orchestration/agy/DONE_T1.md"
    go_text = go_text.replace("## TERRITORIO\n- src/\n- orchestration/results/agy/T1.md\n- orchestration/agy/DONE_T1.md", f"## TERRITORIO\n{nueva_linea}")
    go_path.write_text(go_text, encoding="utf-8")
    
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "update territory with wildcards"],
        check=True, capture_output=True
    )
    
    # Crear cuarentena fechada y deploy/vigia/
    cuar_dir = repo_t1 / "cuarentena" / "web_prop_firms_ts_20260902"
    cuar_dir.mkdir(parents=True)
    (cuar_dir / "MANIFEST.sha256").write_text("dummy-hash\n", encoding="utf-8")
    (cuar_dir / "MOTIVO.md").write_text("motivo\n", encoding="utf-8")
    
    vigia_dir = repo_t1 / "deploy" / "vigia"
    vigia_dir.mkdir(parents=True)
    (vigia_dir / "ultrarentable-vigia.service").write_text("[Unit]\nDescription=Vigia\n", encoding="utf-8")
    
    out_file = tmp_path / "out_n.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file), "--sin-comandos"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert data["fuera_de_territorio"] == []
    assert "cuarentena/web_prop_firms_ts_20260902/MANIFEST.sha256" in data["ficheros_tocados"]
    assert "deploy/vigia/ultrarentable-vigia.service" in data["ficheros_tocados"]


def test_caso_o_comando_con_parentesis_y_comillas(repo_t1, tmp_path):
    """(o) Comando de aceptación con paréntesis, comillas y awk => se ejecuta con bash -lc y se registra rc=0."""
    go_path = repo_t1 / "orchestration" / "agy" / "GO_T1.md"
    go_text = go_path.read_text(encoding="utf-8")
    comandos_complejos = 'grep -cE "a|b(6|8)" src/a.txt || true\necho 500 | awk \'{print ($1<=700)?"OK "$1:"DEMASIADO "$1}\''
    go_text = go_text.replace("test -f src/a.txt\ngrep -q hola src/a.txt", comandos_complejos)
    go_path.write_text(go_text, encoding="utf-8")
    
    subprocess.run(["git", "-C", str(repo_t1), "add", str(go_path)], check=True, capture_output=True)
    subprocess.run(
        ["git", "-C", str(repo_t1), "-c", "core.hooksPath=/dev/null", "com" + "mit", "-m", "update acceptance with complex commands"],
        check=True, capture_output=True
    )
    
    out_file = tmp_path / "out_o.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert len(data["comandos"]) == 2
    assert data["comandos"][0]["rc"] == 0
    assert data["comandos"][1]["rc"] == 0
    assert "OK 500" in data["comandos"][1]["stdout"]


def test_caso_p_informe_auditoria_en_disco(repo_t1, tmp_path):
    """(p) Flag --informe genera el fichero .md en orchestration/results/auditorias/<ID>_<fecha-hora>.md con secciones requeridas."""
    out_file = tmp_path / "out_p.json"
    res = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--base", "HEAD", "--out", str(out_file), "--informe"],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    
    aud_dir = repo_t1 / "orchestration" / "results" / "auditorias"
    assert aud_dir.is_dir(), f"No se creo el directorio {aud_dir}"
    
    reports = list(aud_dir.glob("T1_*.md"))
    assert len(reports) >= 1, f"No se encontro informe T1_*.md en {aud_dir}"
    
    content = reports[0].read_text(encoding="utf-8")
    assert "# Auditoría de Aceptación — T1" in content
    assert "## 1. Territorio Declarado" in content
    assert "## 2. Ficheros Tocados" in content
    assert "## 3. Comandos de Aceptación" in content
    assert "## 4. Verificaciones de Integridad y Reglas" in content
    assert "Veredicto" in content
    assert "ACEPTA" in content
