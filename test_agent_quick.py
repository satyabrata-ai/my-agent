#!/usr/bin/env python3
"""
Quick test script to verify the intelligent sentiment agent works.
Tests file discovery, GCS connectivity, and tool functions.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

print("=" * 80)
print("NEWSS SENTIMENT AGENT - QUICK TEST")
print("=" * 80)

# Test 1: Import and initialize data store
print("\n1️⃣ Testing data store initialization...")
try:
    from app.sub_agents.news_sentiment_agent.tools import data_store
    print("   ✅ Data store imported successfully")
    print(f"   ℹ️  Using GCS: {data_store.use_gcs}")
    print(f"   ℹ️  Base path: {data_store.base_path}")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

# Test 2: Check file catalog
print("\n2️⃣ Checking file catalog...")
try:
    catalog = data_store.file_catalog
    
    news_count = len(catalog['sentiment_sources']['news'])
    analyst_count = len(catalog['sentiment_sources']['analyst'])
    transcript_count = len(catalog['sentiment_sources']['transcripts'])
    
    print(f"   📰 News files: {news_count}")
    print(f"   📊 Analyst files: {analyst_count}")
    print(f"   🎤 Transcript files: {transcript_count}")
    
    if news_count == 0 and analyst_count == 0:
        print("   ⚠️  Warning: No data files discovered!")
        print("   💡 Check your GCS_DATA_BUCKET configuration")
    else:
        print("   ✅ Files discovered successfully")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 3: Test news headline analysis
print("\n3️⃣ Testing analyze_news_headline...")
try:
    from app.sub_agents.news_sentiment_agent.tools import analyze_news_headline
    
    test_headline = "Company announces earnings beat"
    result = analyze_news_headline(test_headline)
    
    print(f"   Headline: '{test_headline}'")
    print(f"   Status: {result.get('status')}")
    print(f"   Sentiment: {result.get('sentiment', 'N/A')}")
    
    if result.get('status') == 'success':
        print("   ✅ Tool working correctly")
    elif result.get('status') == 'no_data':
        print("   ⚠️  No data available (check GCS connectivity)")
    else:
        print(f"   ℹ️  Status: {result.get('status')}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Test analyst sentiment
print("\n4️⃣ Testing analyze_analyst_sentiment...")
try:
    from app.sub_agents.news_sentiment_agent.tools import analyze_analyst_sentiment
    
    test_ticker = "AAPL"
    result = analyze_analyst_sentiment(test_ticker)
    
    print(f"   Ticker: {test_ticker}")
    print(f"   Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        print(f"   Sentiment: {result.get('sentiment')}")
        print(f"   Total ratings: {result.get('total_ratings')}")
        print("   ✅ Tool working correctly")
    elif result.get('status') == 'no_data':
        print("   ⚠️  No analyst data found for this ticker")
    else:
        print(f"   ℹ️  Status: {result.get('status')}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 5: Test comprehensive sentiment
print("\n5️⃣ Testing get_comprehensive_sentiment...")
try:
    from app.sub_agents.news_sentiment_agent.tools import get_comprehensive_sentiment
    
    test_ticker = "MSFT"
    result = get_comprehensive_sentiment(test_ticker)
    
    print(f"   Ticker: {test_ticker}")
    print(f"   Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        sources = len(result.get('data_sources_used', []))
        print(f"   Data sources used: {sources}")
        print(f"   Summary: {list(result.get('sentiment_summary', {}).keys())}")
        print("   ✅ Tool working correctly")
    elif result.get('status') == 'no_data':
        print("   ⚠️  No data found for this ticker")
    else:
        print(f"   ℹ️  Status: {result.get('status')}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 6: Test statistics
print("\n6️⃣ Testing get_sentiment_statistics...")
try:
    from app.sub_agents.news_sentiment_agent.tools import get_sentiment_statistics
    
    result = get_sentiment_statistics("news")
    
    print(f"   Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        news_stats = result.get('sources', {}).get('news', {})
        if news_stats:
            print(f"   Total articles: {news_stats.get('total_articles', 0)}")
            print("   ✅ Tool working correctly")
        else:
            print("   ⚠️  No news statistics available")
    else:
        print(f"   ℹ️  Status: {result.get('status')}")
        
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 7: Agent initialization
print("\n7️⃣ Testing agent initialization...")
try:
    from app.sub_agents.news_sentiment_agent.agent import news_sentiment_agent
    
    print(f"   Name: {news_sentiment_agent.name}")
    print(f"   Model: {news_sentiment_agent.model}")
    print(f"   Tools: {len(news_sentiment_agent.tools)}")
    print("   ✅ Agent initialized successfully")
    
except Exception as e:
    print(f"   ❌ Error: {e}")
    import traceback
    traceback.print_exc()

# Summary
print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("\n✅ If all tests passed:")
print("   Your agent is ready to use!")
print("   Run: make playground")
print("   Then ask: 'What's the sentiment for Apple?'")
print("\n⚠️  If tests failed:")
print("   1. Check GCS_DATA_BUCKET in .env")
print("   2. Run: gcloud auth application-default login")
print("   3. Run GCS tests: pytest tests/integration/test_gcs_connection.py -v -s")
print("\n📚 Documentation:")
print("   - AGENT_IMPLEMENTATION_SUMMARY.md")
print("   - GCS_QUICKSTART.md")
print("   - tests/integration/README_GCS_TESTS.md")
print("=" * 80)
