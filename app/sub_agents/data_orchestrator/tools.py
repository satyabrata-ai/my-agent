"""Data Orchestrator tools: BigQuery connector, ingestion, and baseline metrics."""
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta

from app.config import config


class BigQueryUnavailable(Exception):
    pass


class BigQueryStore:
    """Light wrapper around BigQuery to run queries and return DataFrames.

    This wrapper lazily imports the BigQuery client so the package can be
    imported in environments without the BigQuery SDK (useful for unit tests).
    """

    def __init__(self, project: Optional[str] = None, dataset: Optional[str] = None):
        self.project = project or config.GOOGLE_CLOUD_PROJECT
        self.dataset = dataset or getattr(config, "BIGQUERY_DATASET", None)
        try:
            from google.cloud import bigquery  # type: ignore

            self.client = bigquery.Client(project=self.project)
            self.bigquery = bigquery
        except Exception as e:  # pragma: no cover - environment dependent
            self.client = None
            self.bigquery = None
            self._import_error = e

    def _ensure_client(self):
        if not self.client:
            raise BigQueryUnavailable(
                "google-cloud-bigquery not available; install and authenticate to use BigQuery features"
            )

    def list_tables(self) -> List[str]:
        self._ensure_client()
        dataset_ref = f"{self.project}.{self.dataset}"
        tables = [t.table_id for t in self.client.list_tables(dataset_ref)]
        return tables

    def query_to_df(self, sql: str, limit: Optional[int] = None) -> pd.DataFrame:
        self._ensure_client()
        if limit:
            sql = f"SELECT * FROM ({sql}) LIMIT {limit}"
        job = self.client.query(sql)
        return job.to_dataframe()


# High-level tool functions exposed to the agent
_bq_store = BigQueryStore()


def discover_bq_tables() -> Dict[str, Any]:
    """Return a simple inventory of tables in the configured dataset."""
    try:
        tables = _bq_store.list_tables()
        return {"status": "success", "dataset": _bq_store.dataset, "tables": tables}
    except BigQueryUnavailable as e:
        return {"status": "error", "message": str(e)}


def query_table(sql: str, limit: int = 1000) -> Dict[str, Any]:
    """Run a SQL query against BigQuery and return data in JSON-friendly format."""
    try:
        df = _bq_store.query_to_df(sql, limit=limit)
        return {"status": "success", "rows": df.head(1000).to_dict(orient="records"), "row_count": len(df)}
    except BigQueryUnavailable as e:
        return {"status": "error", "message": str(e)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_baseline_metrics(ticker: str, price_table: Optional[str] = None, lookback_days: int = 5) -> Dict[str, Any]:
    """Compute baseline metrics such as latest price and realized volatility over lookback_days.

    This function expects a price table with columns: date, ticker, close
    """
    ticker = ticker.upper()
    # Best-effort: allow caller to pass table, else try common table names
    candidate_tables = [price_table] if price_table else [
        f"{_bq_store.dataset}.stock_prices",
        f"{_bq_store.dataset}.prices",
        f"{_bq_store.dataset}.market_prices",
    ]

    for table in candidate_tables:
        if not table:
            continue
        sql = f"SELECT date, ticker, close FROM `{_bq_store.project}.{table}` WHERE ticker = '{ticker}' ORDER BY date DESC LIMIT 1000"
        try:
            df = _bq_store.query_to_df(sql)
        except Exception:
            df = pd.DataFrame()

        if df.empty:
            continue

        # Normalize and compute returns
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        df = df.sort_values('date')
        df = df.dropna(subset=['close'])
        df['return'] = df['close'].pct_change()

        # Helper: compute realized volatility for given lookback (in days)
        def realized_vol(df_local: pd.DataFrame, days: int) -> float:
            end_date = df_local['date'].max()
            start_date = end_date - pd.Timedelta(days=days)
            recent = df_local[df_local['date'] >= start_date]
            if recent.empty or recent['return'].dropna().empty:
                return 0.0
            # Vol of daily returns; annualize assuming 252 trading days
            vol_daily = float(recent['return'].std(skipna=True) or 0.0)
            return vol_daily * (252 ** 0.5)

        # Moving averages
        df['ma_5'] = df['close'].rolling(window=5).mean()
        df['ma_20'] = df['close'].rolling(window=20).mean()

        latest_price = float(df['close'].iloc[-1])

        output = {
            "Ticker": ticker,
            "Price": latest_price,
            "HistVol_1D_Ann": realized_vol(df, 1),
            "HistVol_5D_Ann": realized_vol(df, 5),
            "HistVol_30D_Ann": realized_vol(df, 30),
            "MA_5": float(df['ma_5'].iloc[-1]) if not pd.isna(df['ma_5'].iloc[-1]) else None,
            "MA_20": float(df['ma_20'].iloc[-1]) if not pd.isna(df['ma_20'].iloc[-1]) else None,
            "SamplePoints": len(df),
            "SourceTable": table,
        }
        return {"status": "success", "result": output}

    return {"status": "no_data", "message": f"No price data found for {ticker} in candidate tables"}


def list_upcoming_events(days_ahead: int = 7) -> Dict[str, Any]:
    """Return upcoming events from event tables if available in BigQuery.

    This is a lightweight implementation that searches common event table names.
    """
    candidate_tables = [
        f"{_bq_store.dataset}.events",
        f"{_bq_store.dataset}.event_calendar",
        f"{_bq_store.dataset}.corporate_events",
    ]

    today = datetime.utcnow().date()
    end = today + timedelta(days=days_ahead)

    events = []
    for table in candidate_tables:
        if not table:
            continue
        sql = (
            f"SELECT date, ticker, event_type, metadata FROM `{_bq_store.project}.{table}` "
            f"WHERE date BETWEEN '{today.isoformat()}' AND '{end.isoformat()}' LIMIT 1000"
        )
        try:
            df = _bq_store.query_to_df(sql)
        except Exception:
            df = pd.DataFrame()

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
            for _, row in df.iterrows():
                events.append({
                    "date": str(row.get('date')),
                    "ticker": row.get('ticker'),
                    "event": row.get('event_type'),
                    "metadata": row.get('metadata')
                })

    return {"status": "success", "events": events}


def get_sentiment_sources(ticker: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    """Return rows from the canonical tables used for sentiment analysis.

    This helper restricts access to the explicit set of tables that the
    News Sentiment agent is allowed to query when invoking the Data
    Orchestrator. Only the following tables are accessed:
      - stock_news
      - 30_yr_stock_market_data
      - US_Economic_Indicators
      - combined_transcripts

    Args:
        ticker: optional ticker to filter results where applicable
        limit: maximum rows per table

    Returns:
        dict with per-table results and status
    """
    allowed = {
        "stock_news": "stock_news",
        "market_data": "30_yr_stock_market_data",
        "economic": "US_Economic_Indicators",
        "transcripts": "combined_transcripts",
    }

    out = {"status": "success", "tables": {}}

    for key, table_name in allowed.items():
        full_table = f"{_bq_store.project}.{_bq_store.dataset}.{table_name}"
        # Build a permissive SELECT that applies ticker filter when provided
        where = f"WHERE UPPER(ticker) = '{ticker.upper()}'" if ticker else ""
        sql = f"SELECT * FROM `{full_table}` {where} LIMIT {limit}"
        try:
            df = _bq_store.query_to_df(sql)
            rows = df.head(limit).to_dict(orient="records") if not df.empty else []
            out["tables"][key] = {"row_count": len(rows), "rows": rows}
        except Exception as e:
            out["tables"][key] = {"row_count": 0, "rows": [], "error": str(e)}

    return out


def get_table_rows(table_name: str, ticker: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    """Return rows from a specific BigQuery table using the Data Orchestrator.

    This is a minimal, auditable access point for other agents to read
    required tables (e.g., economic, market, index tables).
    """
    full_table = f"{_bq_store.project}.{_bq_store.dataset}.{table_name}"
    where = f"WHERE UPPER(ticker) = '{ticker.upper()}'" if ticker else ""
    sql = f"SELECT * FROM `{full_table}` {where} LIMIT {limit}"
    try:
        df = _bq_store.query_to_df(sql)
        rows = df.head(limit).to_dict(orient='records') if not df.empty else []
        return {"status": "success", "row_count": len(rows), "rows": rows}
    except Exception as e:
        return {"status": "error", "message": str(e), "row_count": 0, "rows": []}


def get_market_economic_data(ticker: Optional[str] = None, limit: int = 1000) -> Dict[str, Any]:
    """Fetch canonical market & economic tables used by downstream agents.

    Returns a dict with keys: `market` -> 30_yr_stock_market_data,
    `economic` -> US_Economic_Indicators, `index` -> indexData
    """
    tables = {
        "market": "30_yr_stock_market_data",
        "economic": "US_Economic_Indicators",
        "index": "indexData",
    }
    out = {"status": "success", "tables": {}}
    for key, tbl in tables.items():
        out_tbl = get_table_rows(tbl, ticker=ticker, limit=limit)
        out["tables"][key] = out_tbl
    return out


__all__ = [
    "discover_bq_tables",
    "query_table",
    "get_baseline_metrics",
    "list_upcoming_events",
    "clean_price_dataframe",
    "compute_event_impact",
    "get_sentiment_sources",
    "get_table_rows",
    "get_market_economic_data",
]


def clean_price_dataframe(df):
    """Clean and normalize a price DataFrame.

    - Parse `date` column to datetimes
    - Uppercase `ticker` column
    - Sort by date and drop duplicate dates (keep last)
    - Ensure `close` is numeric and drop rows without price
    """
    df = df.copy()
    if 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
    if 'ticker' in df.columns:
        df['ticker'] = df['ticker'].astype(str).str.upper()
    if 'close' in df.columns:
        df['close'] = pd.to_numeric(df['close'], errors='coerce')
    # Drop rows missing required fields
    df = df.dropna(subset=['date', 'close'])
    df = df.sort_values('date')
    # Remove duplicate dates (keep last)
    df = df[~df.duplicated(subset=['date'], keep='last')]
    return df.reset_index(drop=True)


def compute_event_impact(ticker: str, event_type: str, pre_window_days: int = 1, post_window_days: int = 1, price_table: Optional[str] = None, event_table: Optional[str] = None) -> Dict[str, Any]:
    """Compute historical average price move around specified events for a ticker.

    For each event occurrence, compute return from close price `pre_window_days` before
    the event to `post_window_days` after the event, then aggregate statistics.
    """
    ticker = ticker.upper()
    event_table_candidates = [event_table] if event_table else [
        f"{_bq_store.dataset}.events",
        f"{_bq_store.dataset}.event_calendar",
    ]
    price_table_candidates = [price_table] if price_table else [
        f"{_bq_store.dataset}.stock_prices",
        f"{_bq_store.dataset}.prices",
    ]

    # Load events
    events = []
    for et in event_table_candidates:
        if not et:
            continue
        sql = (
            f"SELECT date, ticker, event_type FROM `{_bq_store.project}.{et}` "
            f"WHERE event_type LIKE '%{event_type}%' AND ticker = '{ticker}' LIMIT 1000"
        )
        try:
            df_ev = _bq_store.query_to_df(sql)
        except Exception:
            df_ev = pd.DataFrame()
        if not df_ev.empty:
            df_ev['date'] = pd.to_datetime(df_ev['date'], errors='coerce')
            events.extend(df_ev.to_dict(orient='records'))

    if not events:
        return {"status": "no_events", "message": f"No events of type {event_type} for {ticker}"}

    # Load price history once
    price_df = pd.DataFrame()
    for pt in price_table_candidates:
        if not pt:
            continue
        sql = f"SELECT date, ticker, close FROM `{_bq_store.project}.{pt}` WHERE ticker='{ticker}' ORDER BY date"
        try:
            price_df = _bq_store.query_to_df(sql)
        except Exception:
            price_df = pd.DataFrame()
        if not price_df.empty:
            break

    if price_df.empty:
        return {"status": "no_price_data", "message": f"No price data for {ticker}"}

    price_df = clean_price_dataframe(price_df)
    price_df = price_df.set_index('date')

    impacts = []
    for ev in events:
        ev_date = ev.get('date')
        if not ev_date:
            continue
        # ensure datetime
        ev_date = pd.to_datetime(ev_date)
        pre_date = ev_date - pd.Timedelta(days=pre_window_days)
        post_date = ev_date + pd.Timedelta(days=post_window_days)
        # find closest dates in price_df
        try:
            pre_close = price_df.loc[:pre_date]['close'].iloc[-1]
            post_close = price_df.loc[:post_date]['close'].iloc[-1]
            ret = (post_close - pre_close) / pre_close
            impacts.append(float(ret))
        except Exception:
            continue

    if not impacts:
        return {"status": "no_impact_data", "message": "No matching price windows for events"}

    import statistics
    avg_move = statistics.mean(impacts)
    std_move = statistics.pstdev(impacts) if len(impacts) > 1 else 0.0

    return {
        "status": "success",
        "ticker": ticker,
        "event_type": event_type,
        "average_move": avg_move,
        "std_move": std_move,
        "count": len(impacts),
    }
