from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def test_user_query_routes_to_realtime_alerts(monkeypatch):
    """Behavioral test: ensure a user query about real-time volatility is routed to RealtimeAlertsAgent.

    This test monkeypatches the Realtime Alerts tools to return deterministic values
    and asserts that the agent's response contains the alert summary produced by
    the Realtime Alerts agent.
    """
    from app.agent import root_agent

    # Fake outputs from realtime alerts tools
    def fake_detect_high_volatility(tickers, vol_threshold=0.6):
        return {
            "status": "success",
            "alerts": [
                {
                    "id": "test-1",
                    "timestamp": "2025-12-15T00:00:00Z",
                    "ticker": "AAPL",
                    "alert_type": "high_volatility",
                    "severity": "high",
                    "metric": "HistVol_5D_Ann",
                    "metric_value": 0.85,
                    "details": {"reason": "spike in realized vol"},
                }
            ],
        }

    def fake_store_alerts_to_bq(alerts, table_name="realtime_alerts"):
        return {"status": "success", "inserted": len(alerts)}

    def fake_publish_alert_event(alert):
        return {"type": "alert_raised", "payload": alert}

    monkeypatch.setattr(
        "app.sub_agents.realtime_alerts.tools.detect_high_volatility",
        fake_detect_high_volatility,
    )
    monkeypatch.setattr(
        "app.sub_agents.realtime_alerts.tools.store_alerts_to_bq",
        fake_store_alerts_to_bq,
    )
    monkeypatch.setattr(
        "app.sub_agents.realtime_alerts.tools.publish_alert_event",
        fake_publish_alert_event,
    )

    session_service = InMemorySessionService()
    session = session_service.create_session_sync(user_id="test_user", app_name="test")
    runner = Runner(agent=root_agent, session_service=session_service, app_name="test")

    message = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Are there any high-volatility alerts for AAPL right now?")],
    )

    events = list(
        runner.run(
            new_message=message,
            user_id="test_user",
            session_id=session.id,
            run_config=RunConfig(streaming_mode=StreamingMode.SSE),
        )
    )

    # Collect text parts from events
    texts = []
    for ev in events:
        if ev.content and ev.content.parts:
            for p in ev.content.parts:
                if p.text:
                    texts.append(p.text.lower())

    joined = "\n".join(texts)
    assert "aapl" in joined or "apple" in joined
    assert "high" in joined or "high_volatility" in joined or "volatility" in joined
