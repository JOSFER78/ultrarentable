import os
import zipfile
from pathlib import Path

def test_zip_preserves_directory_structure() -> None:
    """Delivery ZIP files must preserve directory paths and not be flattened to root."""
    project_dir = Path(__file__).parent.parent.parent.parent
    zip_files = list(project_dir.glob("*.zip"))

    if not zip_files:
        return  # Skipped if no ZIP built yet

    for zip_path in zip_files:
        with zipfile.ZipFile(zip_path, "r") as z:
            names = z.namelist()
            # Ensure key nested files exist with full directory paths
            has_web_page = any("apps/web/app/page.tsx" in n or "apps\\web\\app\\page.tsx" in n for n in names)
            has_api_main = any("services/api/app/main.py" in n or "services\\api\\app\\main.py" in n for n in names)

            # Ensure no flattened root duplicates for page.tsx
            root_page_count = sum(1 for n in names if n == "page.tsx")

            assert root_page_count <= 1, f"ZIP {zip_path.name} is flattened into root!"
            assert has_web_page, f"ZIP {zip_path.name} missing apps/web/app/page.tsx path!"
            assert has_api_main, f"ZIP {zip_path.name} missing services/api/app/main.py path!"
