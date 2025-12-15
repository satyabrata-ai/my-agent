import pandas as pd

def test_detect_high_volatility_triggers_alert(monkeypatch):
    from app.sub_agents.realtime_alerts.tools import detect_high_volatility

    def fake_get_baseline_metrics(ticker, price_table=None, lookback_days=5):
        return {"status": "success", "result": {"Ticker": ticker, "HistVol_5D_Ann": 0.8, "SourceTable": "test"}}

    monkeypatch.setattr("app.sub_agents.data_orchestrator.tools.get_baseline_metrics", fake_get_baseline_metrics)

    res = detect_high_volatility(["AAPL"], vol_threshold=0.6)
    assert res["status"] == "success"
    assert len(res["alerts"]) == 1
    assert res["alerts"][0]["ticker"] == "AAPL"


def test_publish_alert_event_uses_pubsub_and_webhook(monkeypatch):
    from app.sub_agents.realtime_alerts import tools as ra_tools
    from app.config import config

    # configure both pubsub and webhook
    config.ALERTS_PUBSUB_TOPIC = "projects/myproj/topics/alerts"
    config.ALERTS_WEBHOOK_URL = "https://example.com/hook"

    called = {"pubsub": False, "webhook": False}

    def fake_pubsub(alert, topic):
        called['pubsub'] = True
        return {"status": "published", "topic": topic}

    def fake_webhook(alert, url):
        called['webhook'] = True
        return {"status": "webhook_posted", "code": 200, "url": url}

    monkeypatch.setattr(ra_tools, "publish_alert_pubsub", fake_pubsub)
    monkeypatch.setattr(ra_tools, "publish_alert_webhook", fake_webhook)

    alert = {"id": "1", "ticker": "AAPL", "alert_type": "high_volatility"}
    ev = ra_tools.publish_alert_event(alert)
    assert ev["type"] == "alert_raised"
    assert isinstance(ev.get("outcomes"), list)
    assert called['pubsub'] is True
    assert called['webhook'] is True


def test_store_alerts_to_bq_calls_insert(monkeypatch):
    from app.sub_agents.realtime_alerts.tools import store_alerts_to_bq

    inserted = {}

    class DummyClient:
        def insert_rows_json(self, table_id, rows):
            inserted['table_id'] = table_id
            inserted['rows'] = rows
            return []  # no errors

    # monkeypatch the _bq_store.client
    import app.sub_agents.data_orchestrator.tools as bq_tools
    bq_tools._bq_store.client = DummyClient()
    bq_tools._bq_store.project = "proj"
    bq_tools._bq_store.dataset = "ds"

    alerts = [{"id": "1", "timestamp": "now", "ticker": "AAPL", "alert_type": "high_volatility", "severity": "high", "metric": "HistVol_5D_Ann", "metric_value": 0.8, "details": {}}]

    res = store_alerts_to_bq(alerts, table_name="realtime_alerts")
    assert res["status"] == "success"
    assert inserted['table_id'] == "proj.ds.realtime_alerts"
    assert len(inserted['rows']) == 1


def test_get_active_alerts_queries_bq(monkeypatch):
    from app.sub_agents.realtime_alerts.tools import get_active_alerts
    import app.sub_agents.data_orchestrator.tools as bq_tools

    df = pd.DataFrame([{"id": "1", "timestamp": "2025-12-15T00:00:00Z", "ticker": "AAPL", "alert_type": "high_volatility", "severity": "high", "metric": "HistVol_5D_Ann", "metric_value": 0.8, "details": "{}"}])
    # monkeypatch the query_to_df method on the _bq_store instance used by tools
    monkeypatch.setattr(bq_tools._bq_store, "query_to_df", lambda sql, limit=None: df)

    res = get_active_alerts(hours=48, table_name="realtime_alerts")
    assert res["status"] == "success"
    assert len(res["alerts"]) == 1
    assert res["alerts"][0]["ticker"] == "AAPL"
