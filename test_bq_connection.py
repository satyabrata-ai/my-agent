#!/usr/bin/env python3
"""Quick test to verify BigQuery connection and list tables"""

from google.cloud import bigquery
import os

# Set project
project_id = "ccibt-hack25ww7-706"
dataset_id = "market_activity"

print(f"Testing BigQuery connection...")
print(f"Project: {project_id}")
print(f"Dataset: {dataset_id}")
print("-" * 80)

try:
    # Create BigQuery client
    client = bigquery.Client(project=project_id)
    print("[OK] BigQuery client created successfully")
    
    # List tables in the dataset
    print(f"\nListing tables in {dataset_id}...")
    dataset_ref = f"{project_id}.{dataset_id}"
    tables = list(client.list_tables(dataset_ref))
    
    if tables:
        print(f"\n[SUCCESS] Found {len(tables)} tables:")
        for table in tables:
            print(f"  - {table.table_id}")
            # Get table info
            table_ref = f"{project_id}.{dataset_id}.{table.table_id}"
            table_obj = client.get_table(table_ref)
            print(f"    Rows: {table_obj.num_rows:,}")
            print(f"    Size: {table_obj.num_bytes / 1024 / 1024:.2f} MB")
    else:
        print("\n[WARNING] No tables found in the dataset")
        print("You need to load your data into BigQuery tables.")
        print("\nExpected tables:")
        print("  - stock_market_data")
        print("  - communications")
        print("  - economic_indicators")
        print("  - stock_news")
        print("  - acquisitions")
        print("  - analyst_ratings")
        print("  - sp500_companies")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] BigQuery connection is working!")
    print("=" * 80)
    
except Exception as e:
    print(f"\n[ERROR] Failed to connect to BigQuery: {e}")
    print("\nTroubleshooting:")
    print("1. Run: gcloud auth application-default login")
    print("2. Run: gcloud config set project ccibt-hack25ww7-706")
    print("3. Verify you have BigQuery access permissions")
    import traceback
    traceback.print_exc()
