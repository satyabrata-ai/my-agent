# app/agent.py
import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps.app import App

import os
import google.auth

from app.sub_agents.news_sentiment_agent import news_sentiment_agent
from app.sub_agents.data_orchestrator import data_orchestrator_agent
from app.sub_agents.realtime_alerts import realtime_alerts_agent
from app.sub_agents.event_impact_agent import event_impact_agent
from app.config import config  # ⬅️ Import central config
from app.sub_agents.simulation_agent import build_simulation_agent


# 🔹 Build the simulation agent INSTANCE
simulation_agent = build_simulation_agent(Agent)


# Apply configuration to environment
os.environ["GOOGLE_CLOUD_PROJECT"] = config.GOOGLE_CLOUD_PROJECT
os.environ["GOOGLE_CLOUD_LOCATION"] = config.GOOGLE_CLOUD_LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = config.GOOGLE_GENAI_USE_VERTEXAI
os.environ["LOGS_BUCKET_NAME"] = config.LOGS_BUCKET_NAME

# Optional: Print config in development
if config.is_development:
    print(config)


root_agent = Agent(
    name="BondNavigator",
    model=config.AGENT_MODEL,
    instruction=(
        "You are an agentic fixed-income intelligence coordinator. "
            "Delegate news analysis to NewsSentimentAgent and ensure it fetches all market/news data via the Data Orchestrator. "
            "When NewsSentimentAgent requires fresh data, it must call Data Orchestrator's `get_sentiment_sources()` and only the following BigQuery tables may be accessed: `stock_news`, `30_yr_stock_market_data`, `US_Economic_Indicators`, `combined_transcripts`. "
            "Do not allow direct BigQuery access from NewsSentimentAgent; always route through Data Orchestrator. "
            "For any user request about real-time volatility, imminent high-volatility periods, or significant market shifts, delegate the task to RealtimeAlertsAgent. "
            "RealtimeAlertsAgent must be used to detect, persist, and publish alerts (use `detect_high_volatility`, `store_alerts_to_bq`, `publish_alert_event`, and `get_active_alerts`). "
            "Do not attempt to answer or query live volatility data yourself; always call RealtimeAlertsAgent for these requests. "
            "For any user request about event-driven market impact, historical event correlations, or bond volatility trading strategies, delegate to EventImpactCorrelationAgent. "
            "Use EventImpactCorrelationAgent to analyze how markets react to financial events (Fed announcements, macro releases, earnings, M&A) and to provide bond volatility trading signals."
    ),
    sub_agents=[
        news_sentiment_agent,
        data_orchestrator_agent,
        realtime_alerts_agent,
        event_impact_agent,
    ]
)

app = App(root_agent=root_agent, name="app")