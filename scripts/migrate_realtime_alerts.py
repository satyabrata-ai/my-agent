"""Create the `realtime_alerts` BigQuery table from the SQL template.

Usage:
    python scripts/migrate_realtime_alerts.py [--dry-run]

This script reads the deployment SQL template and executes it against the
configured GCP project and dataset from `app.config.config`.
"""
from pathlib import Path
import argparse
from app.config import config


def load_template() -> str:
    path = Path(__file__).parent.parent / "deployment" / "terraform" / "sql" / "realtime_alerts.sql"
    return path.read_text()


def render_sql(template: str, project_id: str, dataset_id: str) -> str:
    return template.replace("${project_id}", project_id).replace("${dataset_id}", dataset_id)


def run(ddl: str, dry_run: bool = False):
    if dry_run:
        print("DRY RUN - DDL to execute:\n")
        print(ddl)
        return

    try:
        from google.cloud import bigquery
    except Exception as e:
        raise RuntimeError("google-cloud-bigquery not available: %s" % e)

    client = bigquery.Client(project=config.GOOGLE_CLOUD_PROJECT)
    job = client.query(ddl)
    job.result()  # wait
    print("✅ Created/updated realtime_alerts table")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dry-run", action="store_true", help="Print DDL without executing")
    args = p.parse_args()

    template = load_template()
    ddl = render_sql(template, config.GOOGLE_CLOUD_PROJECT, config.BIGQUERY_DATASET)
    run(ddl, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
