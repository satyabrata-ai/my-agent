def test_realtime_alerts_sql_exists_and_has_expected_columns():
    from pathlib import Path
    path = Path(__file__).parent.parent.parent / "deployment" / "terraform" / "sql" / "realtime_alerts.sql"
    assert path.exists(), f"Missing SQL migration: {path}"

    txt = path.read_text()
    assert "CREATE TABLE" in txt
    assert "realtime_alerts" in txt
    assert "details JSON" in txt
    assert "PARTITION BY DATE(timestamp)" in txt