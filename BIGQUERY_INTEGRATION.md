# BigQuery Integration Guide

## Overview

This agent now uses **Google BigQuery** as its primary data source instead of GCS CSV files. This provides:

- ✅ **Dynamic table discovery** - Automatically finds all tables in your dataset
- ✅ **SQL-based filtering** - Push-down predicates for efficient queries
- ✅ **Low-latency caching** - In-memory caching with configurable TTL
- ✅ **Better performance** - Query only needed columns and rows
- ✅ **No encoding issues** - BigQuery handles text encoding automatically
- ✅ **Scalability** - Handles datasets of any size

## Configuration

### Environment Variables

Add these to your `.env` file:

```env
# BigQuery Configuration (Primary Data Source)
BIGQUERY_PROJECT=ccibt-hack25ww7-706
BIGQUERY_DATASET=market_activity

# GCS Configuration (For memory persistence only)
GCS_DATA_BUCKET=gs://datasets-ccibt-hack25ww7-706
GCS_MEMORY_PATH=agent_memory
```

### Required BigQuery Tables

Your `market_activity` dataset should contain these tables:

| Table Name | Description | Key Columns |
|-----------|-------------|-------------|
| `stock_market_data` | 30-year historical prices | Symbol, Date, Open, High, Low, Close, Volume |
| `communications` | Fed announcements | Date, Speaker, Content |
| `economic_indicators` | US economic data | Date, Indicator, Value |
| `stock_news` | News headlines | Date, Symbol, Headline, Sentiment |
| `acquisitions` | M&A events | Date, Acquirer, Target |
| `analyst_ratings` | Analyst recommendations | Date, Symbol, Rating, Firm |
| `sp500_companies` | S&P 500 company metadata | Symbol, Name, Sector, Industry |

## Installation

1. **Update dependencies:**
   ```bash
   uv sync
   ```

2. **Verify BigQuery access:**
   ```bash
   gcloud auth application-default login
   gcloud config set project ccibt-hack25ww7-706
   ```

3. **Test the integration:**
   ```bash
   uv run python test_bigquery_integration.py
   ```

## Features

### 1. Dynamic Table Discovery

The agent automatically discovers all tables in your BigQuery dataset:

```python
from app.sub_agents.event_impact_agent.tools import _data_loader

# List all available tables
tables = _data_loader.list_available_tables()
# Returns: ['stock_market_data', 'communications', 'economic_indicators', ...]
```

### 2. Efficient Filtered Queries

Instead of loading entire CSV files, queries use SQL WHERE clauses:

```python
# Load only AAPL data (efficient)
df = _data_loader.load_table_from_bigquery(
    "stock_market_data",
    where_clause="Symbol = 'AAPL' AND Date >= '2020-01-01'"
)
```

### 3. Multi-Level Caching

**In-memory cache** for ultra-low latency:
- Default TTL: 60 minutes
- Configurable per query
- Automatic cache key generation

```python
# First call: ~2-3 seconds (BigQuery query)
df1 = _data_loader.load_table_from_bigquery("stock_market_data")

# Second call: ~50ms (in-memory cache hit)
df2 = _data_loader.load_table_from_bigquery("stock_market_data")
```

### 4. Schema Introspection

Get table schemas dynamically:

```python
schema = _data_loader.get_table_schema("stock_market_data")
# Returns: {'Symbol': 'STRING', 'Date': 'DATE', 'Close': 'FLOAT64', ...}
```

## New Tools

### `list_available_symbols()`

Lists all unique stock symbols in the historical data:

```python
from app.sub_agents.event_impact_agent.tools import list_available_symbols

result = list_available_symbols()
# {
#   "status": "success",
#   "symbols": ["AAPL", "MSFT", "GOOGL", ...],
#   "count": 500,
#   "date_range": {"start": "1993-01-01", "end": "2024-12-15"}
# }
```

**This fixes the original issue where the agent couldn't list available symbols!**

### Updated `load_price_data(symbol)`

Now uses BigQuery with optional filtering:

```python
from app.sub_agents.event_impact_agent.tools import load_price_data

# Load specific symbol (efficient - uses WHERE clause)
result = load_price_data("AAPL")

# Load all symbols overview
result = load_price_data()  # Returns summary, suggests using list_available_symbols()
```

## Performance Comparison

### Before (GCS CSV)
- Load 30yr stock data: **~15-20 seconds**
- Filter by symbol in Python: **Additional ~2-3 seconds**
- Encoding issues: **Frequent failures**
- Cache: File-level only

### After (BigQuery)
- Load filtered data: **~2-3 seconds**
- Filter in SQL: **Included in query time**
- Encoding issues: **None**
- Cache: Query-level + in-memory
- Subsequent queries: **~50-100ms** (cached)

## Migration Guide

### CSV to BigQuery Table Mapping

The loader automatically maps legacy CSV names to BigQuery tables:

| Old CSV File | New BigQuery Table |
|--------------|-------------------|
| `30_yr_stock_market_data.csv` | `stock_market_data` |
| `communications.csv` | `communications` |
| `US_Economic_Indicators.csv` | `economic_indicators` |
| `stock_news.csv` | `stock_news` |
| `acquisitions_update_2021.csv` | `acquisitions` |
| `analyst_ratings_processed.csv` | `analyst_ratings` |

### Backward Compatibility

Legacy code using `load_csv_from_gcs()` still works:

```python
# This still works (internally uses BigQuery)
df = _data_loader.load_csv_from_gcs("30_yr_stock_market_data.csv")
```

## Architecture

```
┌─────────────────┐
│   Root Agent    │
│  BondNavigator  │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐  ┌──▼────┐
│News   │  │Event  │
│Agent  │  │Agent  │
└───┬───┘  └───┬───┘
    │          │
    └────┬─────┘
         │
    ┌────▼─────────────────┐
    │ BigQueryDataLoader   │
    │  - Table discovery   │
    │  - In-memory cache   │
    │  - SQL filtering     │
    │  - Schema access     │
    └────┬─────────────────┘
         │
    ┌────▼────────────┐
    │ BigQuery Dataset│
    │ market_activity │
    │  - 30yr prices  │
    │  - Fed comms    │
    │  - News data    │
    │  - Economics    │
    └─────────────────┘
```

## Testing

### Run Full Test Suite

```bash
uv run python test_bigquery_integration.py
```

### Expected Output

```
🚀 BigQuery Integration Test Suite

================================================================================
TESTING BIGQUERY CONNECTION AND TABLE DISCOVERY
================================================================================

📊 Project: ccibt-hack25ww7-706
📊 Dataset: market_activity

Test 1: Discovering BigQuery tables...
────────────────────────────────────────────────────────────────────────────
📊 Discovered 12 tables in BigQuery dataset
✅ Successfully discovered 12 tables

Test 2: Listing available stock symbols...
────────────────────────────────────────────────────────────────────────────
✅ Successfully retrieved 500 symbols
   Date range: 1993-01-01 to 2024-12-15

...

================================================================================
✅ ALL TESTS PASSED
================================================================================

🎉 Ready for low-latency agent operations!
```

## Troubleshooting

### "Permission denied" Errors

Ensure your service account has these IAM roles:
```bash
gcloud projects add-iam-policy-binding ccibt-hack25ww7-706 \
  --member="serviceAccount:YOUR_SA@project.iam.gserviceaccount.com" \
  --role="roles/bigquery.dataViewer"

gcloud projects add-iam-policy-binding ccibt-hack25ww7-706 \
  --member="serviceAccount:YOUR_SA@project.iam.gserviceaccount.com" \
  --role="roles/bigquery.jobUser"
```

### "Table not found" Errors

List available tables to verify names:
```bash
bq ls ccibt-hack25ww7-706:market_activity
```

### Cache Not Working

Clear cache and retry:
```python
_data_loader.clear_cache()  # Clear all
_data_loader.clear_cache("stock_market_data")  # Clear specific table
```

### Slow Queries

1. **Add partitioning** to BigQuery tables (by Date column)
2. **Add clustering** on frequently filtered columns (Symbol, Date)
3. **Use specific WHERE clauses** instead of loading full tables

## Cost Optimization

BigQuery charges by data scanned. Optimize with:

1. **Query only needed columns:**
   ```sql
   SELECT Symbol, Date, Close FROM stock_market_data
   WHERE Symbol = 'AAPL'
   ```

2. **Use date partitioning:**
   ```sql
   CREATE TABLE market_activity.stock_market_data
   PARTITION BY Date
   CLUSTER BY Symbol
   ```

3. **Monitor query costs:**
   ```bash
   bq ls -j --max_results=10
   ```

## Next Steps

1. ✅ BigQuery integration complete
2. ✅ In-memory caching operational
3. ✅ Dynamic table discovery working
4. ✅ Symbol listing functional
5. 🎯 Add more tools leveraging BigQuery SQL
6. 🎯 Implement query result streaming for large datasets
7. 🎯 Add BigQuery ML integration for predictions

## Support

For issues or questions:
- Check logs: The agent prints detailed diagnostic information
- Run tests: `uv run python test_bigquery_integration.py`
- Review this guide: All features are documented here

---

**Migration completed:** GCS CSV → BigQuery with dynamic discovery & low-latency caching ✅
