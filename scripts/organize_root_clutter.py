import os
import shutil
from pathlib import Path

def organize_root():
    project_dir = Path(__file__).resolve().parents[1]

    prompts_archive = project_dir / "prompts" / "archive"
    reports_archive = project_dir / "reports" / "archive"
    docs_archive = project_dir / "docs" / "archive"

    prompts_archive.mkdir(parents=True, exist_ok=True)
    reports_archive.mkdir(parents=True, exist_ok=True)
    docs_archive.mkdir(parents=True, exist_ok=True)

    # File categorization
    prompts_files = [
        "PEGAR_EN_EL_IDE.txt",
        "PEGAR_EN_EL_IDE_V5_1.txt",
        "PROMPT_IDE_AUTOPILOTO_TOTAL_BINGX.md",
        "PROMPT_IDE_CORRECCIONES_C2_Y_FASE_D.md",
        "PROMPT_IDE_CORRECCIONES_E2_F2.md",
        "PROMPT_IDE_FASE_EF_FACTORY_AUTONOMA.md",
        "PROMPT_IDE_V5_1_AUTOPILOTO_REAL_SIN_FALSOS.md",
        "PROMPT_MODIFICACIONES_IDE_LOCAL_REAL_ONLY.md",
    ]

    reports_files = [
        "AUDITORIA_FASES_ABC_V3.md",
        "AUDITORIA_FASES_EF_V4.md",
        "AUDITORIA_TECNICA_ULTRARENTABLE.md",
        "AUDITORIA_V2_LOCAL_REAL_ONLY.md",
        "AUDITORIA_V5_AUTOPILOTO_REAL.md",
        "VALIDACION_PAQUETE_V2.md",
    ]

    docs_files = [
        "ARQUITECTURA_FACTORY_AUTONOMA_BINGX.md",
        "ESPECIFICACION_COMPLETA_BINGX_ULTRARENTABLE.md",
        "PACKAGE_MANIFEST_SHA256.json",
        "REAL_ONLY_START_HERE.md",
        "START_HERE_AUTOPILOTO_TOTAL.md",
        "START_HERE_V3.md",
        "START_HERE_V4_REVIEW.md",
        "START_HERE_V5_1_CORRECTION.md",
    ]

    for fname in prompts_files:
        src = project_dir / fname
        if src.exists():
            shutil.move(str(src), str(prompts_archive / fname))
            print(f"Movido a prompts/archive: {fname}")

    for fname in reports_files:
        src = project_dir / fname
        if src.exists():
            shutil.move(str(src), str(reports_archive / fname))
            print(f"Movido a reports/archive: {fname}")

    for fname in docs_files:
        src = project_dir / fname
        if src.exists():
            shutil.move(str(src), str(docs_archive / fname))
            print(f"Movido a docs/archive: {fname}")

if __name__ == "__main__":
    organize_root()
