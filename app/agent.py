# app/agent.py
import os
from google.adk.agents import Agent, SequentialAgent
from google.adk.apps.app import App

from app.sub_agents.news_sentiment_agent import news_sentiment_agent
from app.sub_agents.data_orchestrator import data_orchestrator_agent
from app.sub_agents.realtime_alerts import realtime_alerts_agent
from app.sub_agents.event_impact_agent import event_impact_agent
from app.sub_agents.predictor_agent.agent import predictor_agent
from app.sub_agents.simulation_agent import build_simulation_agent
from app.config import config


# ─────────────────────────────────────────────────────────────
# Environment configuration
# ─────────────────────────────────────────────────────────────
os.environ["GOOGLE_CLOUD_PROJECT"] = config.GOOGLE_CLOUD_PROJECT
os.environ["GOOGLE_CLOUD_LOCATION"] = config.GOOGLE_CLOUD_LOCATION
os.environ["GOOGLE_GENAI_USE_VERTEXAI"] = config.GOOGLE_GENAI_USE_VERTEXAI
os.environ["LOGS_BUCKET_NAME"] = config.LOGS_BUCKET_NAME

if config.is_development:
    print(config)


# ─────────────────────────────────────────────────────────────
# Sequential advisor (prediction pipeline)
# ─────────────────────────────────────────────────────────────
bond_investment_advisor = SequentialAgent(
    name="BondInvestmentAdvisor",
    sub_agents=[
        predictor_agent,
        build_simulation_agent,  # ✅ Agent instance
    ],
)


# ─────────────────────────────────────────────────────────────
# Root orchestrator
# ─────────────────────────────────────────────────────────────
root_agent = Agent(
    name="BondNavigator",
    model=config.AGENT_MODEL,
    instruction=(
        "You are an agentic fixed-income intelligence coordinator.\n\n"

        "NEWS:\n"
        "- Delegate news analysis to NewsSentimentAgent.\n"
        "- NewsSentimentAgent must fetch all market/news data ONLY via "
        "Data Orchestrator using `get_sentiment_sources()`.\n"
        "- Allowed BigQuery tables: stock_news, 30_yr_stock_market_data, "
        "US_Economic_Indicators, combined_transcripts.\n\n"

        "REAL-TIME ALERTS:\n"
        "- For real-time volatility or imminent market shifts, delegate to "
        "RealtimeAlertsAgent.\n"
        "- RealtimeAlertsAgent must use detect_high_volatility, "
        "store_alerts_to_bq, publish_alert_event, and get_active_alerts.\n\n"

        "EVENT ANALYSIS:\n"
        "- For event-driven market impact or bond volatility strategies, "
        "delegate to EventImpactCorrelationAgent.\n\n"

        "PREDICTIONS & INVESTMENT ADVICE:\n"
        "- For bond yield predictions, treasury outlooks, or fixed-income "
        "investment advice, invoke BondInvestmentAdvisor.\n"
        "- BondInvestmentAdvisor MUST run agents in this order:\n"
        "  1) PredictorAgent\n"
        "  2) SimulationAgent\n"
        "- Each agent receives the user query and the full output of the "
        "previous agent.\n"
    ),
    sub_agents=[
        news_sentiment_agent,
        data_orchestrator_agent,
        realtime_alerts_agent,
        event_impact_agent,
        bond_investment_advisor,
    ],
)


app = App(root_agent=root_agent, name="app")
