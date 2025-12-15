#!/usr/bin/env python3
"""Check the schema of the BigQuery table"""

from google.cloud import bigquery

project_id = "ccibt-hack25ww7-706"
dataset_id = "market_activity"
table_id = "30_yr_stock_market_data"

client = bigquery.Client(project=project_id)
table_ref = f"{project_id}.{dataset_id}.{table_id}"
table = client.get_table(table_ref)

print(f"\nSchema for {table_id}:")
print("=" * 80)
for field in table.schema:
    print(f"  {field.name}: {field.field_type}")

# Also get a sample row
query = f"SELECT * FROM `{table_ref}` LIMIT 1"
df = client.query(query).to_dataframe()
print(f"\nSample row columns:")
print("=" * 80)
print(list(df.columns))
print(f"\nSample data:")
print(df.head())
