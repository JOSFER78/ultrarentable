from services.api.app.api.certified_summary_router import _explicit_gate_state, _real_oos_months


def test_approved_without_explicit_eleven_gates_is_not_certifiable():
    sc = {"gates_evaluation": {"gate_01": "PASSED"}}
    explicit, passed, certified = _explicit_gate_state(sc)
    assert explicit == 1
    assert passed == 1
    assert certified is False


def test_all_eleven_explicit_and_passed_is_certifiable():
    sc = {"gates_evaluation": {f"gate_{i:02d}": "PASSED" for i in range(1, 12)}}
    explicit, passed, certified = _explicit_gate_state(sc)
    assert explicit == 11
    assert passed == 11
    assert certified is True


def test_missing_duration_is_not_invented():
    assert _real_oos_months({}) is None
    assert _real_oos_months({"duration_info": {}}) is None


def test_duration_can_be_derived_from_real_oos_dates():
    months = _real_oos_months(
        {"duration_info": {"oos_start": "2026-01-01T00:00:00+00:00", "oos_end": "2026-07-01T00:00:00+00:00"}}
    )
    assert months is not None
    assert 5.8 < months < 6.2


def test_master_catalog_export_csv_and_xlsx_structure():
    from services.api.app.db.database import SessionLocal
    from services.export.excel_master_catalog import build_master_catalog_csv, build_master_catalog_xlsx
    
    db = SessionLocal()
    try:
        csv_text = build_master_catalog_csv(db)
        assert len(csv_text) > 0
        assert "Tipo,ID,Nombre,Ruta" in csv_text
        
        xlsx_bytes = build_master_catalog_xlsx(db)
        assert len(xlsx_bytes) > 0
        # Valid ZIP / XLSX magic number PK\x03\x04
        assert xlsx_bytes[:4] == b"PK\x03\x04"
    finally:
        db.close()


