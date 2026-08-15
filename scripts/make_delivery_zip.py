import os
import zipfile
from pathlib import Path

def make_delivery_zip():
    project_dir = Path(__file__).resolve().parents[1]
    output_zip = project_dir / "ultrarentable_autopiloto_total_v5_1_final.zip"

    if output_zip.exists():
        output_zip.unlink()

    ignored_patterns = [
        ".venv",
        "node_modules",
        ".next",
        ".git",
        "__pycache__",
        ".pytest_cache",
        "v3",
        "v3_extracted",
        "v4",
        "v4_extracted",
        "v5",
        "v5_extracted",
        "v5.1",
        "v5_1_extracted",
    ]

    count = 0
    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(project_dir):
            # Exclude ignored directories in-place
            dirs[:] = [d for d in dirs if not any(p in d for p in ignored_patterns)]

            for file in files:
                if file.endswith(".zip"):
                    continue
                file_path = Path(root) / file
                rel_path = file_path.relative_to(project_dir)
                z.write(file_path, arcname=str(rel_path).replace("\\", "/"))
                count += 1

    print(f"ZIP v5.1 final creado con exito ({count} archivos con rutas relativas): {output_zip}")

if __name__ == "__main__":
    make_delivery_zip()
