#!/usr/bin/env python3
"""Quick test of key functions"""
import sys
sys.path.insert(0, '.')

from app.sub_agents.event_impact_agent.tools import list_available_symbols, load_price_data

print("="*80)
print("QUICK BIGQUERY TEST")
print("="*80)

# Test 1: List symbols
print("\nTest 1: Listing available symbols...")
result = list_available_symbols()
if result["status"] == "success":
    print(f"[OK] Found {result['count']} symbols")
    print(f"   Sample: {', '.join(result['symbols'][:10])}")
else:
    print(f"[FAIL] {result.get('message')}")

# Test 2: Load price data for AAPL
print("\nTest 2: Loading price data for AAPL...")
result = load_price_data("AAPL")
if result["status"] == "success":
    print(f"[OK] Loaded {result['rows']} rows")
    print(f"   Date range: {result['date_range']}")
else:
    print(f"[FAIL] {result.get('message')}")

print("\n" + "="*80)
print("[SUCCESS] Quick test complete!")
print("="*80)
