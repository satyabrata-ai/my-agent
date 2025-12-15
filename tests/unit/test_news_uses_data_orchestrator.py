def test_comprehensive_calls_data_orchestrator(monkeypatch):
    """Ensure NewsSentimentAgent uses Data Orchestrator's get_sentiment_sources."""
    from app.sub_agents.news_sentiment_agent.tools import get_comprehensive_sentiment

    def fake_get_sentiment_sources(ticker, limit=1000):
        return {
            "status": "success",
            "tables": {
                "stock_news": {"row_count": 1, "rows": [{"headline": "Test headline", "label": "positive"}]},
                "transcripts": {"row_count": 0, "rows": []},
                "market_data": {"row_count": 0, "rows": []},
                "economic": {"row_count": 0, "rows": []},
            }
        }

    # Patch the function where News agent imports it (module-local binding)
    import importlib
    ns_tools_module = importlib.import_module("app.sub_agents.news_sentiment_agent.tools")
    monkeypatch.setattr(ns_tools_module, "get_sentiment_sources", fake_get_sentiment_sources)


    # Ensure cached comprehensive results are cleared for a fresh run
    from app.sub_agents.news_sentiment_agent import tools as ns_tools
    ns_tools.persistent_memory._in_memory_cache.clear()
    ns_tools.persistent_memory.memory.get('query_cache', {}).pop('comprehensive_AAPL_True', None)
    ns_tools.persistent_memory.memory.get('analyzed_tickers', {}).pop('AAPL', None)

    res = get_comprehensive_sentiment("AAPL")

    assert res["status"] == "success"
    assert "news" in res["datasources"]["sources_with_data"]
    assert res["result"]["sentiment_by_source"]["news"]["total_articles"] == 1
