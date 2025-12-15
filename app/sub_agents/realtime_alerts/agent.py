from google.adk.agents import Agent
from app.config import config

from .tools import (
    detect_high_volatility,
    store_alerts_to_bq,
    publish_alert_event,
    get_active_alerts,
)

realtime_alerts_agent = Agent(
    name="RealtimeAlertsAgent",
    model=config.AGENT_MODEL,
    description="Generates and stores real-time alerts for high-volatility or significant market shifts",
    instruction="""
    You are responsible for detecting imminent high-volatility periods and significant market shifts.
    - Use `detect_high_volatility(tickers, vol_threshold)` to identify candidate alerts.
    - Persist generated alerts to BigQuery with `store_alerts_to_bq()` and raise an event via `publish_alert_event()`.
    - Provide `get_active_alerts(hours)` to return recent alerts for chat responses.

    When invoked by other agents, ensure alerts are stored before returning. Keep messages concise and include alert summary, severity, and justification.
    """,
    tools=[
        detect_high_volatility,
        store_alerts_to_bq,
        publish_alert_event,
        get_active_alerts,
    ]
)
