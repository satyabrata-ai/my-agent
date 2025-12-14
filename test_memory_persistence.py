#!/usr/bin/env python3
"""
Test script to verify persistent memory saves correctly.
Tests the new hybrid save approach (every 5 operations + shutdown).
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.sub_agents.news_sentiment_agent.tools import PersistentMemoryStore

def test_periodic_saves():
    """Test that memory saves every 5 operations"""
    print("=" * 70)
    print("TEST 1: Periodic Saves (Every 5 Operations)")
    print("=" * 70)
    
    memory = PersistentMemoryStore()
    
    test_tickers = ["AAPL", "MSFT", "GOOGL", "TSLA", "AMZN", "META", "NVDA"]
    
    print(f"\n📊 Initial state:")
    print(f"   Operations count: {memory._operations_since_save}")
    print(f"   Dirty flag: {memory._dirty}")
    
    for i, ticker in enumerate(test_tickers, 1):
        print(f"\n{i}. Adding analysis for {ticker}...")
        
        analysis = {
            "sentiment": "positive",
            "score": 0.75,
            "data_sources": ["news_headlines.csv"]
        }
        
        memory.add_analysis(ticker, analysis)
        
        print(f"   Operations count: {memory._operations_since_save}")
        print(f"   Dirty flag: {memory._dirty}")
        
        if i % 5 == 0:
            print(f"   ✅ EXPECTED: Memory should have been saved!")
            assert memory._operations_since_save == 0, "Counter should reset after save"
            assert not memory._dirty, "Dirty flag should be cleared after save"
        
        time.sleep(0.5)  # Small delay for readability
    
    print("\n" + "=" * 70)
    print("✅ TEST 1 PASSED: Periodic saves working correctly!")
    print("=" * 70)

def test_cache_operations():
    """Test that query caching also triggers saves"""
    print("\n" + "=" * 70)
    print("TEST 2: Query Cache Operations")
    print("=" * 70)
    
    memory = PersistentMemoryStore()
    
    print(f"\n📊 Initial state:")
    print(f"   Operations count: {memory._operations_since_save}")
    
    for i in range(1, 6):
        print(f"\n{i}. Caching query result...")
        
        result = {
            "sentiment": "positive",
            "ticker": f"TEST{i}",
            "score": 0.8
        }
        
        memory.cache_query(f"query_{i}", result, ttl_minutes=60)
        
        print(f"   Operations count: {memory._operations_since_save}")
        print(f"   Dirty flag: {memory._dirty}")
        
        if i == 5:
            print(f"   ✅ EXPECTED: Memory should have been saved!")
            assert memory._operations_since_save == 0, "Counter should reset"
    
    print("\n" + "=" * 70)
    print("✅ TEST 2 PASSED: Cache operations trigger saves correctly!")
    print("=" * 70)

def test_mixed_operations():
    """Test mixed operations (analysis + cache + insights)"""
    print("\n" + "=" * 70)
    print("TEST 3: Mixed Operations")
    print("=" * 70)
    
    memory = PersistentMemoryStore()
    
    operations = [
        ("analysis", "AAPL"),
        ("cache", "query_1"),
        ("insight", "Market looks bullish"),
        ("analysis", "MSFT"),
        ("cache", "query_2"),
    ]
    
    print(f"\n📊 Running {len(operations)} mixed operations...")
    
    for i, (op_type, data) in enumerate(operations, 1):
        print(f"\n{i}. Operation: {op_type} ({data})")
        
        if op_type == "analysis":
            memory.add_analysis(data, {"sentiment": "positive"})
        elif op_type == "cache":
            memory.cache_query(data, {"result": "test"})
        elif op_type == "insight":
            memory.add_insight(data, category="market")
        
        print(f"   Operations count: {memory._operations_since_save}")
        print(f"   Dirty flag: {memory._dirty}")
        
        if i == 5:
            print(f"   ✅ EXPECTED: Memory should have been saved!")
            assert memory._operations_since_save == 0, "Counter should reset"
    
    print("\n" + "=" * 70)
    print("✅ TEST 3 PASSED: Mixed operations work correctly!")
    print("=" * 70)

def test_shutdown_save():
    """Test that memory saves on shutdown"""
    print("\n" + "=" * 70)
    print("TEST 4: Shutdown Save (atexit)")
    print("=" * 70)
    
    memory = PersistentMemoryStore()
    
    # Add 3 operations (less than 5, so no auto-save)
    print("\n📊 Adding 3 operations (won't trigger auto-save)...")
    memory.add_analysis("AAPL", {"sentiment": "positive"})
    memory.add_analysis("MSFT", {"sentiment": "positive"})
    memory.add_analysis("GOOGL", {"sentiment": "positive"})
    
    print(f"   Operations count: {memory._operations_since_save} (should be 3)")
    print(f"   Dirty flag: {memory._dirty} (should be True)")
    
    assert memory._operations_since_save == 3, "Should have 3 operations"
    assert memory._dirty, "Should be dirty"
    
    # Simulate shutdown
    print("\n🔄 Simulating shutdown (calling cleanup)...")
    memory.cleanup()
    
    print(f"   Operations count: {memory._operations_since_save} (should be 0)")
    print(f"   Dirty flag: {memory._dirty} (should be False)")
    
    assert memory._operations_since_save == 0, "Should be reset after cleanup"
    assert not memory._dirty, "Should not be dirty after cleanup"
    
    print("\n" + "=" * 70)
    print("✅ TEST 4 PASSED: Shutdown save works correctly!")
    print("=" * 70)

def main():
    """Run all tests"""
    print("\n" + "=" * 70)
    print("🧪 TESTING PERSISTENT MEMORY SAVE FIX")
    print("=" * 70)
    print("\nThis test verifies the hybrid save approach:")
    print("  1. Saves every 5 operations (any type)")
    print("  2. Saves on shutdown (cleanup)")
    print("  3. Resets counter after save")
    print()
    
    try:
        # Run tests
        test_periodic_saves()
        test_cache_operations()
        test_mixed_operations()
        test_shutdown_save()
        
        # Final summary
        print("\n" + "=" * 70)
        print("🎉 ALL TESTS PASSED!")
        print("=" * 70)
        print("\n✅ Memory persistence is working correctly:")
        print("   • Saves every 5 operations ✓")
        print("   • Saves on shutdown ✓")
        print("   • Counter resets after save ✓")
        print("   • Works for all operation types ✓")
        print("\n📁 Memory location:")
        print("   gs://datasets-ccibt-hack25ww7-706/agent_memory/session_memory.json")
        print()
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
