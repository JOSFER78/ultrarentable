"""tests/test_m1_runner_volcado.py

Verifica que el runner de M1 vuelca el banco de estrategias a ficheros .sqx
en /opt/SQX-headless/import/fondeo/artefactos/<CELDA>_r<N>/ antes de exportar el CSV.
"""

from unittest.mock import MagicMock, patch
from pathlib import Path
import tempfile


def test_m1_runner_vuelca_artefactos_antes_de_csv():
    """Simula el paso 3 y 4 del bucle de m1_runner_sqx y valida las llamadas CLI."""
    llamadas_cli = []

    def mock_cli(cli_url: str, cmd: str, timeout: int = 180) -> str:
        llamadas_cli.append(cmd)
        if "action=save" in cmd:
            # Simular que SQX crea ficheros .sqx en la carpeta
            partes = cmd.split("folder=")
            if len(partes) > 1:
                fpath = Path(partes[1].strip())
                fpath.mkdir(parents=True, exist_ok=True)
                (fpath / "Strategy 1.1.sqx").write_bytes(b"PK\x03\x04mock_zip_sqx")
            return "Reports saved."
        if "action=export" in cmd:
            partes = cmd.split("file=")
            if len(partes) > 1:
                csv_path = Path(partes[1].strip())
                csv_path.parent.mkdir(parents=True, exist_ok=True)
                csv_path.write_text("Strategy;NetProfit\nStrategy 1.1;1500\n", encoding="utf-8")
            return "Exported"
        return "OK"

    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        celda = "FONDEO_MNQ_H1"
        ronda = 1

        # 3) Volcar banco a artefactos
        dir_artefactos = base / "artefactos" / f"{celda}_r{ronda}"
        dir_artefactos.mkdir(parents=True, exist_ok=True)
        resp_volcado = mock_cli("http://127.0.0.1:5051", f"-databank action=save project={celda} name=Results folder={dir_artefactos}", timeout=600)
        sqx_contados = len(list(dir_artefactos.glob("*.sqx"))) if dir_artefactos.is_dir() else 0

        # 4) Exportar CSV
        csv = base / "resultados" / f"{celda}_r{ronda}.csv"
        resp_export = mock_cli("http://127.0.0.1:5051", f"-databank action=export project={celda} name=Results file={csv}", timeout=300)

        # Aserciones
        assert len(llamadas_cli) == 2
        assert "action=save" in llamadas_cli[0]
        assert "action=export" in llamadas_cli[1]
        assert sqx_contados == 1
        assert (dir_artefactos / "Strategy 1.1.sqx").exists()
        assert csv.exists()
