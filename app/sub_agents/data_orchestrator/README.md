# Data Orchestrator Agent

Provides BigQuery-backed data discovery, ingestion, and baseline metric calculations for downstream agents.

Key tools:
- `discover_bq_tables()` — list tables in configured BigQuery dataset
- `query_table(sql, limit=1000)` — run SQL and return rows
- `get_baseline_metrics(ticker, price_table=None, lookback_days=5)` — returns latest price and realized volatility
- `list_upcoming_events(days_ahead=7)` — returns events in the next N days

Configuration:
- Set `BIGQUERY_DATASET` in `.env` (defaults to `market_activity` if not provided).

Notes:
- If `google-cloud-bigquery` is not installed or credentials are not available, the tools return an error-style dict to aid local development and testing.

Dev setup & testing:
- Create a Python virtualenv (Windows):
	- `python -m venv .venv`
	- `.\.venv\Scripts\Activate.ps1`
	- `python -m pip install -r requirements-dev.txt`
- Run tests: `pytest tests/unit -q`
