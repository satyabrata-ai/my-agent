def test_get_sentiment_sources_tables_present():
    from app.sub_agents.data_orchestrator.tools import get_sentiment_sources

    res = get_sentiment_sources(ticker=None, limit=1)

    assert res.get("status") in ("success", "error")
    # Ensure the structure contains only the allowed table keys
    tables = res.get("tables", {})
    assert set(tables.keys()) == {"stock_news", "market_data", "economic", "transcripts"}
