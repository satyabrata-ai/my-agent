#!/usr/bin/env python3
"""
Test script to verify the encoding fix for CSV files
"""
import sys
import os

# Set UTF-8 encoding for console output on Windows
if os.name == 'nt':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from app.sub_agents.event_impact_agent.tools import _data_loader

def test_encoding_fix():
    """Test loading communications.csv with encoding fix"""
    
    print("="*80)
    print("TESTING ENCODING FIX FOR CSV FILES")
    print("="*80)
    
    files_to_test = [
        "communications.csv",
        "30_yr_stock_market_data.csv",
        "US_Economic_Indicators.csv"
    ]
    
    results = {}
    
    for filename in files_to_test:
        print(f"\n📄 Testing {filename}...")
        print("-" * 80)
        
        try:
            df = _data_loader.load_csv_from_gcs(filename, use_cache=False)
            
            print(f"✅ Successfully loaded {filename}")
            print(f"   Rows: {len(df):,}")
            print(f"   Columns: {len(df.columns)}")
            print(f"   Column names: {list(df.columns)[:5]}{'...' if len(df.columns) > 5 else ''}")
            
            results[filename] = {
                "status": "success",
                "rows": len(df),
                "columns": len(df.columns)
            }
            
        except Exception as e:
            print(f"❌ Failed to load {filename}")
            print(f"   Error: {e}")
            results[filename] = {
                "status": "error",
                "error": str(e)
            }
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    success_count = sum(1 for r in results.values() if r["status"] == "success")
    total_count = len(results)
    
    for filename, result in results.items():
        status_icon = "✅" if result["status"] == "success" else "❌"
        print(f"{status_icon} {filename}: {result['status'].upper()}")
        if result["status"] == "success":
            print(f"   → {result['rows']:,} rows, {result['columns']} columns")
    
    print("\n" + "="*80)
    if success_count == total_count:
        print(f"✅ ALL TESTS PASSED ({success_count}/{total_count})")
        print("="*80)
        print("\n🎉 Encoding fix is working correctly!")
        print("   The agent can now read CSV files with special characters.")
        return True
    else:
        print(f"⚠️  PARTIAL SUCCESS ({success_count}/{total_count})")
        print("="*80)
        return False

if __name__ == "__main__":
    try:
        success = test_encoding_fix()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

