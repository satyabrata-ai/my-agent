"""Simple script to check BigQuery dataset access and list tables.

Usage:
  python scripts/check_bq_access.py

Requires: google-cloud-bigquery and valid GCP application default credentials.
"""
import sys
from app.config import config

def main():
    dataset = getattr(config, "BIGQUERY_DATASET", None)
    if not dataset:
        print("BIGQUERY_DATASET not configured in app.config or .env")
        sys.exit(1)

    try:
        from google.cloud import bigquery
    except Exception as e:
        print("google-cloud-bigquery not installed. Install with: pip install google-cloud-bigquery")
        print("Error:", e)
        sys.exit(1)

    try:
        client = bigquery.Client()
        project = client.project
        ds_ref = f"{project}.{dataset}"
        print(f"Listing tables in dataset: {ds_ref}")
        tables = list(client.list_tables(ds_ref))
        if not tables:
            print("No tables found or dataset not accessible.")
            sys.exit(0)
        for t in tables[:20]:
            print(f" - {t.table_id}")

        # Try querying the first table for a sample row
        first_table = tables[0].table_id
        sql = f"SELECT * FROM `{project}.{dataset}.{first_table}` LIMIT 5"
        print(f"\nQuerying sample rows from {first_table}...\n")
        try:
            df = client.query(sql).to_dataframe()
            print(df.head().to_string())
        except Exception as inner_e:
            msg = str(inner_e)
            if 'db-dtypes' in msg or 'Please install the' in msg:
                print("BigQuery returned an error: it looks like the 'db-dtypes' package is missing.")
                print("Install it into your environment with: python -m pip install db-dtypes")
                sys.exit(1)
            raise
    except Exception as e:
        print("Error accessing BigQuery:", e)
        print("Tip: run 'gcloud auth application-default login' or ensure ADC are set.")
        sys.exit(1)

if __name__ == '__main__':
    main()
