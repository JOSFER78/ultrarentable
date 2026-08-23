from pathlib import Path
import re

file_path = Path("services/api/app/api/real_data_router.py")
if not file_path.exists():
    file_path = Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/services/api/app/api/real_data_router.py")

content = file_path.read_text(encoding="utf-8")

old_snippet = """    # 4. Inventario dinámico real de datasets en disco (Cripto, Futuros CME, Forex)
    sqx_imports_dir = Path(__file__).resolve().parents[4] / "data" / "sqx_imports"
    datasets_map: Dict[str, Any] = {}"""

new_snippet = """    # 4. Inventario dinámico real de datasets en disco (Cripto, Futuros CME, Forex)
    possible_sqx_dirs = [
        Path("data/sqx_imports"),
        Path.cwd() / "data" / "sqx_imports",
        Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports"),
        Path(__file__).resolve().parents[0] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[1] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[2] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[3] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[4] / "data" / "sqx_imports",
    ]
    sqx_imports_dir = None
    for p in possible_sqx_dirs:
        if p.exists() and p.is_dir():
            sqx_imports_dir = p.resolve()
            break
    datasets_map: Dict[str, Any] = {}"""

if old_snippet in content:
    content = content.replace(old_snippet, new_snippet)
    file_path.write_text(content, encoding="utf-8")
    print("Successfully patched real_data_router.py with robust sqx_imports_dir resolution!")
else:
    print("Snippet not found exactly, applying regex replace...")
    content = re.sub(
        r'sqx_imports_dir = Path\(__file__\)\.resolve\(\)\.parents\[\d+\] / "data" / "sqx_imports"',
        '''possible_sqx_dirs = [
        Path("data/sqx_imports"),
        Path.cwd() / "data" / "sqx_imports"),
        Path("/home/ubuntu/workspace/pro/trading/01 Ultrarentable/data/sqx_imports"),
        Path(__file__).resolve().parents[0] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[1] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[2] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[3] / "data" / "sqx_imports",
        Path(__file__).resolve().parents[4] / "data" / "sqx_imports",
    ]
    sqx_imports_dir = next((p.resolve() for p in possible_sqx_dirs if p.exists() and p.is_dir()), None)''',
        content
    )
    file_path.write_text(content, encoding="utf-8")
    print("Applied regex replacement in real_data_router.py")
