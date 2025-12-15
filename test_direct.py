#!/usr/bin/env python3
"""Direct test without agent imports"""
from google.cloud import bigquery
import pandas as pd

project_id = "ccibt-hack25ww7-706"
dataset_id = "market_activity"

print("="*80)
print("DIRECT BIGQUERY TEST")
print("="*80)

client = bigquery.Client(project=project_id)

# Test: List instruments
print("\nTest 1: Getting available instruments...")
table_ref = f"{project_id}.{dataset_id}.30_yr_stock_market_data"
table = client.get_table(table_ref)
instruments = [f.name for f in table.schema if f.name not in ['Date', 'id']]

print(f"[OK] Found {len(instruments)} instruments")
print(f"\nCategories:")
indices = [i for i in instruments if any(x in i for x in ['Dow', 'Nasdaq', 'S&P', 'Russell', 'DAX'])]
commodities = [i for i in instruments if any(x in i for x in ['Cocoa', 'Coffee', 'Corn'])]
treasuries = [i for i in instruments if 'Treasury' in i]
print(f"  Indices: {len(indices)} (e.g., {indices[:3]})")
print(f"  Commodities: {len(commodities)} (e.g., {commodities[:3]})")
print(f"  Treasuries: {len(treasuries)} ({treasuries})")

# Test: Load data for Dow Jones
print("\nTest 2: Loading data for Dow Jones...")
query = f"""
SELECT Date, `Dow Jones`
FROM `{table_ref}`
ORDER BY Date DESC
LIMIT 10
"""
df = client.query(query).to_dataframe()
print(f"[OK] Loaded {len(df)} rows")
print(f"   Date range: {df['Date'].min()} to {df['Date'].max()}")
print(f"   Sample values:\n{df.head()}")

print("\n" + "="*80)
print("[SUCCESS] BigQuery connection working perfectly!")
print("="*80)
print("\nYour BigQuery dataset contains:")
print(f"  - {len(instruments)} market instruments")
print(f"  - Market indices (Dow, S&P 500, Nasdaq, etc.)")
print(f"  - Commodities (Gold, Oil, Coffee, etc.)")  
print(f"  - Treasury yields (5Y, 10Y, 30Y)")
print(f"\nData is structured with instruments as COLUMNS, not rows")
print(f"Each row represents a date with values for all instruments")
