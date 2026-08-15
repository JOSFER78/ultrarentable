#!/usr/bin/env python
"""
Clean Installation & Verification Script for Ultrarentable Autopiloto (v5)
Initializes an isolated temporary SQLite DB and executes pytest.
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path

def main() -> int:
    print("=" * 70)
    print("VERIFICACION DE INSTALACION LIMPIA - ULTRARENTABLE V5")
    print("=" * 70)

    # 1. Create temporary directory
    with tempfile.TemporaryDirectory(prefix="ultra_clean_test_") as tmp_dir:
        tmp_db_path = Path(tmp_dir) / "clean_test.sqlite3"
        print(f"Directorio temporal de prueba: {tmp_dir}")
        print(f"Base de datos aislada: {tmp_db_path}")

        # Set environment variable for tests
        env = os.environ.copy()
        env["ULTRA_TEST_DB_PATH"] = str(tmp_db_path)

        # 2. Run pytest with isolated env
        cmd = [sys.executable, "-m", "pytest", "services/api/tests", "-v", "--tb=short"]
        print(f"Ejecutando suite de pruebas: {' '.join(cmd)}")
        result = subprocess.run(cmd, env=env)

        if result.returncode == 0:
            print("\n[OK] TODAS LAS PRUEBAS PASARON CORRECTAMENTE DESDE UNA INSTALACION LIMPIA.")
        else:
            print(f"\n[ERROR] ALGUNAS PRUEBAS FALLARON (codigo de salida: {result.returncode}).")

        return result.returncode

if __name__ == "__main__":
    sys.exit(main())
