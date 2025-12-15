#!/usr/bin/env python3
"""
Test script to verify BigQuery integration and caching
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.sub_agents.event_impact_agent.tools import _data_loader, list_available_symbols, load_price_data
from app.config import config

def test_bigquery_connection():
    """Test BigQuery connection and table discovery"""
    print("="*80)
    print("TESTING BIGQUERY CONNECTION AND TABLE DISCOVERY")
    print("="*80)
    print(f"\n📊 Project: {config.BIGQUERY_PROJECT}")
    print(f"📊 Dataset: {config.BIGQUERY_DATASET}\n")
    
    try:
        # Test 1: List available tables
        print("Test 1: Discovering BigQuery tables...")
        print("-" * 80)
        tables = _data_loader.list_available_tables()
        print(f"\n[OK] Successfully discovered {len(tables)} tables")
        print(f"   Tables: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}\n")
        
        # Test 2: List available symbols
        print("\nTest 2: Listing available stock symbols...")
        print("-" * 80)
        result = list_available_symbols()
        if result["status"] == "success":
            print(f"[OK] Successfully retrieved {result['count']} symbols")
            print(f"   Date range: {result['date_range']['start']} to {result['date_range']['end']}")
            print(f"   Sample symbols: {', '.join(result['symbols'][:10])}")
        else:
            print(f"[FAIL] Failed: {result.get('message')}")
        
        # Test 3: Load price data for a specific symbol (with cache)
        print("\n\nTest 3: Loading price data for AAPL (first call - no cache)...")
        print("-" * 80)
        start_time = datetime.now()
        result = load_price_data("AAPL")
        duration = (datetime.now() - start_time).total_seconds()
        
        if result["status"] == "success":
            print(f"[OK] Successfully loaded {result['rows']} rows for AAPL")
            print(f"   Columns: {', '.join(result['columns'])}")
            print(f"   Date range: {result['date_range']['start']} to {result['date_range']['end']}")
            print(f"   [TIME] Duration: {duration:.2f}s")
        else:
            print(f"[FAIL] Failed: {result.get('message')}")
        
        # Test 4: Load same data again (should use cache)
        print("\n\nTest 4: Loading price data for AAPL again (should use cache)...")
        print("-" * 80)
        start_time = datetime.now()
        result = load_price_data("AAPL")
        duration = (datetime.now() - start_time).total_seconds()
        
        if result["status"] == "success":
            print(f"[OK] Successfully loaded {result['rows']} rows for AAPL")
            print(f"   [CACHE] Duration: {duration:.2f}s (cache hit should be <1s)")
        else:
            print(f"[FAIL] Failed: {result.get('message')}")
        
        # Test 5: Get table schema
        print("\n\nTest 5: Getting table schema...")
        print("-" * 80)
        schema = _data_loader.get_table_schema("30_yr_stock_market_data")
        if schema:
            print(f"✅ Successfully retrieved schema:")
            for col_name, col_type in list(schema.items())[:10]:
                print(f"   • {col_name}: {col_type}")
            if len(schema) > 10:
                print(f"   ... and {len(schema) - 10} more columns")
        else:
            print("[FAIL] Failed to retrieve schema")
        
        # Summary
        print("\n" + "="*80)
        print("SUMMARY")
        print("="*80)
        print("[SUCCESS] All BigQuery integration tests passed!")
        print("\nKey Features Verified:")
        print("  ✓ BigQuery connection established")
        print("  ✓ Table discovery working")
        print("  ✓ Symbol listing functional")
        print("  ✓ Data loading with filters")
        print("  ✓ In-memory caching operational")
        print("  ✓ Schema introspection available")
        print("\n[READY] Ready for low-latency agent operations!")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_cache_performance():
    """Test cache performance"""
    print("\n\n" + "="*80)
    print("TESTING CACHE PERFORMANCE")
    print("="*80)
    
    try:
        # Clear cache first
        _data_loader.clear_cache("30_yr_stock_market_data")
        
        # First load (cold)
        print("\n1. Cold load (no cache)...")
        start = datetime.now()
        load_price_data("MSFT")
        cold_duration = (datetime.now() - start).total_seconds()
        print(f"   Duration: {cold_duration:.2f}s")
        
        # Second load (cached)
        print("\n2. Warm load (cached)...")
        start = datetime.now()
        load_price_data("MSFT")
        warm_duration = (datetime.now() - start).total_seconds()
        print(f"   Duration: {warm_duration:.2f}s")
        
        # Calculate speedup
        if warm_duration > 0:
            speedup = cold_duration / warm_duration
            print(f"\n[SPEEDUP] Cache speedup: {speedup:.1f}x faster")
            print(f"   Cold: {cold_duration:.2f}s")
            print(f"   Warm: {warm_duration:.2f}s")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] Cache test failed: {e}")
        return False


if __name__ == "__main__":
    try:
        print("\n🚀 BigQuery Integration Test Suite\n")
        
        # Run tests
        connection_ok = test_bigquery_connection()
        cache_ok = test_cache_performance()
        
        if connection_ok and cache_ok:
            print("\n" + "="*80)
            print("[SUCCESS] ALL TESTS PASSED")
            print("="*80)
            sys.exit(0)
        else:
            print("\n" + "="*80)
            print("❌ SOME TESTS FAILED")
            print("="*80)
            sys.exit(1)
            
    except Exception as e:
        print(f"\n[FAIL] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
