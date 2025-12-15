import os
import time
import pytest


def skip_if_not_enabled():
    return os.getenv("RUN_REALTIME_MIGRATE_TEST") != "1"


@pytest.mark.skipif(skip_if_not_enabled(), reason="Integration test for migration (opt-in via RUN_REALTIME_MIGRATE_TEST=1)")
def test_migrate_realtime_alerts_creates_table():
    """Run the migration against a real BigQuery project (requires ADC).

    This test is opt-in (set `RUN_REALTIME_MIGRATE_TEST=1`) and will create a
    temporary dataset, run the migration, assert the table exists, and clean up.
    """
    from google.cloud import bigquery
    from app.config import config
    from scripts import migrate_realtime_alerts as migrator

    client = bigquery.Client(project=config.GOOGLE_CLOUD_PROJECT)

    # create temporary dataset
    ts = int(time.time())
    temp_dataset_id = f"realtime_alerts_test_{ts}"
    dataset_ref = bigquery.Dataset(f"{client.project}.{temp_dataset_id}")
    dataset_ref.location = config.GOOGLE_CLOUD_LOCATION
    client.create_dataset(dataset_ref)

    # Monkeypatch config to point to the temp dataset
    orig_dataset = config.BIGQUERY_DATASET
    config.BIGQUERY_DATASET = temp_dataset_id

    try:
        # load and render DDL
        template = migrator.load_template()
        ddl = migrator.render_sql(template, config.GOOGLE_CLOUD_PROJECT, config.BIGQUERY_DATASET)
        # execute
        migrator.run(ddl, dry_run=False)

        # verify table exists
        table_id = f"{config.GOOGLE_CLOUD_PROJECT}.{config.BIGQUERY_DATASET}.realtime_alerts"
        tbl = client.get_table(table_id)
        assert tbl.table_id == "realtime_alerts"
    finally:
        # cleanup: delete table and dataset
        try:
            client.delete_table(table_id, not_found_ok=True)
        except Exception:
            pass
        client.delete_dataset(f"{client.project}.{temp_dataset_id}", delete_contents=True, not_found_ok=True)
        config.BIGQUERY_DATASET = orig_dataset
