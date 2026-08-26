#!/usr/bin/env python3
"""Fail-closed dependency authority check for R0.1.

The repository has two package managers by design:
- npm: root workspace + apps/web workspace, governed by root package-lock.json.
- Python: pyproject.toml, governed by uv.lock.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def fail(message: str, failures: list[str]) -> None:
    failures.append(message)

def normalize_constraint(value: object) -> object:
    return value.replace(", ", ",").strip() if isinstance(value, str) else value

def check_npm(failures: list[str]) -> None:
    package_path = ROOT / "package.json"
    lock_path = ROOT / "package-lock.json"
    web_package_path = ROOT / "apps" / "web" / "package.json"
    if not package_path.is_file():
        fail("missing root package.json", failures)
        return
    if not lock_path.is_file():
        fail("missing root package-lock.json", failures)
    if not web_package_path.is_file():
        fail("missing apps/web/package.json", failures)
    try:
        package = json.loads(package_path.read_text(encoding="utf-8"))
        lock = json.loads(lock_path.read_text(encoding="utf-8")) if lock_path.is_file() else {}
        web_package = json.loads(web_package_path.read_text(encoding="utf-8")) if web_package_path.is_file() else {}
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid npm manifest/lockfile: {exc}", failures)
        return
    if lock.get("lockfileVersion") != 3:
        fail(f"root package-lock.json must use lockfileVersion 3, got {lock.get('lockfileVersion')!r}", failures)
    root_lock = lock.get("packages", {}).get("")
    if not isinstance(root_lock, dict):
        fail("package-lock.json has no root package entry", failures)
    else:
        for key in ("name", "version", "workspaces"):
            if root_lock.get(key) != package.get(key):
                fail(f"root {key} differs between package.json and package-lock.json", failures)
    if package.get("workspaces") != ["apps/web", "packages/*"]:
        fail("unexpected root workspace authority; expected apps/web and packages/*", failures)
    web_lock = lock.get("packages", {}).get("apps/web")
    if not isinstance(web_lock, dict):
        fail("package-lock.json has no apps/web workspace entry", failures)
    else:
        for key in ("name", "version"):
            if web_lock.get(key) != web_package.get(key):
                fail(f"apps/web {key} differs between package.json and package-lock.json", failures)
    present = [str(path.relative_to(ROOT)) for path in [ROOT / "npm-shrinkwrap.json", ROOT / "pnpm-lock.yaml", ROOT / "yarn.lock"] if path.is_file()]
    if present:
        fail("competing npm lockfile(s): " + ", ".join(present), failures)

def check_python(failures: list[str]) -> None:
    pyproject_path = ROOT / "pyproject.toml"
    uv_lock_path = ROOT / "uv.lock"
    if not pyproject_path.is_file():
        fail("missing pyproject.toml", failures)
        return
    if not uv_lock_path.is_file():
        fail("missing uv.lock", failures)
        return
    try:
        pyproject = tomllib.loads(pyproject_path.read_text(encoding="utf-8"))
        uv_lock = tomllib.loads(uv_lock_path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        fail(f"invalid Python dependency manifest/lockfile: {exc}", failures)
        return
    project = pyproject.get("project", {})
    root_packages = uv_lock.get("package", [])
    if not next((pkg for pkg in root_packages if pkg.get("name") == project.get("name")), None):
        fail("uv.lock has no package entry matching pyproject project.name", failures)
    else:
        if normalize_constraint(project.get("requires-python")) != normalize_constraint(uv_lock.get("requires-python")):
            fail(f"Python requires-python differs: pyproject={project.get('requires-python')!r}, uv.lock={uv_lock.get('requires-python')!r}", failures)
    present = [str(path.relative_to(ROOT)) for path in [ROOT / "requirements.txt", ROOT / "requirements-dev.txt", ROOT / "Pipfile", ROOT / "Pipfile.lock", ROOT / "poetry.lock"] if path.is_file()]
    if present:
        fail("competing Python dependency authority file(s): " + ", ".join(present), failures)

def main() -> int:
    failures: list[str] = []
    check_npm(failures)
    check_python(failures)
    result = {"check": "R0.1_DEPENDENCY_AUTHORITY", "status": "PASS" if not failures else "BLOCKED", "repository_root": str(ROOT), "failures": failures}
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
