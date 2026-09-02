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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file)],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file)],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file), "--sin-comandos"],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file)],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file), "--sin-comandos"],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file)],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file)],
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
        [sys.executable, str(SCRIPT_PATH), "T1", "--worktree", str(repo_t1), "--out", str(out_file)],
        capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    assert res.returncode == 0, f"stdout: {res.stdout}, stderr: {res.stderr}"
    data = json.loads(out_file.read_text(encoding="utf-8"))
    assert data["veredicto"] == "ACEPTA"
    assert not any("error_interno" in m for m in data["motivos"])
    assert len(data["comandos"]) == 1
    assert data["comandos"][0]["rc"] == 0

