# tools.py
"""
Intelligent sentiment analysis tools with automatic file discovery.
Supports both GCS and local filesystem with persistent memory.
"""

import pandas as pd
import gcsfs
from typing import Optional, Dict, List, Any
import re
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

from app.config import config
# Data Orchestrator helper - canonical data for sentiment analysis
from app.sub_agents.data_orchestrator.tools import get_sentiment_sources


class PersistentMemoryStore:
    """
    Persistent memory store using GCS as backing storage.
    Survives across agent restarts and maintains session history.
    Optimized for low-latency access with in-memory caching.
    """
    
    def __init__(self):
        """Initialize persistent memory with GCS backing"""
        # Debug: Print bucket configuration
        print(f"🔧 Initializing PersistentMemoryStore...")
        print(f"   GCS_DATA_BUCKET: {config.GCS_DATA_BUCKET}")
        print(f"   GCS_MEMORY_PATH: {config.GCS_MEMORY_PATH}")
        
        self.fs = gcsfs.GCSFileSystem() if config.GCS_DATA_BUCKET else None
        self.memory_file = f"{config.GCS_DATA_BUCKET}/{config.GCS_MEMORY_PATH}/session_memory.json" if config.GCS_DATA_BUCKET else None
        
        if self.memory_file:
            print(f"   Memory file: {self.memory_file}")
        
        self.memory = self._load_memory()
        self._in_memory_cache = {}  # Fast access cache
        self._dirty = False  # Track if memory needs saving
        self._operations_since_save = 0  # Track operations for periodic saves
        
        # Note: atexit is unreliable with gcsfs due to thread pool shutdown
        # Instead, we save frequently (every 3 ops) during normal operation
    
    def _load_memory(self) -> dict:
        """Load memory from GCS with fallback"""
        if not self.fs or not self.memory_file:
            print("=" * 70)
            print("⚠️  WARNING: NO GCS PERSISTENCE CONFIGURED!")
            print("=" * 70)
            print("Memory will be lost when agent restarts.")
            print("To enable persistence, set in .env file:")
            print("  GCS_DATA_BUCKET=gs://your-bucket-name")
            print("=" * 70)
            return self._init_empty_memory()
        
        try:
            print(f"🔍 Checking for existing memory at: {self.memory_file}")
            if self.fs.exists(self.memory_file):
                with self.fs.open(self.memory_file, 'r') as f:
                    memory = json.load(f)
                    print(f"✅ Loaded persistent memory from GCS")
                    print(f"   Tickers analyzed: {len(memory.get('analyzed_tickers', {}))}")
                    print(f"   Total queries: {memory.get('statistics', {}).get('total_queries', 0)}")
                    return memory
            else:
                print("📝 No existing memory found - initializing new store")
                print(f"   Will create: {self.memory_file}")
                return self._init_empty_memory()
        except Exception as e:
            print(f"⚠️  Could not load memory from GCS: {e}")
            print(f"   This might be a permissions issue.")
            print(f"   Ensure service account has Storage Object Admin on bucket.")
            return self._init_empty_memory()
    
    def _init_empty_memory(self) -> dict:
        """Initialize empty memory structure"""
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "session_count": 0,
            "analyzed_tickers": {},
            "sentiment_history": [],
            "query_cache": {},
            "insights": [],
            "statistics": {
                "total_queries": 0,
                "unique_tickers_analyzed": 0,
                "cache_hits": 0
            }
        }
    
    def save_memory(self, force: bool = False):
        """
        Save memory to GCS with robust error handling.
        Designed to work during normal operation (not during Python shutdown).
        """
        if not self._dirty and not force:
            return
        
        if not self.fs or not self.memory_file:
            if self._operations_since_save > 0:
                print(f"⚠️  Cannot persist {self._operations_since_save} operations (no GCS configured)")
            return  # No persistence available
        
        try:
            self.memory["last_updated"] = datetime.now().isoformat()
            print(f"💾 Saving memory to GCS: {self.memory_file}")
            with self.fs.open(self.memory_file, 'w') as f:
                json.dump(self.memory, f, indent=2)
            self._dirty = False
            self._operations_since_save = 0  # Reset counter after successful save
            print(f"✅ Memory persisted successfully ({len(self.memory.get('analyzed_tickers', {}))} tickers)")
        except RuntimeError as e:
            # Handle shutdown-related errors gracefully
            if "shutdown" in str(e).lower() or "future" in str(e).lower():
                print(f"⚠️  Cannot save during shutdown (last {self._operations_since_save} ops may be lost)")
            else:
                print(f"⚠️  Failed to save memory: {e}")
        except PermissionError as e:
            print(f"⚠️  Permission denied saving to GCS: {e}")
            print(f"   Service account needs 'Storage Object Admin' on bucket")
        except Exception as e:
            print(f"⚠️  Failed to save memory: {e}")
            print(f"   Type: {type(e).__name__}")
    
    def add_analysis(self, ticker: str, analysis: dict):
        """Add ticker analysis to memory with source tracking"""
        if ticker not in self.memory["analyzed_tickers"]:
            self.memory["analyzed_tickers"][ticker] = []
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "analysis": analysis,
            "sources": analysis.get("data_sources", [])
        }
        
        self.memory["analyzed_tickers"][ticker].append(entry)
        self.memory["statistics"]["unique_tickers_analyzed"] = len(self.memory["analyzed_tickers"])
        self._dirty = True
        self._operations_since_save += 1
        
        # Save every 3 operations for more aggressive persistence
        # This reduces risk of data loss since atexit is unreliable with gcsfs
        if self._operations_since_save >= 3:
            self.save_memory()
    
    def get_cached_query(self, query_key: str) -> Optional[dict]:
        """Get cached query result for low latency"""
        # Check in-memory first (fastest)
        if query_key in self._in_memory_cache:
            self.memory["statistics"]["cache_hits"] += 1
            return self._in_memory_cache[query_key]
        
        # Check persistent cache
        if query_key in self.memory.get("query_cache", {}):
            result = self.memory["query_cache"][query_key]
            self._in_memory_cache[query_key] = result  # Promote to fast cache
            self.memory["statistics"]["cache_hits"] += 1
            return result
        
        return None
    
    def cache_query(self, query_key: str, result: dict, ttl_minutes: int = 60):
        """Cache query result with TTL"""
        cache_entry = {
            "result": result,
            "cached_at": datetime.now().isoformat(),
            "ttl_minutes": ttl_minutes
        }
        
        self.memory["query_cache"][query_key] = cache_entry
        self._in_memory_cache[query_key] = cache_entry
        self._dirty = True
        self._operations_since_save += 1
        
        # Save every 3 operations for more aggressive persistence
        if self._operations_since_save >= 3:
            self.save_memory()
    
    def add_insight(self, insight: str, category: str = "general", metadata: dict = None):
        """Store an insight with metadata"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "insight": insight,
            "metadata": metadata or {}
        }
        self.memory["insights"].append(entry)
        self._dirty = True
        self._operations_since_save += 1
        
        # Save every 3 operations for more aggressive persistence
        if self._operations_since_save >= 3:
            self.save_memory()
    
    def get_ticker_history(self, ticker: str) -> List[dict]:
        """Get all historical analyses for a ticker"""
        return self.memory["analyzed_tickers"].get(ticker, [])
    
    def search_memory(self, query: str) -> dict:
        """Search through memory with structured output"""
        query_lower = query.lower()
        results = {
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "tickers": [],
            "insights": [],
            "statistics": self.memory["statistics"]
        }
        
        # Search in ticker analyses
        for ticker, analyses in self.memory["analyzed_tickers"].items():
            if query_lower in ticker.lower():
                results["tickers"].append({
                    "ticker": ticker,
                    "analysis_count": len(analyses),
                    "last_analyzed": analyses[-1]["timestamp"] if analyses else None,
                    "sources": list(set([s for a in analyses for s in a.get("sources", [])]))
                })
        
        # Search in insights
        for insight in self.memory["insights"]:
            if query_lower in insight["insight"].lower():
                results["insights"].append(insight)
        
        return results


class SentimentDataStore:
    """
    Intelligent data store that automatically discovers and categorizes files.
    Works with both GCS and local filesystem with persistent memory integration.
    Optimized for low-latency access with multi-level caching.
    """
    
    def __init__(self, memory_store: Optional['PersistentMemoryStore'] = None):
        """Initialize data store with automatic file discovery and memory"""
        # Determine storage backend
        if config.GCS_DATA_BUCKET:
            self.fs = gcsfs.GCSFileSystem()
            self.base_path = f"{config.GCS_DATA_BUCKET}/{config.GCS_DATASET_PREFIX}"
            self.use_gcs = True
            print(f"☁️  Using GCS: {self.base_path}")
        else:
            self.base_path = Path(__file__).parent.parent.parent / "dataset"
            self.use_gcs = False
            print(f"💾 Using local filesystem: {self.base_path}")
        
        # Persistent memory integration
        self.memory = memory_store or PersistentMemoryStore()
        
        # Discover and categorize all available files
        self.file_catalog = self._discover_and_categorize_files()
        self._data_cache = {}  # Fast in-memory cache for loaded data
        self._query_count = 0
    
    def _discover_and_categorize_files(self) -> Dict[str, Any]:
        """
        Automatically discover and intelligently categorize all data files.
        Returns a structured catalog of files by type and purpose.
        """
        catalog = {
            'sentiment_sources': {
                'news': [],           # News headlines for sentiment
                'analyst': [],        # Analyst ratings/recommendations
                'transcripts': []     # Earnings call transcripts
            },
            'market_data': {
                'prices': [],         # Stock price history
                'indices': [],        # Market indices data
                'economic': []        # Economic indicators
            },
            'company_info': {
                'companies': [],      # Company metadata
                'symbols': [],        # Symbol/ticker mappings
                'sp500': []          # S&P 500 constituents
            },
            'corporate_actions': {
                'acquisitions': [],   # M&A activity
                'communications': []  # Corporate filings/communications
            },
            'metadata': [],           # Dataset metadata
            'unknown': []             # Uncategorized files
        }
        
        try:
            # Get all files
            if self.use_gcs:
                all_files = self.fs.ls(self.base_path)
            else:
                all_files = [str(f) for f in self.base_path.glob("*.csv")]
                # Also check for transcript folders
                transcript_folders = list(self.base_path.glob("*earnings*"))
                for folder in transcript_folders:
                    if folder.is_dir():
                        catalog['sentiment_sources']['transcripts'].append(str(folder))
            
            print(f"\n📂 Discovered {len(all_files)} files")
            print("📋 Categorizing files...\n")
            
            # Intelligent categorization by filename patterns
            for file_path in all_files:
                filename = str(file_path).split('/')[-1].lower()
                
                # Skip non-data files
                if filename.startswith('.') or filename.endswith(('.zip', '.md', '.txt')):
                    continue
                
                # Sentiment sources
                if 'news' in filename or 'headline' in filename:
                    catalog['sentiment_sources']['news'].append(file_path)
                    print(f"  📰 News: {filename}")
                
                elif 'analyst' in filename or 'rating' in filename:
                    catalog['sentiment_sources']['analyst'].append(file_path)
                    print(f"  📊 Analyst: {filename}")
                
                elif 'transcript' in filename or 'earnings' in filename:
                    catalog['sentiment_sources']['transcripts'].append(file_path)
                    print(f"  🎤 Transcripts: {filename}")
                
                # Market data
                elif ('stock_market' in filename or 'market_data' in filename or 
                      '30_yr' in filename or '_yr_' in filename):
                    catalog['market_data']['prices'].append(file_path)
                    print(f"  📈 Market: {filename}")
                
                elif 'index' in filename and 'data' in filename:
                    catalog['market_data']['indices'].append(file_path)
                    print(f"  📉 Index: {filename}")
                
                elif 'economic' in filename or 'indicator' in filename:
                    catalog['market_data']['economic'].append(file_path)
                    print(f"  💹 Economic: {filename}")
                
                # Company info
                elif 'sp500' in filename or 's&p' in filename or 's_p_500' in filename:
                    catalog['company_info']['sp500'].append(file_path)
                    print(f"  🏢 S&P 500: {filename}")
                
                elif 'companies' in filename or 'company' in filename:
                    catalog['company_info']['companies'].append(file_path)
                    print(f"  🏢 Companies: {filename}")
                
                elif 'symbol' in filename or 'ticker' in filename or 'meta' in filename:
                    catalog['company_info']['symbols'].append(file_path)
                    print(f"  🔤 Symbols: {filename}")
                
                # Corporate actions
                elif 'acquisition' in filename or 'merger' in filename or 'm&a' in filename:
                    catalog['corporate_actions']['acquisitions'].append(file_path)
                    print(f"  🤝 M&A: {filename}")
                
                elif 'communication' in filename or 'filing' in filename:
                    catalog['corporate_actions']['communications'].append(file_path)
                    print(f"  📢 Comms: {filename}")
                
                # Metadata
                elif 'summary' in filename or 'metadata' in filename or 'ds_store' in filename:
                    catalog['metadata'].append(file_path)
                    print(f"  ℹ️  Meta: {filename}")
                
                else:
                    catalog['unknown'].append(file_path)
                    print(f"  ❓ Other: {filename}")
            
            print(f"\n✅ File discovery complete!")
            return catalog
            
        except Exception as e:
            print(f"❌ Error discovering files: {e}")
            import traceback
            traceback.print_exc()
            return catalog
    
    def get_files_for_intent(self, intent: str) -> List[str]:
        """
        Get relevant file paths based on user intent.
        
        Args:
            intent: One of 'sentiment', 'news', 'analyst', 'transcripts', 
                    'market', 'economic', 'company', 'comprehensive', 'all'
        
        Returns:
            List of file paths relevant to the intent
        """
        files = []
        
        intent = intent.lower()
        
        if intent in ['sentiment', 'news']:
            files.extend(self.file_catalog['sentiment_sources']['news'])
        
        elif intent == 'analyst':
            files.extend(self.file_catalog['sentiment_sources']['analyst'])
        
        elif intent in ['transcripts', 'earnings']:
            files.extend(self.file_catalog['sentiment_sources']['transcripts'])
        
        elif intent == 'market':
            files.extend(self.file_catalog['market_data']['prices'])
            files.extend(self.file_catalog['market_data']['indices'])
        
        elif intent == 'economic':
            files.extend(self.file_catalog['market_data']['economic'])
        
        elif intent == 'company':
            files.extend(self.file_catalog['company_info']['companies'])
            files.extend(self.file_catalog['company_info']['sp500'])
            files.extend(self.file_catalog['company_info']['symbols'])
        
        elif intent in ['comprehensive', 'all']:
            # Return all sentiment-related sources
            files.extend(self.file_catalog['sentiment_sources']['news'])
            files.extend(self.file_catalog['sentiment_sources']['analyst'])
        
        return files
    
    def smart_query(self, intent: str, filters: Optional[Dict] = None, max_rows: Optional[int] = None) -> pd.DataFrame:
        """
        Intelligently query data based on intent with caching for low latency.
        Automatically selects and reads the right files.
        
        Args:
            intent: What type of data to retrieve
            filters: Optional filters (ticker, date_range, sentiment, etc.)
            max_rows: Optional limit on rows per file
        
        Returns:
            Combined DataFrame with data from relevant files
        """
        self._query_count += 1
        filters = filters or {}
        
        # Generate cache key for this query
        cache_key = f"{intent}_{json.dumps(filters, sort_keys=True)}_{max_rows}"
        
        # Check cache for low-latency access
        cached_result = self.memory.get_cached_query(cache_key)
        if cached_result and cached_result.get("result"):
            print(f"⚡ Cache hit! Returning cached data (query #{self._query_count})")
            # Return cached DataFrame
            return pd.DataFrame(cached_result["result"].get("data", []))
        
        relevant_files = self.get_files_for_intent(intent)
        
        if not relevant_files:
            print(f"⚠️  No files found for intent: {intent}")
            return pd.DataFrame()
        
        print(f"🔍 Querying {len(relevant_files)} file(s) for intent: {intent} (query #{self._query_count})")
        
        all_data = []
        sources_used = []
        
        for file_path in relevant_files:
            try:
                # Read file
                if self.use_gcs:
                    with self.fs.open(file_path, 'r') as f:
                        if max_rows:
                            df = pd.read_csv(f, nrows=max_rows)
                        else:
                            df = pd.read_csv(f)
                else:
                    if max_rows:
                        df = pd.read_csv(file_path, nrows=max_rows)
                    else:
                        df = pd.read_csv(file_path)
                
                if df.empty:
                    continue
                
                # Apply filters if provided
                if filters:
                    # Filter by ticker/stock
                    if 'ticker' in filters:
                        ticker = filters['ticker'].upper()
                        if 'stock' in df.columns:
                            df = df[df['stock'].str.upper() == ticker]
                        elif 'Stock' in df.columns:
                            df = df[df['Stock'].str.upper() == ticker]
                        elif 'ticker' in df.columns:
                            df = df[df['ticker'].str.upper() == ticker]
                    
                    # Filter by date range
                    if 'start_date' in filters:
                        if 'date' in df.columns:
                            df['date'] = pd.to_datetime(df['date'], errors='coerce')
                            df = df[df['date'] >= filters['start_date']]
                        elif 'Date' in df.columns:
                            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                            df = df[df['Date'] >= filters['start_date']]
                    
                    # Filter by sentiment
                    if 'sentiment' in filters:
                        sentiment_val = filters['sentiment'].lower()
                        if 'label' in df.columns:
                            df = df[df['label'].str.lower() == sentiment_val]
                        elif 'sentiment' in df.columns:
                            df = df[df['sentiment'].str.lower() == sentiment_val]
                
                if not df.empty:
                    # Add source file tracking
                    filename = str(file_path).split('/')[-1]
                    df['_source_file'] = filename
                    df['_source_path'] = str(file_path)
                    all_data.append(df)
                    sources_used.append(filename)
                    print(f"  ✓ Loaded {len(df)} rows from {filename}")
                    
            except Exception as e:
                filename = str(file_path).split('/')[-1]
                print(f"  ✗ Error reading {filename}: {e}")
        
        if all_data:
            result = pd.concat(all_data, ignore_index=True)
            print(f"📊 Total: {len(result)} rows from {result['_source_file'].nunique()} file(s)")
            
            # Cache result for future low-latency access
            # Store limited data to keep cache size manageable
            cache_data = {
                "data": result.head(1000).to_dict(orient='records'),  # Cache first 1000 rows
                "total_rows": len(result),
                "sources": sources_used,
                "intent": intent
            }
            self.memory.cache_query(cache_key, cache_data, ttl_minutes=30)
            
            return result
        
        print(f"⚠️  No data retrieved")
        return pd.DataFrame()


# Initialize global memory and data store
print("\n🚀 Initializing Persistent Memory & Data Store...")
persistent_memory = PersistentMemoryStore()
data_store = SentimentDataStore(memory_store=persistent_memory)
print("✅ Data store with persistent memory ready!\n")


# ============================================================================
# TOOL FUNCTIONS
# ============================================================================

def analyze_news_headline(headline: str) -> dict:
    """
    Analyzes sentiment of a news headline with structured JSON output.
    Automatically discovers and searches all available news data files.
    Returns low-latency results with full datasource attribution.
    
    Args:
        headline: The news headline to analyze
        
    Returns:
        Structured JSON dictionary with sentiment analysis and datasources
    """
    try:
        print(f"\n🔍 Analyzing headline: '{headline[:50]}...'")
        
        # Check memory for similar queries (low latency)
        cache_key = f"headline_{headline[:100]}"
        cached = persistent_memory.get_cached_query(cache_key)
        if cached:
            print("⚡ Returning cached headline analysis")
            return cached.get("result", {})
        
        # Automatically query all news data
        df = data_store.smart_query('news')
        
        if df.empty:
            result = {
                "status": "no_data",
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "type": "headline_analysis",
                    "headline": headline
                },
                "result": {
                    "sentiment": "unknown",
                    "confidence": "none",
                    "message": "No news data files available"
                },
                "datasources": {
                    "files_searched": [],
                    "total_records": 0,
                    "storage_backend": "gcs" if data_store.use_gcs else "local"
                },
                "performance": {
                    "cache_hit": False,
                    "query_count": data_store._query_count
                },
                "recommendation": "Check GCS bucket configuration"
            }
            return result
        
        print(f"📰 Searching across {len(df)} news articles")
        
        # Extract unique source files
        source_files = df['_source_file'].unique().tolist() if '_source_file' in df.columns else []
        
        # Search for exact or similar matches
        if 'headline' in df.columns:
            matches = df[df['headline'].str.contains(
                re.escape(headline[:50]), case=False, na=False
            )]
            
            if not matches.empty:
                sentiment = matches.iloc[0].get('label', 'unknown')
                matched_sources = matches['_source_file'].unique().tolist() if '_source_file' in matches.columns else []
                
                result = {
                    "status": "success",
                    "timestamp": datetime.now().isoformat(),
                    "query": {
                        "type": "headline_analysis",
                        "headline": headline
                    },
                    "result": {
                        "sentiment": str(sentiment).lower(),
                        "confidence": "high",
                        "match_type": "exact_match",
                        "matches_found": len(matches)
                    },
                    "datasources": {
                        "files_matched": matched_sources,
                        "files_searched": source_files,
                        "total_records_searched": len(df),
                        "matching_records": len(matches),
                        "storage_backend": "gcs" if data_store.use_gcs else "local",
                        "base_path": str(data_store.base_path)
                    },
                    "performance": {
                        "cache_hit": False,
                        "query_count": data_store._query_count,
                        "latency": "low"
                    }
                }
                
                # Cache for future queries
                persistent_memory.cache_query(cache_key, result, ttl_minutes=60)
                
                # Store in memory
                persistent_memory.add_insight(
                    f"Headline '{headline[:50]}' analyzed with sentiment: {sentiment}",
                    category="headline_analysis",
                    metadata={"sentiment": str(sentiment), "sources": matched_sources}
                )
                
                return result
            
            # Try keyword-based similarity
            keywords = headline.lower().split()[:5]
            for keyword in keywords:
                if len(keyword) > 4:
                    matches = df[df['headline'].str.contains(keyword, case=False, na=False)]
                    if not matches.empty:
                        if 'label' in matches.columns:
                            sentiment_counts = matches['label'].value_counts()
                            most_common = sentiment_counts.idxmax()
                            matched_sources = matches['_source_file'].unique().tolist() if '_source_file' in matches.columns else []
                            
                            result = {
                                "status": "success",
                                "timestamp": datetime.now().isoformat(),
                                "query": {
                                    "type": "headline_analysis",
                                    "headline": headline
                                },
                                "result": {
                                    "sentiment": str(most_common).lower(),
                                    "confidence": "medium",
                                    "match_type": "keyword_match",
                                    "keyword": keyword,
                                    "related_headlines": len(matches),
                                    "sentiment_distribution": sentiment_counts.to_dict()
                                },
                                "datasources": {
                                    "files_matched": matched_sources,
                                    "files_searched": source_files,
                                    "total_records_searched": len(df),
                                    "matching_records": len(matches),
                                    "storage_backend": "gcs" if data_store.use_gcs else "local",
                                    "base_path": str(data_store.base_path)
                                },
                                "performance": {
                                    "cache_hit": False,
                                    "query_count": data_store._query_count
                                }
                            }
                            
                            persistent_memory.cache_query(cache_key, result, ttl_minutes=30)
                            return result
        
        result = {
            "status": "no_match",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "headline_analysis",
                "headline": headline
            },
            "result": {
                "sentiment": "unknown",
                "confidence": "none",
                "message": "No matching headlines found in historical data"
            },
            "datasources": {
                "files_searched": source_files,
                "total_records_searched": len(df),
                "storage_backend": "gcs" if data_store.use_gcs else "local"
            },
            "performance": {
                "cache_hit": False,
                "query_count": data_store._query_count
            },
            "recommendation": "Consider using LLM inference for unseen headlines"
        }
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "headline_analysis",
                "headline": headline
            },
            "result": {
                "sentiment": "error",
                "message": str(e)
            },
            "datasources": {
                "files_searched": [],
                "error": str(e)
            }
        }


def analyze_analyst_sentiment(company_ticker: str, days_lookback: int = 5000) -> dict:
    """
    Analyzes analyst sentiment for a company with structured JSON output.
    Automatically discovers and reads analyst rating files.
    Returns low-latency results with full datasource attribution.
    
    Args:
        company_ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        days_lookback: Number of days to look back (default 5000)
        
    Returns:
        Structured JSON dictionary with analyst sentiment and datasources
    """
    try:
        ticker_upper = company_ticker.upper()
        print(f"\n📊 Analyzing analyst sentiment for {ticker_upper}")
        
        # Check memory cache for low latency
        cache_key = f"analyst_{ticker_upper}_{days_lookback}"
        cached = persistent_memory.get_cached_query(cache_key)
        if cached:
            print("⚡ Returning cached analyst analysis")
            return cached.get("result", {})
        
        # Automatically query analyst data filtered by ticker
        df = data_store.smart_query('analyst', filters={'ticker': ticker_upper})
        
        if df.empty:
            result = {
                "status": "no_data",
                "timestamp": datetime.now().isoformat(),
                "query": {
                    "type": "analyst_sentiment",
                    "ticker": ticker_upper,
                    "days_lookback": days_lookback
                },
                "result": {
                    "sentiment": "unknown",
                    "confidence": "none",
                    "message": f"No analyst ratings found for {ticker_upper}"
                },
                "datasources": {
                    "files_searched": list(data_store.file_catalog['sentiment_sources']['analyst']),
                    "files_matched": [],
                    "total_records": 0,
                    "storage_backend": "gcs" if data_store.use_gcs else "local"
                },
                "performance": {
                    "cache_hit": False,
                    "query_count": data_store._query_count
                },
                "recommendation": f"Check if {ticker_upper} exists in analyst data or try different ticker"
            }
            return result
        
        print(f"✓ Found {len(df)} analyst ratings for {ticker_upper}")
        
        # Extract source files
        source_files = df['_source_file'].unique().tolist() if '_source_file' in df.columns else []
        
        # Analyze sentiment from titles
        recent = df.head(50)  # Most recent ratings
        
        upgrade_keywords = ['upgrade', 'raise', 'outperform', 'buy', 'beat', 'higher', 'positive']
        downgrade_keywords = ['downgrade', 'lower', 'cut', 'sell', 'miss', 'underperform', 'negative']
        
        upgrades = 0
        downgrades = 0
        neutral = 0
        sample_titles = []
        
        for _, row in recent.iterrows():
            title = str(row.get('title', '')).lower()
            if any(word in title for word in upgrade_keywords):
                upgrades += 1
            elif any(word in title for word in downgrade_keywords):
                downgrades += 1
            else:
                neutral += 1
            
            # Collect sample titles
            if len(sample_titles) < 5:
                sample_titles.append(row.get('title', 'N/A'))
        
        total = upgrades + downgrades + neutral
        
        if upgrades > downgrades:
            sentiment = "positive"
        elif downgrades > upgrades:
            sentiment = "negative"
        else:
            sentiment = "neutral"
        
        # Determine confidence
        confidence = "high" if total > 10 else "medium" if total > 5 else "low"
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "analyst_sentiment",
                "ticker": ticker_upper,
                "days_lookback": days_lookback
            },
            "result": {
                "sentiment": sentiment,
                "confidence": confidence,
                "analysis": {
                    "upgrades": upgrades,
                    "downgrades": downgrades,
                    "neutral": neutral,
                    "total_ratings_analyzed": total,
                    "upgrade_ratio": round(upgrades / total, 3) if total > 0 else 0,
                    "downgrade_ratio": round(downgrades / total, 3) if total > 0 else 0,
                    "sentiment_score": round((upgrades - downgrades) / total, 3) if total > 0 else 0
                },
                "sample_ratings": sample_titles,
                "interpretation": f"Analysts are {sentiment} on {ticker_upper} with {upgrades} upgrades vs {downgrades} downgrades"
            },
            "datasources": {
                "files_matched": source_files,
                "total_records_found": len(df),
                "records_analyzed": len(recent),
                "storage_backend": "gcs" if data_store.use_gcs else "local",
                "base_path": str(data_store.base_path),
                "file_paths": df['_source_path'].unique().tolist() if '_source_path' in df.columns else []
            },
            "performance": {
                "cache_hit": False,
                "query_count": data_store._query_count,
                "latency": "low"
            }
        }
        
        # Cache for future queries
        persistent_memory.cache_query(cache_key, result, ttl_minutes=60)
        
        # Store in persistent memory
        persistent_memory.add_analysis(ticker_upper, result)
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "analyst_sentiment",
                "ticker": company_ticker,
                "days_lookback": days_lookback
            },
            "result": {
                "sentiment": "error",
                "message": str(e)
            },
            "datasources": {
                "files_searched": [],
                "error": str(e)
            }
        }


def get_comprehensive_sentiment(company_ticker: str, include_transcripts: bool = True) -> dict:
    """
    Gets comprehensive sentiment analysis from all available sources.
    Automatically discovers and combines news, analyst, and transcript data.
    Returns structured JSON with complete datasource attribution.
    Optimized for low-latency with intelligent caching.
    
    Args:
        company_ticker: Stock ticker symbol
        include_transcripts: Whether to include transcript analysis (default True)
        
    Returns:
        Structured JSON dictionary with multi-source sentiment analysis
    """
    try:
        ticker_upper = company_ticker.upper()
        print(f"\n🔎 Comprehensive sentiment analysis for {ticker_upper}")
        
        # Check memory cache
        cache_key = f"comprehensive_{ticker_upper}_{include_transcripts}"
        cached = persistent_memory.get_cached_query(cache_key)
        if cached:
            print("⚡ Returning cached comprehensive analysis")
            return cached.get("result", {})
        
        result = {
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "comprehensive_sentiment",
                "ticker": ticker_upper,
                "include_transcripts": include_transcripts
            },
            "result": {
                "overall_sentiment": "unknown",
                "confidence": "none",
                "sentiment_by_source": {},
                "aggregated_metrics": {}
            },
            "datasources": {
                "sources_queried": [],
                "sources_with_data": [],
                "files_by_source": {},
                "total_records_by_source": {},
                "storage_backend": "gcs" if data_store.use_gcs else "local",
                "base_path": str(data_store.base_path)
            },
            "performance": {
                "cache_hit": False,
                "query_count": data_store._query_count
            }
        }
        
        sources_with_data = []
        total_records = 0
        
        # 1. Get news sentiment (via Data Orchestrator)
        print("  📰 Querying news data via Data Orchestrator...")
        result["datasources"]["sources_queried"].append("news")
        # Use canonical tables: stock_news, 30_yr_stock_market_data, US_Economic_Indicators, combined_transcripts
        ds = get_sentiment_sources(ticker_upper, limit=1000)
        news_rows = ds.get('tables', {}).get('stock_news', {}).get('rows', [])
        news_df = pd.DataFrame(news_rows)

        if not news_df.empty:
            sources_with_data.append("news")
            # No reliable _source_file in BQ rows; report source table instead
            news_files = ["bq:stock_news"] if news_rows else []

            if 'label' in news_df.columns:
                news_sentiment = news_df['label'].value_counts().to_dict()
                total_positive = news_sentiment.get('positive', 0)
                total_negative = news_sentiment.get('negative', 0)
                total_neutral = news_sentiment.get('neutral', 0)
                total_news = len(news_df)

                result["result"]["sentiment_by_source"]["news"] = {
                    "sentiment_distribution": news_sentiment,
                    "total_articles": total_news,
                    "positive_ratio": round(total_positive / total_news, 3) if total_news > 0 else 0,
                    "negative_ratio": round(total_negative / total_news, 3) if total_news > 0 else 0,
                    "sentiment_score": round((total_positive - total_negative) / total_news, 3) if total_news > 0 else 0,
                    "sample_headlines": news_df.head(3)['headline'].tolist() if 'headline' in news_df.columns else []
                }

                result["datasources"]["files_by_source"]["news"] = news_files
                result["datasources"]["total_records_by_source"]["news"] = total_news
                total_records += total_news

                print(f"    ✓ Found {total_news} news articles from BigQuery")
        
        # 2. Get analyst sentiment
        print("  📊 Querying analyst data...")
        result["datasources"]["sources_queried"].append("analyst")
        analyst_df = data_store.smart_query('analyst', filters={'ticker': ticker_upper})
        
        if not analyst_df.empty:
            sources_with_data.append("analyst")
            analyst_files = analyst_df['_source_file'].unique().tolist() if '_source_file' in analyst_df.columns else []
            
            # Analyze analyst sentiment
            upgrade_keywords = ['upgrade', 'raise', 'outperform', 'buy', 'beat', 'higher', 'positive']
            downgrade_keywords = ['downgrade', 'lower', 'cut', 'sell', 'miss', 'underperform', 'negative']
            
            upgrades = 0
            downgrades = 0
            neutral = 0
            
            for _, row in analyst_df.iterrows():
                title = str(row.get('title', '')).lower()
                if any(word in title for word in upgrade_keywords):
                    upgrades += 1
                elif any(word in title for word in downgrade_keywords):
                    downgrades += 1
                else:
                    neutral += 1
            
            total_analyst = len(analyst_df)
            
            result["result"]["sentiment_by_source"]["analyst"] = {
                "upgrades": upgrades,
                "downgrades": downgrades,
                "neutral": neutral,
                "total_ratings": total_analyst,
                "upgrade_ratio": round(upgrades / total_analyst, 3) if total_analyst > 0 else 0,
                "sentiment_score": round((upgrades - downgrades) / total_analyst, 3) if total_analyst > 0 else 0,
                "sample_titles": analyst_df.head(3)['title'].tolist() if 'title' in analyst_df.columns else []
            }
            
            result["datasources"]["files_by_source"]["analyst"] = analyst_files
            result["datasources"]["total_records_by_source"]["analyst"] = total_analyst
            total_records += total_analyst
            
            print(f"    ✓ Found {total_analyst} analyst ratings from {len(analyst_files)} file(s)")
        
        # 3. Check for transcripts (via Data Orchestrator)
        if include_transcripts:
            print("  🎤 Checking for earnings transcripts via Data Orchestrator...")
            result["datasources"]["sources_queried"].append("transcripts")
            transcript_rows = ds.get('tables', {}).get('transcripts', {}).get('rows', [])
            transcript_df = pd.DataFrame(transcript_rows)

            if not transcript_df.empty:
                sources_with_data.append("transcripts")
                transcript_names = transcript_df.head(5).to_dict(orient='records')

                result["result"]["sentiment_by_source"]["transcripts"] = {
                    "count": len(transcript_df),
                    "available": True,
                    "files": transcript_names
                }

                result["datasources"]["files_by_source"]["transcripts"] = ["bq:combined_transcripts"]
                result["datasources"]["total_records_by_source"]["transcripts"] = len(transcript_df)

                print(f"    ✓ Found {len(transcript_df)} transcript(s) from BigQuery")
        # 4. Add market & economic context from Data Orchestrator
        market_rows = ds.get('tables', {}).get('market_data', {}).get('rows', [])
        econ_rows = ds.get('tables', {}).get('economic', {}).get('rows', [])

        if market_rows:
            result["datasources"]["sources_queried"].append("market")
            result["datasources"]["files_by_source"]["market"] = ["bq:30_yr_stock_market_data"]
            result["datasources"]["total_records_by_source"]["market"] = len(market_rows)
            total_records += len(market_rows)

        if econ_rows:
            result["datasources"]["sources_queried"].append("economic")
            result["datasources"]["files_by_source"]["economic"] = ["bq:US_Economic_Indicators"]
            result["datasources"]["total_records_by_source"]["economic"] = len(econ_rows)
            total_records += len(econ_rows)
        
        # Aggregate overall sentiment
        result["datasources"]["sources_with_data"] = sources_with_data
        
        if sources_with_data:
            result["status"] = "success"
            
            # Calculate overall sentiment from all sources
            sentiment_scores = []
            
            if "news" in result["result"]["sentiment_by_source"]:
                news_score = result["result"]["sentiment_by_source"]["news"]["sentiment_score"]
                sentiment_scores.append(("news", news_score))
            
            if "analyst" in result["result"]["sentiment_by_source"]:
                analyst_score = result["result"]["sentiment_by_source"]["analyst"]["sentiment_score"]
                sentiment_scores.append(("analyst", analyst_score))
            
            if sentiment_scores:
                avg_score = sum(score for _, score in sentiment_scores) / len(sentiment_scores)
                
                if avg_score > 0.15:
                    overall = "positive"
                elif avg_score < -0.15:
                    overall = "negative"
                else:
                    overall = "neutral"
                
                result["result"]["overall_sentiment"] = overall
                result["result"]["confidence"] = "high" if len(sentiment_scores) >= 2 else "medium"
                result["result"]["aggregated_metrics"] = {
                    "overall_score": round(avg_score, 3),
                    "sources_analyzed": len(sentiment_scores),
                    "total_records": total_records,
                    "interpretation": f"Composite sentiment for {ticker_upper} is {overall} based on {len(sentiment_scores)} source(s)"
                }
            
            print(f"\n✅ Comprehensive analysis complete: {result['result']['overall_sentiment'].upper()}")
            print(f"   📊 {len(sources_with_data)} source(s), {total_records} records analyzed")
            
        else:
            result["status"] = "no_data"
            result["result"]["overall_sentiment"] = "unknown"
            result["result"]["message"] = f"No data found for {ticker_upper} across any source"
            print(f"\n⚠️  No data found for {ticker_upper}")
        
        # Cache comprehensive result
        persistent_memory.cache_query(cache_key, result, ttl_minutes=30)
        
        # Store in persistent memory
        persistent_memory.add_analysis(ticker_upper, result)
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "comprehensive_sentiment",
                "ticker": company_ticker
            },
            "result": {
                "sentiment": "error",
                "message": str(e)
            },
            "datasources": {
                "sources_queried": [],
                "error": str(e)
            }
        }


def get_sentiment_statistics(source: str = "all") -> dict:
    """
    Returns aggregate sentiment statistics from datasets with structured JSON.
    Automatically discovers and analyzes available data.
    Includes full datasource attribution and low-latency caching.
    
    Args:
        source: Data source - 'news', 'analyst', 'all'
        
    Returns:
        Structured JSON dictionary with sentiment distribution statistics
    """
    try:
        print(f"\n📈 Getting sentiment statistics for: {source}")
        
        # Check cache for low latency
        cache_key = f"statistics_{source}"
        cached = persistent_memory.get_cached_query(cache_key)
        if cached:
            print("⚡ Returning cached statistics")
            return cached.get("result", {})
        
        result = {
            "status": "pending",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "sentiment_statistics",
                "source": source
            },
            "result": {
                "sources": {},
                "overall_metrics": {}
            },
            "datasources": {
                "sources_analyzed": [],
                "files_by_source": {},
                "storage_backend": "gcs" if data_store.use_gcs else "local",
                "base_path": str(data_store.base_path)
            },
            "performance": {
                "cache_hit": False,
                "query_count": data_store._query_count
            }
        }
        
        total_records = 0
        
        if source in ["news", "all"]:
            print("  📰 Analyzing news data...")
            df = data_store.smart_query('news', max_rows=10000)  # Limit for performance
            
            if not df.empty:
                news_files = df['_source_file'].unique().tolist() if '_source_file' in df.columns else []
                
                if 'label' in df.columns:
                    sentiment_counts = df['label'].value_counts().to_dict()
                    sentiment_pcts = (df['label'].value_counts(normalize=True) * 100).round(2).to_dict()
                    
                    # Calculate additional metrics
                    positive = sentiment_counts.get('positive', 0)
                    negative = sentiment_counts.get('negative', 0)
                    neutral = sentiment_counts.get('neutral', 0)
                    total = len(df)
                    
                    result["result"]["sources"]["news"] = {
                        "total_articles": total,
                        "sentiment_distribution": sentiment_counts,
                        "sentiment_percentages": sentiment_pcts,
                        "sentiment_score": round((positive - negative) / total, 3) if total > 0 else 0,
                        "unique_stocks": df['stock'].nunique() if 'stock' in df.columns else 0,
                        "top_mentioned_stocks": df['stock'].value_counts().head(10).to_dict() if 'stock' in df.columns else {}
                    }
                    
                    result["datasources"]["files_by_source"]["news"] = news_files
                    result["datasources"]["sources_analyzed"].append("news")
                    total_records += total
                    
                    print(f"    ✓ Analyzed {total} articles from {len(news_files)} file(s)")
        
        if source in ["analyst", "all"]:
            print("  📊 Analyzing analyst data...")
            df = data_store.smart_query('analyst', max_rows=10000)
            
            if not df.empty:
                analyst_files = df['_source_file'].unique().tolist() if '_source_file' in df.columns else []
                total_analyst = len(df)
                
                analyst_stats = {
                    "total_ratings": total_analyst,
                    "unique_stocks": df['stock'].nunique() if 'stock' in df.columns else 0,
                    "top_analyzed_stocks": df['stock'].value_counts().head(10).to_dict() if 'stock' in df.columns else {}
                }
                
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    analyst_stats["date_range"] = {
                        "earliest": str(df['date'].min()),
                        "latest": str(df['date'].max()),
                        "span_days": (df['date'].max() - df['date'].min()).days if not df['date'].isna().all() else 0
                    }
                
                # Analyze upgrade/downgrade sentiment
                upgrade_keywords = ['upgrade', 'raise', 'outperform', 'buy', 'beat', 'higher', 'positive']
                downgrade_keywords = ['downgrade', 'lower', 'cut', 'sell', 'miss', 'underperform', 'negative']
                
                upgrades = 0
                downgrades = 0
                
                for _, row in df.iterrows():
                    title = str(row.get('title', '')).lower()
                    if any(word in title for word in upgrade_keywords):
                        upgrades += 1
                    elif any(word in title for word in downgrade_keywords):
                        downgrades += 1
                
                analyst_stats["sentiment_analysis"] = {
                    "upgrades": upgrades,
                    "downgrades": downgrades,
                    "upgrade_ratio": round(upgrades / total_analyst, 3) if total_analyst > 0 else 0,
                    "sentiment_score": round((upgrades - downgrades) / total_analyst, 3) if total_analyst > 0 else 0
                }
                
                result["result"]["sources"]["analyst"] = analyst_stats
                result["datasources"]["files_by_source"]["analyst"] = analyst_files
                result["datasources"]["sources_analyzed"].append("analyst")
                total_records += total_analyst
                
                print(f"    ✓ Analyzed {total_analyst} ratings from {len(analyst_files)} file(s)")
        
        # Calculate overall metrics
        if result["datasources"]["sources_analyzed"]:
            result["status"] = "success"
            result["result"]["overall_metrics"] = {
                "total_records_analyzed": total_records,
                "sources_count": len(result["datasources"]["sources_analyzed"]),
                "sources": result["datasources"]["sources_analyzed"]
            }
            
            # Aggregate sentiment if both sources available
            if "news" in result["result"]["sources"] and "analyst" in result["result"]["sources"]:
                news_score = result["result"]["sources"]["news"]["sentiment_score"]
                analyst_score = result["result"]["sources"]["analyst"]["sentiment_analysis"]["sentiment_score"]
                overall_score = (news_score + analyst_score) / 2
                
                result["result"]["overall_metrics"]["composite_sentiment_score"] = round(overall_score, 3)
                result["result"]["overall_metrics"]["interpretation"] = (
                    "positive" if overall_score > 0.1 else "negative" if overall_score < -0.1 else "neutral"
                )
            
            print(f"\n✅ Statistics generated: {total_records} records from {len(result['datasources']['sources_analyzed'])} source(s)")
        else:
            result["status"] = "no_data"
            result["result"]["message"] = f"No data available for source: {source}"
            print(f"\n⚠️  No data found for source: {source}")
        
        # Cache for future queries
        persistent_memory.cache_query(cache_key, result, ttl_minutes=60)
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "sentiment_statistics",
                "source": source
            },
            "result": {
                "message": str(e)
            },
            "datasources": {
                "error": str(e)
            }
        }


def recall_ticker_history(ticker: str) -> dict:
    """
    Recall all historical analyses for a specific ticker from agent memory.
    Provides continuity across sessions with low-latency access.
    
    Args:
        ticker: Stock ticker symbol
        
    Returns:
        Structured JSON with historical analysis data
    """
    try:
        ticker_upper = ticker.upper()
        print(f"\n🧠 Recalling memory for {ticker_upper}")
        
        history = persistent_memory.get_ticker_history(ticker_upper)
        
        result = {
            "status": "success" if history else "no_data",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "recall_memory",
                "ticker": ticker_upper
            },
            "result": {
                "ticker": ticker_upper,
                "analysis_count": len(history),
                "history": history,
                "first_analyzed": history[0]["timestamp"] if history else None,
                "last_analyzed": history[-1]["timestamp"] if history else None
            },
            "datasources": {
                "source": "agent_persistent_memory",
                "storage_backend": "gcs" if persistent_memory.fs else "in_memory_only"
            },
            "performance": {
                "cache_hit": True,
                "latency": "ultra_low"
            }
        }
        
        if history:
            print(f"✅ Found {len(history)} historical analysis(es) for {ticker_upper}")
        else:
            print(f"⚠️  No historical data for {ticker_upper}")
            result["result"]["message"] = f"No previous analyses found for {ticker_upper}"
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "recall_memory",
                "ticker": ticker
            },
            "result": {
                "message": str(e)
            }
        }


def search_agent_memory(query: str) -> dict:
    """
    Search through agent's persistent memory for relevant information.
    Ultra-low latency access to historical insights and analyses.
    
    Args:
        query: Search query (ticker, keyword, or phrase)
        
    Returns:
        Structured JSON with matching memory entries
    """
    try:
        print(f"\n🔍 Searching memory for: {query}")
        
        search_results = persistent_memory.search_memory(query)
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "memory_search",
                "search_term": query
            },
            "result": {
                "tickers_found": search_results.get("tickers", []),
                "insights_found": search_results.get("insights", []),
                "total_matches": len(search_results.get("tickers", [])) + len(search_results.get("insights", [])),
                "statistics": search_results.get("statistics", {})
            },
            "datasources": {
                "source": "agent_persistent_memory",
                "storage_backend": "gcs" if persistent_memory.fs else "in_memory_only",
                "memory_stats": persistent_memory.memory.get("statistics", {})
            },
            "performance": {
                "cache_hit": True,
                "latency": "ultra_low"
            }
        }
        
        print(f"✅ Found {result['result']['total_matches']} match(es)")
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "memory_search",
                "search_term": query
            },
            "result": {
                "message": str(e)
            }
        }


def get_memory_statistics() -> dict:
    """
    Get statistics about agent's persistent memory usage and performance.
    Provides insights into cache hit rates, stored analyses, and more.
    
    Returns:
        Structured JSON with memory statistics
    """
    try:
        print(f"\n📊 Retrieving memory statistics")
        
        memory_stats = persistent_memory.memory.get("statistics", {})
        
        result = {
            "status": "success",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "memory_statistics"
            },
            "result": {
                "memory_info": {
                    "version": persistent_memory.memory.get("version"),
                    "created_at": persistent_memory.memory.get("created_at"),
                    "last_updated": persistent_memory.memory.get("last_updated"),
                    "session_count": persistent_memory.memory.get("session_count", 0)
                },
                "statistics": memory_stats,
                "stored_data": {
                    "unique_tickers_analyzed": len(persistent_memory.memory.get("analyzed_tickers", {})),
                    "total_insights": len(persistent_memory.memory.get("insights", [])),
                    "cached_queries": len(persistent_memory.memory.get("query_cache", {})),
                    "sentiment_history_entries": len(persistent_memory.memory.get("sentiment_history", []))
                },
                "top_analyzed_tickers": list(persistent_memory.memory.get("analyzed_tickers", {}).keys())[:10]
            },
            "datasources": {
                "source": "agent_persistent_memory",
                "storage_backend": "gcs" if persistent_memory.fs else "in_memory_only",
                "memory_file": persistent_memory.memory_file if persistent_memory.memory_file else "in_memory_only"
            },
            "performance": {
                "cache_hit_rate": round(
                    memory_stats.get("cache_hits", 0) / memory_stats.get("total_queries", 1), 3
                ) if memory_stats.get("total_queries", 0) > 0 else 0,
                "total_queries": memory_stats.get("total_queries", 0),
                "cache_hits": memory_stats.get("cache_hits", 0)
            }
        }
        
        print(f"✅ Memory statistics retrieved")
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "timestamp": datetime.now().isoformat(),
            "query": {
                "type": "memory_statistics"
            },
            "result": {
                "message": str(e)
            }
        }


# Export all tools
__all__ = [
    'data_store',
    'persistent_memory',
    'analyze_news_headline',
    'analyze_analyst_sentiment',
    'get_comprehensive_sentiment',
    'get_sentiment_statistics',
    'recall_ticker_history',
    'search_agent_memory',
    'get_memory_statistics'
]
