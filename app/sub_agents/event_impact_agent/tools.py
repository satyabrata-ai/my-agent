# app/sub_agents/event_impact_agent/tools.py
"""
Event Impact Correlation tools for analyzing historical market reactions to financial events.
Correlates events from multiple datasets with price movements.
Includes bond volatility analysis with robust GCS caching for low latency.

Cross-platform compatible: Works on Windows, Linux, and macOS.
"""

import pandas as pd
import numpy as np
from google.cloud import bigquery
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
from functools import lru_cache
import hashlib
import platform
import sys

from app.config import config

# Platform detection for cross-platform compatibility
PLATFORM = platform.system()  # 'Windows', 'Linux', 'Darwin' (macOS)
IS_WINDOWS = PLATFORM == 'Windows'
IS_LINUX = PLATFORM == 'Linux'
IS_MACOS = PLATFORM == 'Darwin'


def sanitize_for_json(obj):
    """
    Recursively convert NaN, Inf values to None for JSON serialization.
    Handles dictionaries, lists, pandas DataFrames, and numpy types.
    
    This is critical for ADK agents as Gemini API requires valid JSON
    and cannot accept NaN values which are common in pandas DataFrames.
    """
    if isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    elif isinstance(obj, (np.integer, np.int64, np.int32)):
        return int(obj)
    elif isinstance(obj, (np.floating, np.float64, np.float32)):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return float(obj)
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    elif isinstance(obj, pd.DataFrame):
        # Replace NaN with None in DataFrame and convert to records
        df_clean = obj.replace([np.nan, np.inf, -np.inf], None)
        return df_clean.to_dict('records')
    elif pd.isna(obj):  # Handles pandas NA types
        return None
    return obj


class BigQueryDataLoader:
    """
    Intelligent data loader for event and price datasets from BigQuery.
    Dynamically discovers tables and handles multi-level caching for ultra-low latency access.
    
    Cross-platform compatible: Works on Windows, Linux, and macOS.
    """
    
    def __init__(self):
        """Initialize BigQuery client and cache"""
        self.bq_client = bigquery.Client(project=config.BIGQUERY_PROJECT)
        self.project_id = config.BIGQUERY_PROJECT
        self.dataset_id = config.BIGQUERY_DATASET
        self._memory_cache = {}  # In-memory cache for immediate access
        self._cache_metadata = {}  # Track cache freshness
        self._available_tables = None  # Cache of available tables
        self._table_list_time = None  # When we last listed tables
        
        print(f"[BigQuery] Data Loader initialized with caching")
        print(f"   Platform: {PLATFORM} ({'Windows' if IS_WINDOWS else 'Linux' if IS_LINUX else 'macOS' if IS_MACOS else 'Unknown'})")
        print(f"   Project: {self.project_id}")
        print(f"   Dataset: {self.dataset_id}")
        print(f"   Data Source: BigQuery (SQL-based)")
    
    def _get_cache_key(self, table_name: str, where_clause: Optional[str] = None) -> str:
        """Generate cache key for a table/query"""
        key_string = f"{table_name}:{where_clause or 'full'}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_key: str, cache_ttl_minutes: int) -> bool:
        """Check if cache entry is still valid"""
        if cache_key not in self._cache_metadata:
            return False
        cache_time = self._cache_metadata[cache_key]
        age_minutes = (datetime.now() - cache_time).total_seconds() / 60
        return age_minutes < cache_ttl_minutes
    
    def list_available_tables(self, refresh: bool = False) -> List[str]:
        """
        List all available tables in the BigQuery dataset
        
        Args:
            refresh: Force refresh the table list
            
        Returns:
            List of table names
        """
        # Use cached list if available and less than 5 minutes old
        if not refresh and self._available_tables and self._table_list_time:
            age_minutes = (datetime.now() - self._table_list_time).total_seconds() / 60
            if age_minutes < 5:
                return self._available_tables
        
        try:
            dataset_ref = f"{self.project_id}.{self.dataset_id}"
            tables = list(self.bq_client.list_tables(dataset_ref))
            table_names = [table.table_id for table in tables]
            
            self._available_tables = table_names
            self._table_list_time = datetime.now()
            
            print(f"[BigQuery] Discovered {len(table_names)} tables in BigQuery dataset")
            for table_name in sorted(table_names):
                print(f"   • {table_name}")
            
            return table_names
        except Exception as e:
            print(f"❌ Error listing tables: {e}")
            return []
    
    def load_table_from_bigquery(
        self, 
        table_name: str, 
        where_clause: Optional[str] = None,
        use_cache: bool = True, 
        cache_ttl_minutes: int = 60
    ) -> pd.DataFrame:
        """
        Load table from BigQuery with optional filtering and caching
        
        Args:
            table_name: Name of the BigQuery table to load
            where_clause: Optional SQL WHERE clause (without 'WHERE' keyword)
            use_cache: Whether to use cached data if available
            cache_ttl_minutes: Cache time-to-live in minutes
            
        Returns:
            DataFrame containing the table data
            
        Example:
            # Load full table
            df = loader.load_table_from_bigquery("stock_market_data")
            
            # Load with filter
            df = loader.load_table_from_bigquery(
                "stock_market_data", 
                where_clause="Symbol = 'AAPL' AND Date >= '2020-01-01'"
            )
        """
        cache_key = self._get_cache_key(table_name, where_clause)
        
        # Check in-memory cache first (fastest)
        if use_cache and cache_key in self._memory_cache:
            if self._is_cache_valid(cache_key, cache_ttl_minutes):
                age_minutes = (datetime.now() - self._cache_metadata[cache_key]).total_seconds() / 60
                print(f"[CACHE HIT] Using cached data for {table_name} (age: {age_minutes:.1f} min)")
                return self._memory_cache[cache_key].copy()
            else:
                age_minutes = (datetime.now() - self._cache_metadata[cache_key]).total_seconds() / 60
                print(f"[CACHE EXPIRED] Cache expired for {table_name} (age: {age_minutes:.1f} min)")
        
        try:
            # Build SQL query
            query = f"""
            SELECT *
            FROM `{self.project_id}.{self.dataset_id}.{table_name}`
            """
            
            if where_clause:
                query += f"\nWHERE {where_clause}"
            
            print(f"[LOADING] Loading {table_name} from BigQuery...")
            if where_clause:
                print(f"   Filter: {where_clause[:100]}...")
            
            # Execute query and load into DataFrame
            df = self.bq_client.query(query).to_dataframe()
            
            print(f"[SUCCESS] Loaded {len(df):,} rows from {table_name}")
            print(f"   Columns: {len(df.columns)} ({', '.join(list(df.columns)[:5])}...)")
            
            # Update cache
            if use_cache:
                self._memory_cache[cache_key] = df.copy()
                self._cache_metadata[cache_key] = datetime.now()
                print(f"[CACHED] Cached {table_name} for {cache_ttl_minutes} minutes")
            
            return df
            
        except Exception as e:
            print(f"[ERROR] Error loading {table_name}: {e}")
            print(f"   Project: {self.project_id}")
            print(f"   Dataset: {self.dataset_id}")
            print(f"   Table: {table_name}")
            if where_clause:
                print(f"   WHERE clause: {where_clause}")
            raise
    
    def load_csv_from_gcs(self, filename: str, use_cache: bool = True, cache_ttl_minutes: int = 60) -> pd.DataFrame:
        """
        Legacy compatibility method - maps CSV filenames to BigQuery tables
        
        Args:
            filename: CSV filename (will be converted to table name)
            use_cache: Whether to use cached data
            cache_ttl_minutes: Cache TTL in minutes
            
        Returns:
            DataFrame from BigQuery table
        """
        # Map common CSV filenames to BigQuery table names (matches actual table names in BigQuery)
        csv_to_table_map = {
            "30_yr_stock_market_data.csv": "30_yr_stock_market_data",
            "communications.csv": "communications",
            "US_Economic_Indicators.csv": "US_Economic_Indicators",
            "us_economic_indicators.csv": "US_Economic_Indicators",
            "stock_news.csv": "stock_news",
            "acquisitions_update_2021.csv": "acquisitions_update_2021",
            "analyst_ratings_processed.csv": "analyst_ratings",
            "sp500_companies.csv": "sp500_companies",
            "symbols_valid_meta.csv": "symbols_valid_meta",
            "dataset_summary.csv": "dataset_summary",
            "indexdata.csv": "indexData",
            "combined_transcripts.csv": "combined_transcripts",
            "transcripts_raw.csv": "transcripts_raw"
        }
        
        # Try direct mapping first
        table_name = csv_to_table_map.get(filename)
        
        # If no mapping, try removing .csv extension and replacing _ with underscore
        if not table_name:
            table_name = filename.replace(".csv", "").lower()
            print(f"⚠️  No explicit mapping for {filename}, trying table name: {table_name}")
        
        return self.load_table_from_bigquery(table_name, use_cache=use_cache, cache_ttl_minutes=cache_ttl_minutes)
    
    def clear_cache(self, table_name: Optional[str] = None):
        """Clear cache for specific table or all tables"""
        if table_name:
            # Clear all cache entries for this table (including filtered versions)
            keys_to_remove = [k for k in self._memory_cache.keys() if table_name in str(k)]
            for key in keys_to_remove:
                self._memory_cache.pop(key, None)
                self._cache_metadata.pop(key, None)
            print(f"[CACHE] Cleared cache for {table_name}")
        else:
            self._memory_cache.clear()
            self._cache_metadata.clear()
            print(f"[CACHE] Cleared all cache")
    
    def get_table_schema(self, table_name: str) -> Dict[str, str]:
        """
        Get schema information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary mapping column names to types
        """
        try:
            table_ref = f"{self.project_id}.{self.dataset_id}.{table_name}"
            table = self.bq_client.get_table(table_ref)
            
            schema = {}
            for field in table.schema:
                schema[field.name] = field.field_type
            
            return schema
        except Exception as e:
            print(f"[ERROR] Error getting schema for {table_name}: {e}")
            return {}


# Initialize global loader singleton
_data_loader = BigQueryDataLoader()


def list_available_symbols() -> Dict[str, Any]:
    """
    List all available market indices, commodities, and instruments in the historical data
    
    Note: The data structure has instruments as columns, not rows
    
    Returns:
        Dictionary with list of available instruments, count, and metadata
    """
    try:
        print("[QUERY] Querying available instruments from BigQuery...")
        
        # Get table schema to list all available instruments (columns)
        schema = _data_loader.get_table_schema("30_yr_stock_market_data")
        
        # Exclude Date and id columns to get actual instruments
        instruments = [col for col in schema.keys() if col not in ['Date', 'id']]
        instruments_sorted = sorted(instruments)
        
        # Get date range for context
        date_query = f"""
        SELECT 
            MIN(Date) as min_date,
            MAX(Date) as max_date
        FROM `{config.BIGQUERY_PROJECT}.{config.BIGQUERY_DATASET}.30_yr_stock_market_data`
        """
        date_df = _data_loader.bq_client.query(date_query).to_dataframe()
        
        # Categorize instruments
        indices = [i for i in instruments if any(x in i for x in ['Dow', 'Nasdaq', 'S&P', 'NYSE', 'Russell', 'DAX', 'FTSE', 'Hang Seng'])]
        commodities = [i for i in instruments if any(x in i for x in ['Cocoa', 'Coffee', 'Corn', 'Cotton', 'Cattle', 'Orange', 'Soy', 'Sugar', 'Wheat'])]
        energy = [i for i in instruments if any(x in i for x in ['Ethanol', 'Oil', 'Gas', 'Heating'])]
        metals = [i for i in instruments if any(x in i for x in ['Copper', 'Gold', 'Palladium', 'Platinum', 'Silver'])]
        treasuries = [i for i in instruments if 'Treasury' in i]
        volatility = [i for i in instruments if 'Volatility' in i or 'VIX' in i]
        
        return {
            "status": "success",
            "symbols": instruments_sorted,
            "count": len(instruments),
            "date_range": {
                "start": str(date_df['min_date'].iloc[0]) if not date_df.empty else None,
                "end": str(date_df['max_date'].iloc[0]) if not date_df.empty else None
            },
            "categories": {
                "indices": indices,
                "commodities": commodities,
                "energy": energy,
                "metals": metals,
                "treasuries": treasuries,
                "volatility": volatility
            },
            "message": f"Found {len(instruments)} market instruments with {len(indices)} indices, {len(commodities)} commodities, {len(treasuries)} treasury yields"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error listing instruments: {str(e)}"
        }


def load_price_data(instrument: Optional[str] = None) -> Dict[str, Any]:
    """
    Load historical market data from BigQuery 30_yr_stock_market_data table
    
    Note: This table has instruments as columns (Dow Jones, Gold, Treasury yields, etc.)
    
    Args:
        instrument: Optional instrument name to focus on (e.g., "Dow Jones", "Gold", "Treasury Yield 10 Years")
        
    Returns:
        Dictionary with status, data preview, and metadata
    """
    try:
        # Load the full table (instruments are columns, not rows)
        df = _data_loader.load_table_from_bigquery("30_yr_stock_market_data")
        
        # Ensure Date column is datetime
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        
        if len(df) == 0:
            return {
                "status": "error",
                "message": "No data found in table"
            }
        
        # If specific instrument requested, focus on that column
        if instrument:
            # Find matching column (case-insensitive partial match)
            matching_cols = [col for col in df.columns if instrument.lower() in col.lower()]
            if matching_cols:
                selected_col = matching_cols[0]
                display_df = df[['Date', selected_col]].dropna()
                result = {
                    "status": "success",
                    "instrument": selected_col,
                    "rows": len(display_df),
                    "date_range": {
                        "start": str(display_df['Date'].min()),
                        "end": str(display_df['Date'].max())
                    },
                    "data_preview": sanitize_for_json(display_df.head(10).to_dict('records')),
                    "message": f"Showing data for {selected_col}"
                }
            else:
                result = {
                    "status": "error",
                    "message": f"Instrument '{instrument}' not found",
                    "suggestion": "Use list_available_symbols() to see available instruments",
                    "available_instruments": list(df.columns)
                }
        else:
            # Return summary of all instruments
            result = {
                "status": "success",
                "rows": len(df),
                "date_range": {
                    "start": str(df['Date'].min()),
                    "end": str(df['Date'].max())
                },
                "instruments": [col for col in df.columns if col not in ['Date', 'id']],
                "instruments_count": len([col for col in df.columns if col not in ['Date', 'id']]),
                "data_preview": sanitize_for_json(df.head(5).to_dict('records')),
                "message": "Showing overview of all market instruments. Use list_available_symbols() for categories."
            }
        
        return sanitize_for_json(result)
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def extract_event_dates(event_type: str, 
                        symbol: Optional[str] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Extract event dates from various event datasets
    
    Args:
        event_type: Type of event - "fed", "macro", "earnings", or "m&a"
        symbol: Optional stock symbol to filter by
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        Dictionary with event dates and metadata
    """
    
    # Map event types to datasets
    dataset_map = {
        "fed": "communications.csv",
        "macro": "US_Economic_Indicators.csv",
        "earnings": "stock_news.csv",
        "m&a": "acquisitions_update_2021.csv"
    }
    
    if event_type.lower() not in dataset_map:
        return {
            "status": "error",
            "message": f"Unknown event type: {event_type}. Valid types: {list(dataset_map.keys())}"
        }
    
    try:
        filename = dataset_map[event_type.lower()]
        df = _data_loader.load_csv_from_gcs(filename)
        
        # Identify date column (varies by dataset)
        date_col = None
        for col in ['Date', 'date', 'DATE', 'event_date', 'announcement_date', 'Announcement Date']:
            if col in df.columns:
                date_col = col
                break
        
        if not date_col:
            return {
                "status": "error",
                "message": f"No date column found in {filename}",
                "columns": list(df.columns)
            }
        
        # Parse dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        # Filter by symbol if applicable and provided
        if symbol and event_type.lower() in ["earnings", "m&a"]:
            symbol_cols = [col for col in df.columns if 'symbol' in col.lower() or 'ticker' in col.lower()]
            if symbol_cols:
                df = df[df[symbol_cols[0]].str.upper() == symbol.upper()]
        
        # Filter by date range
        if start_date:
            df = df[df[date_col] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df[date_col] <= pd.to_datetime(end_date)]
        
        # Extract unique dates
        event_dates = sorted(df[date_col].dt.strftime('%Y-%m-%d').unique().tolist())
        
        return {
            "status": "success",
            "event_type": event_type,
            "event_count": len(event_dates),
            "date_range": {
                "start": event_dates[0] if event_dates else None,
                "end": event_dates[-1] if event_dates else None
            },
            "event_dates": event_dates[:100],  # Limit to first 100 for display
            "total_dates": len(event_dates),
            "source_file": filename
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "event_type": event_type
        }


def compute_event_impact(symbol: str,
                        event_dates: List[str],
                        event_type: str,
                        window_days: int = 1,
                        baseline_volatility: Optional[float] = None) -> Dict[str, Any]:
    """
    Compute market reaction metrics for events
    
    Args:
        symbol: Stock symbol to analyze
        event_dates: List of event dates (YYYY-MM-DD format)
        event_type: Type of event (for context)
        window_days: Number of days before/after event to measure (default: 1)
        baseline_volatility: Optional baseline volatility for comparison
        
    Returns:
        Dictionary with impact metrics and statistics
    """
    
    try:
        # Load price data (cached)
        df = _data_loader.load_csv_from_gcs("30_yr_stock_market_data.csv")
        
        # Filter for symbol
        df = df[df['Symbol'].str.upper() == symbol.upper()].copy()
        
        if len(df) == 0:
            return {
                "status": "error",
                "message": f"No price data found for symbol {symbol}"
            }
        
        # Ensure Date is datetime and set as index
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        df.set_index('Date', inplace=True)
        
        # Convert event dates to datetime
        event_dates_dt = [pd.to_datetime(d) for d in event_dates]
        
        # Compute reactions
        impacts = []
        directions = []
        volatilities = []
        valid_events = []
        skipped_events = []
        
        for event_date in event_dates_dt:
            try:
                # Find closest trading days before and after
                before_date = event_date - pd.Timedelta(days=window_days)
                after_date = event_date + pd.Timedelta(days=window_days)
                
                # Get prices (use closest available dates)
                before_data = df[df.index <= event_date].iloc[-window_days-1:-1]
                after_data = df[df.index >= event_date].iloc[1:window_days+1]
                
                if len(before_data) == 0 or len(after_data) == 0:
                    skipped_events.append(str(event_date.date()))
                    continue
                
                price_before = before_data['Close'].iloc[-1]
                price_after = after_data['Close'].iloc[-1]
                
                # Calculate return
                move = (price_after - price_before) / price_before
                
                # Calculate volatility around event
                event_window = df[(df.index >= before_date) & (df.index <= after_date)]
                if len(event_window) > 1:
                    returns = event_window['Close'].pct_change().dropna()
                    vol = returns.std()
                else:
                    vol = 0
                
                impacts.append(abs(move))
                directions.append(move)
                volatilities.append(vol)
                valid_events.append(str(event_date.date()))
                
            except (KeyError, IndexError) as e:
                skipped_events.append(str(event_date.date()))
                continue
        
        if not impacts:
            return {
                "status": "error",
                "message": "No valid event impacts could be computed",
                "skipped_events": skipped_events
            }
        
        # Calculate statistics
        avg_impact = float(np.mean(impacts))
        median_impact = float(np.median(impacts))
        avg_direction = float(np.mean(directions))
        directional_bias = "Downside" if avg_direction < -0.001 else ("Upside" if avg_direction > 0.001 else "Neutral")
        
        # Calculate volatility multiplier
        avg_volatility = float(np.mean(volatilities)) if volatilities else 0
        if baseline_volatility and baseline_volatility > 0:
            volatility_multiplier = avg_volatility / baseline_volatility
        else:
            volatility_multiplier = avg_volatility
        
        # Calculate confidence based on sample size and consistency
        event_count = len(impacts)
        confidence = min(0.99, (event_count / 50) * 0.7 + 0.3)  # Scale 0.3-0.99 based on sample size
        
        # Add consistency penalty
        if len(impacts) > 1:
            consistency = 1 - (np.std(impacts) / (avg_impact + 1e-6))
            confidence *= max(0.5, consistency)
        
        result = {
            "status": "success",
            "Symbol": symbol.upper(),
            "EventType": event_type,
            "EventCount": event_count,
            "EventsProcessed": len(valid_events),
            "EventsSkipped": len(skipped_events),
            "EventImpactAvg": round(avg_impact, 4),
            "EventImpactAvgPercent": f"{round(avg_impact * 100, 2)}%",
            "MedianImpact": round(median_impact, 4),
            "MedianImpactPercent": f"{round(median_impact * 100, 2)}%",
            "DirectionalBias": directional_bias,
            "AverageDirection": round(avg_direction, 4),
            "VolatilityAvg": round(avg_volatility, 4),
            "VolatilityMultiplier": round(volatility_multiplier, 2),
            "Confidence": round(confidence, 2),
            "Rationale": f"{event_type.capitalize()} events historically produce {'elevated' if avg_impact > 0.02 else 'moderate'} "
                        f"post-event volatility with {directional_bias.lower()} bias. "
                        f"Based on {event_count} historical events.",
            "ValidEventDates": valid_events[:10],  # Show first 10
            "WindowDays": window_days
        }
        return sanitize_for_json(result)
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "symbol": symbol,
            "event_type": event_type
        }


def analyze_market_baseline(symbol: str, 
                            start_date: Optional[str] = None,
                            end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Calculate baseline market volatility and returns for comparison
    
    Args:
        symbol: Stock symbol to analyze
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        Dictionary with baseline statistics
    """
    
    try:
        # Load price data (cached)
        df = _data_loader.load_csv_from_gcs("30_yr_stock_market_data.csv")
        
        # Filter for symbol
        df = df[df['Symbol'].str.upper() == symbol.upper()].copy()
        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')
        
        # Filter by date range
        if start_date:
            df = df[df['Date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['Date'] <= pd.to_datetime(end_date)]
        
        if len(df) < 2:
            return {
                "status": "error",
                "message": f"Insufficient data for baseline analysis"
            }
        
        # Calculate daily returns
        df['Returns'] = df['Close'].pct_change()
        
        # Calculate baseline metrics
        baseline_volatility = df['Returns'].std()
        avg_daily_return = df['Returns'].mean()
        median_abs_return = df['Returns'].abs().median()
        
        # Calculate VaR (Value at Risk) at 95% confidence
        var_95 = df['Returns'].quantile(0.05)
        
        result = {
            "status": "success",
            "symbol": symbol.upper(),
            "data_points": len(df),
            "date_range": {
                "start": str(df['Date'].min().date()),
                "end": str(df['Date'].max().date())
            },
            "baseline_volatility": round(baseline_volatility, 4),
            "avg_daily_return": round(avg_daily_return, 4),
            "median_abs_return": round(median_abs_return, 4),
            "var_95": round(var_95, 4),
            "interpretation": f"On average, {symbol} moves {round(median_abs_return * 100, 2)}% per day "
                            f"with volatility of {round(baseline_volatility * 100, 2)}%"
        }
        return sanitize_for_json(result)
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


def get_comprehensive_event_impact(symbol: str,
                                   event_type: str,
                                   start_date: Optional[str] = None,
                                   end_date: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete end-to-end analysis: extract events, compute impacts, compare to baseline
    
    Args:
        symbol: Stock symbol to analyze
        event_type: Type of event - "fed", "macro", "earnings", or "m&a"
        start_date: Optional start date (YYYY-MM-DD)
        end_date: Optional end date (YYYY-MM-DD)
        
    Returns:
        Comprehensive impact analysis
    """
    
    print(f"\n{'='*70}")
    print(f"🎯 COMPREHENSIVE EVENT IMPACT ANALYSIS")
    print(f"{'='*70}")
    print(f"Symbol: {symbol.upper()}")
    print(f"Event Type: {event_type.upper()}")
    if start_date or end_date:
        print(f"Date Range: {start_date or 'earliest'} to {end_date or 'latest'}")
    print(f"{'='*70}\n")
    
    # Step 1: Extract event dates
    print("📅 Step 1: Extracting event dates...")
    events = extract_event_dates(event_type, symbol, start_date, end_date)
    
    if events['status'] != 'success' or events['event_count'] == 0:
        return {
            "status": "error",
            "message": "Failed to extract events or no events found",
            "details": events
        }
    
    print(f"✅ Found {events['event_count']} events\n")
    
    # Step 2: Calculate baseline
    print("📊 Step 2: Calculating market baseline...")
    baseline = analyze_market_baseline(symbol, start_date, end_date)
    
    if baseline['status'] != 'success':
        print("⚠️  Warning: Could not calculate baseline\n")
        baseline_vol = None
    else:
        baseline_vol = baseline.get('baseline_volatility')
        print(f"✅ Baseline volatility: {round(baseline_vol * 100, 2)}%\n")
    
    # Step 3: Compute event impacts
    print("🔬 Step 3: Computing event impacts...")
    impact = compute_event_impact(
        symbol=symbol,
        event_dates=events['event_dates'],
        event_type=event_type,
        window_days=1,
        baseline_volatility=baseline_vol
    )
    
    if impact['status'] != 'success':
        return {
            "status": "error",
            "message": "Failed to compute event impacts",
            "details": impact
        }
    
    print(f"✅ Analysis complete!\n")
    print(f"{'='*70}")
    print(f"📈 RESULTS SUMMARY")
    print(f"{'='*70}")
    print(f"Events Analyzed: {impact['EventCount']}")
    print(f"Average Impact: {impact['EventImpactAvgPercent']}")
    print(f"Directional Bias: {impact['DirectionalBias']}")
    print(f"Confidence: {impact['Confidence']}")
    print(f"{'='*70}\n")
    
    # Combine results
    result = {
        "status": "success",
        "analysis_type": "comprehensive_event_impact",
        "timestamp": datetime.now().isoformat(),
        "input_parameters": {
            "symbol": symbol.upper(),
            "event_type": event_type,
            "date_range": {
                "start": start_date,
                "end": end_date
            }
        },
        "event_data": events,
        "baseline_metrics": baseline,
        "impact_analysis": impact,
        "summary": {
            "symbol": symbol.upper(),
            "event_type": event_type,
            "events_analyzed": impact['EventCount'],
            "avg_impact": impact['EventImpactAvgPercent'],
            "directional_bias": impact['DirectionalBias'],
            "confidence": impact['Confidence'],
            "recommendation": _generate_recommendation(impact, baseline)
        }
    }
    return sanitize_for_json(result)


def _generate_recommendation(impact: Dict, baseline: Dict) -> str:
    """Generate actionable recommendation based on analysis"""
    
    avg_impact = impact.get('EventImpactAvg', 0)
    confidence = impact.get('Confidence', 0)
    bias = impact.get('DirectionalBias', 'Neutral')
    
    if confidence < 0.5:
        return "Low confidence - insufficient historical data. Consider wider date range or different event type."
    
    if avg_impact > 0.03:  # 3% average move
        severity = "significant"
    elif avg_impact > 0.015:  # 1.5% average move
        severity = "moderate"
    else:
        severity = "minor"
    
    return (f"Historical events show {severity} market impact ({round(avg_impact*100, 2)}%) "
            f"with {bias.lower()} bias. Confidence: {int(confidence*100)}%. "
            f"{'Consider hedging strategies.' if severity == 'significant' else 'Monitor for similar patterns.'}")


def analyze_bond_volatility(instrument: str = "10Y",
                            time_horizon_years: int = 5,
                            confidence_threshold: float = 0.7) -> Dict[str, Any]:
    """
    Analyze bond volatility patterns and generate trading signals
    
    Note: Works with BigQuery data where instruments are COLUMNS, not rows
    
    Args:
        instrument: Bond instrument (default: "10Y" for 10-year treasury)
                   Options: "5Y", "10Y", "30Y", "13W" (13-week bill)
        time_horizon_years: Analysis time horizon in years (default: 5)
        confidence_threshold: Minimum confidence for recommendations (default: 0.7)
        
    Returns:
        Comprehensive volatility analysis with trading signals
    """
    
    print(f"\n{'='*70}")
    print(f"[BOND ANALYSIS] BOND VOLATILITY ANALYSIS FOR TRADING")
    print(f"{'='*70}")
    print(f"Instrument: {instrument} Treasury Bond")
    print(f"Time Horizon: {time_horizon_years} years")
    print(f"Confidence Threshold: {confidence_threshold}")
    print(f"{'='*70}\n")
    
    try:
        # Map instrument parameter to actual BigQuery column names
        treasury_column_map = {
            "5Y": "Treasury Yield 5 Years __FVX_",
            "10Y": "Treasury Yield 10 Years __TNX_",
            "30Y": "Treasury Yield 30 Years __TYX_",
            "13W": "Treasury Bill 13 Week __IRX_"
        }
        
        treasury_column = treasury_column_map.get(instrument.upper())
        if not treasury_column:
            return {
                "status": "error",
                "message": f"Unknown instrument: {instrument}. Available: 5Y, 10Y, 30Y, 13W"
            }
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=time_horizon_years * 365)
        
        print(f"[DATE] Analysis Period: {start_date.date()} to {end_date.date()}")
        
        # Load Fed communications for monetary policy events (cached)
        df_fed = _data_loader.load_table_from_bigquery("communications")
        
        # Parse Fed announcement dates
        date_col_fed = None
        for col in ['Date', 'date', 'announcement_date']:
            if col in df_fed.columns:
                date_col_fed = col
                break
        
        if date_col_fed:
            df_fed[date_col_fed] = pd.to_datetime(df_fed[date_col_fed], errors='coerce')
            df_fed = df_fed.dropna(subset=[date_col_fed])
            fed_dates = df_fed[(df_fed[date_col_fed] >= start_date) & 
                              (df_fed[date_col_fed] <= end_date)][date_col_fed].tolist()
        else:
            fed_dates = []
        
        print(f"[FED] Found {len(fed_dates)} Fed announcements in period")
        
        # Load market data (instruments are COLUMNS in this table)
        df_market = _data_loader.load_table_from_bigquery("30_yr_stock_market_data")
        
        # Ensure Date column is datetime
        df_market['Date'] = pd.to_datetime(df_market['Date'])
        df_market = df_market.sort_values('Date')
        df_market = df_market[(df_market['Date'] >= start_date) & (df_market['Date'] <= end_date)]
        
        if len(df_market) < 30:
            return {
                "status": "error",
                "message": f"Insufficient data for {time_horizon_years}-year analysis (only {len(df_market)} days)"
            }
        
        # Check if treasury column exists
        if treasury_column not in df_market.columns:
            return {
                "status": "error",
                "message": f"Column '{treasury_column}' not found in data. Available columns: {list(df_market.columns)}"
            }
        
        # Use VIX for market volatility proxy (if available)
        vix_column = "CBOE Volitility __VIX_"  # Note: typo in actual column name
        if vix_column not in df_market.columns:
            vix_column = None
            print("[WARNING] VIX column not found, will use treasury yield volatility only")
        
        # Calculate treasury yield changes as volatility proxy
        df_market['Treasury_Change'] = df_market[treasury_column].diff()
        df_market['Treasury_Volatility'] = df_market['Treasury_Change'].rolling(window=30).std() * np.sqrt(252)  # Annualized
        
        # Drop NA values from volatility calculation
        df_market = df_market.dropna(subset=['Treasury_Volatility'])
        
        if len(df_market) < 30:
            return {
                "status": "error",
                "message": "Insufficient valid data points after cleaning"
            }
        
        # Identify high volatility periods
        volatility_mean = df_market['Treasury_Volatility'].mean()
        volatility_std = df_market['Treasury_Volatility'].std()
        high_vol_threshold = volatility_mean + volatility_std
        
        high_vol_periods = df_market[df_market['Treasury_Volatility'] > high_vol_threshold]
        
        print(f"[VOLATILITY] Volatility Analysis:")
        print(f"   Mean Volatility: {volatility_mean*100:.2f}%")
        print(f"   Std Dev: {volatility_std*100:.2f}%")
        print(f"   High Vol Threshold: {high_vol_threshold*100:.2f}%")
        print(f"   High Vol Days: {len(high_vol_periods)} ({len(high_vol_periods)/len(df_market)*100:.1f}%)")
        
        # Analyze event-driven volatility
        event_volatilities = []
        for fed_date in fed_dates:
            try:
                fed_date = pd.to_datetime(fed_date)
                # Get volatility in 5-day window around event
                window_data = df_market[(df_market['Date'] >= fed_date - pd.Timedelta(days=5)) & 
                                       (df_market['Date'] <= fed_date + pd.Timedelta(days=5))]
                if len(window_data) > 0:
                    avg_vol = window_data['Treasury_Volatility'].mean()
                    if not np.isnan(avg_vol):
                        event_volatilities.append(avg_vol)
            except:
                continue
        
        avg_event_volatility = np.mean(event_volatilities) if event_volatilities else volatility_mean
        
        # Calculate current volatility (last 30 days)
        current_volatility = df_market['Treasury_Volatility'].iloc[-1] if not np.isnan(df_market['Treasury_Volatility'].iloc[-1]) else volatility_mean
        
        # Get current treasury yield for context
        current_yield = df_market[treasury_column].iloc[-1]
        
        print(f"   Current {instrument} Yield: {current_yield:.3f}%")
        print(f"   Current Volatility: {current_volatility*100:.2f}%")
        print(f"   Average Event Volatility: {avg_event_volatility*100:.2f}%")
        
        # Generate trading signal
        vol_percentile = (df_market['Treasury_Volatility'].rank(pct=True).iloc[-1]) * 100
        
        # Trading logic for bonds: High volatility = opportunity for volatility trades
        if current_volatility > high_vol_threshold:
            signal = "SELL_VOLATILITY"
            signal_strength = "STRONG"
            rationale = f"Current volatility ({current_volatility*100:.2f}%) is elevated (>{high_vol_threshold*100:.2f}%). Consider volatility selling strategies (e.g., selling options, receiving in swaptions)."
        elif current_volatility < volatility_mean - 0.5 * volatility_std:
            signal = "BUY_VOLATILITY"
            signal_strength = "MODERATE"
            rationale = f"Current volatility ({current_volatility*100:.2f}%) is below average. Consider buying volatility protection ahead of potential events."
        else:
            signal = "HOLD"
            signal_strength = "NEUTRAL"
            rationale = f"Current volatility ({current_volatility*100:.2f}%) is within normal range. Monitor for event-driven opportunities."
        
        # Calculate confidence based on data quality and consistency
        data_completeness = len(df_market) / (time_horizon_years * 252)  # 252 trading days per year
        sample_confidence = min(1.0, data_completeness)
        
        event_coverage = min(1.0, len(fed_dates) / (time_horizon_years * 8))  # ~8 FOMC meetings per year
        
        volatility_consistency = 1 - (volatility_std / volatility_mean) if volatility_mean > 0 else 0.5
        
        overall_confidence = (sample_confidence * 0.4 + event_coverage * 0.3 + volatility_consistency * 0.3)
        
        print(f"\n[SIGNAL] TRADING SIGNAL: {signal} ({signal_strength})")
        print(f"[CONFIDENCE] Confidence: {overall_confidence*100:.1f}%")
        print(f"[PERCENTILE] Volatility Percentile: {vol_percentile:.1f}%")
        
        # Generate recommendation
        if overall_confidence >= confidence_threshold:
            recommendation_status = "ACTIONABLE"
            recommendation = f"{signal}: {rationale}"
        else:
            recommendation_status = "MONITOR_ONLY"
            recommendation = f"Confidence below threshold ({overall_confidence:.2%} < {confidence_threshold:.2%}). Monitor market but avoid trading until more data confirms signal."
        
        print(f"\n[COMPLETE] Analysis Complete!")
        print(f"{'='*70}\n")
        
        result = {
            "status": "success",
            "instrument": f"{instrument} Treasury Bond",
            "analysis_period": {
                "start": str(start_date.date()),
                "end": str(end_date.date()),
                "years": time_horizon_years
            },
            "volatility_metrics": {
                "current_volatility": round(current_volatility * 100, 2),
                "mean_volatility": round(volatility_mean * 100, 2),
                "volatility_std": round(volatility_std * 100, 2),
                "high_vol_threshold": round(high_vol_threshold * 100, 2),
                "volatility_percentile": round(vol_percentile, 1),
                "avg_event_volatility": round(avg_event_volatility * 100, 2)
            },
            "event_analysis": {
                "fed_announcements_analyzed": len(fed_dates),
                "event_driven_vol_observations": len(event_volatilities)
            },
            "trading_signal": {
                "signal": signal,
                "strength": signal_strength,
                "confidence": round(overall_confidence, 3),
                "confidence_percentage": f"{round(overall_confidence * 100, 1)}%",
                "recommendation_status": recommendation_status,
                "rationale": rationale
            },
            "confidence_breakdown": {
                "data_completeness": round(sample_confidence, 3),
                "event_coverage": round(event_coverage, 3),
                "volatility_consistency": round(volatility_consistency, 3),
                "overall_confidence": round(overall_confidence, 3)
            },
            "recommendation": recommendation,
            "current_yield": round(current_yield, 3),
            "market_context": {
                "data_source": "Treasury Yield Changes",
                "treasury_column": treasury_column,
                "data_points": len(df_market),
                "high_volatility_periods": len(high_vol_periods),
                "high_vol_percentage": f"{len(high_vol_periods)/len(df_market)*100:.1f}%"
            },
            "risk_disclaimer": "This analysis is based on historical data and statistical patterns. Past volatility does not guarantee future results. Always consider current market conditions, portfolio objectives, and risk tolerance before trading."
        }
        return sanitize_for_json(result)
        
    except Exception as e:
        import traceback
        return {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc(),
            "instrument": instrument,
            "time_horizon": time_horizon_years
        }


def get_bond_trading_strategy(instrument: str = "10Y",
                              time_horizon_years: int = 5,
                              risk_appetite: str = "moderate") -> Dict[str, Any]:
    """
    Generate comprehensive bond trading strategy with multiple scenarios
    
    Args:
        instrument: Bond instrument (default: "10Y")
        time_horizon_years: Analysis time horizon (default: 5 years)
        risk_appetite: Risk level - "conservative", "moderate", "aggressive"
        
    Returns:
        Detailed trading strategy with scenarios and risk management
    """
    
    # Get base volatility analysis
    vol_analysis = analyze_bond_volatility(instrument, time_horizon_years)
    
    if vol_analysis['status'] != 'success':
        return vol_analysis
    
    signal = vol_analysis['trading_signal']['signal']
    confidence = vol_analysis['trading_signal']['confidence']
    current_vol = vol_analysis['volatility_metrics']['current_volatility']
    mean_vol = vol_analysis['volatility_metrics']['mean_volatility']
    
    # Risk-adjusted position sizing
    risk_multipliers = {
        "conservative": 0.5,
        "moderate": 1.0,
        "aggressive": 1.5
    }
    
    position_size_multiplier = risk_multipliers.get(risk_appetite.lower(), 1.0)
    
    # Generate specific trade ideas
    strategies = []
    
    if signal == "SELL_VOLATILITY":
        strategies.append({
            "strategy": "Sell Treasury Options",
            "rationale": "Elevated volatility provides premium selling opportunities",
            "implementation": f"Sell out-of-the-money {instrument} options 1-3 months out",
            "target_premium": f"{current_vol * 0.3:.2f}% of notional",
            "risk": "Unlimited if rates move sharply",
            "position_size": f"{position_size_multiplier * 100:.0f}% of normal allocation"
        })
        
        strategies.append({
            "strategy": "Receive Fixed in Interest Rate Swaps",
            "rationale": "High volatility often precedes rate stabilization",
            "implementation": f"Enter receiver swaption on {instrument} point",
            "target_return": f"Capture {(current_vol - mean_vol):.1f}bps of elevated vol premium",
            "risk": "Rates rise faster than expected",
            "position_size": f"{position_size_multiplier * 75:.0f}% of normal allocation"
        })
        
    elif signal == "BUY_VOLATILITY":
        strategies.append({
            "strategy": "Buy Treasury Options",
            "rationale": "Low volatility environment, cheap protection",
            "implementation": f"Buy straddles or strangles on {instrument} futures",
            "target_entry": f"When implied vol < {mean_vol:.2f}%",
            "risk": "Time decay if volatility stays low",
            "position_size": f"{position_size_multiplier * 100:.0f}% of normal allocation"
        })
        
        strategies.append({
            "strategy": "Long Volatility ETF/Products",
            "rationale": "Position for volatility expansion",
            "implementation": "Buy volatility-linked products ahead of known events",
            "target_return": f"Capture {(mean_vol - current_vol):.1f}bps of vol expansion",
            "risk": "Volatility remains compressed",
            "position_size": f"{position_size_multiplier * 50:.0f}% of normal allocation"
        })
        
    else:  # HOLD
        strategies.append({
            "strategy": "Monitor and Wait",
            "rationale": "Volatility in normal range, no clear edge",
            "implementation": "Maintain current positions, watch for signals",
            "target_entry": f"Wait for vol to move outside {mean_vol-5:.1f}%-{mean_vol+5:.1f}% range",
            "risk": "Opportunity cost",
            "position_size": "Maintain existing allocations"
        })
    
    # Risk management rules
    risk_management = {
        "stop_loss": f"Exit if volatility moves {2 * vol_analysis['volatility_metrics']['volatility_std']:.1f}% against position",
        "profit_target": f"Take profits when volatility reverts to {mean_vol:.1f}% (mean)",
        "time_limit": f"Re-evaluate strategy every {max(30, time_horizon_years * 60)} days",
        "hedging": "Consider hedging with opposite maturity bonds (2Y or 30Y)"
    }
    
    # Market scenarios
    scenarios = [
        {
            "scenario": "Fed Hawkish Pivot",
            "probability": "25%",
            "expected_vol_impact": "+2-4%",
            "recommended_action": "Reduce duration, buy short-term vol protection"
        },
        {
            "scenario": "Fed Dovish Pivot",
            "probability": "20%",
            "expected_vol_impact": "+1-3%",
            "recommended_action": "Extend duration, consider selling near-term vol"
        },
        {
            "scenario": "Economic Recession",
            "probability": "15%",
            "expected_vol_impact": "+5-10%",
            "recommended_action": "Long bonds, long volatility products"
        },
        {
            "scenario": "Continued Stability",
            "probability": "40%",
            "expected_vol_impact": "-0.5 to +0.5%",
            "recommended_action": "Opportunistic volatility selling, theta capture"
        }
    ]
    
    result = {
        "status": "success",
        "strategy_overview": {
            "instrument": f"{instrument} Treasury Bond",
            "time_horizon": f"{time_horizon_years} years",
            "risk_appetite": risk_appetite,
            "primary_signal": signal,
            "confidence": confidence,
            "confidence_percentage": f"{confidence * 100:.1f}%"
        },
        "volatility_analysis": vol_analysis,
        "trading_strategies": strategies,
        "risk_management": risk_management,
        "market_scenarios": scenarios,
        "execution_notes": [
            "Start with smaller positions and scale up as confidence increases",
            "Monitor Fed communications calendar for event risk",
            "Review strategy weekly during high volatility periods",
            f"Confidence level is {vol_analysis['trading_signal']['recommendation_status']}"
        ],
        "generated_at": datetime.now().isoformat()
    }
    return sanitize_for_json(result)

