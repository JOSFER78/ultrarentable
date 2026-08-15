from pathlib import Path

from services.api.app.database import database_health, initialize_database


def test_sqlite_initializes_in_temporary_directory(tmp_path: Path) -> None:
    database_path = tmp_path / "state.sqlite3"
    initialize_database(database_path)
    assert database_path.exists()
    assert database_health(database_path)["status"] == "ONLINE"
