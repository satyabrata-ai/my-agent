# app/agent.py
import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps.app import App

import os
import google.auth

from app.sub_agents.news_sentiment_agent import news_sentiment_agent
from app.sub_agents.data_orchestrator import data_orchestrator_agent
from app.config import config  # ⬅️ Import central config


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
        "Do not allow direct BigQuery access from NewsSentimentAgent; always route through Data Orchestrator."
    ),
    sub_agents=[
        news_sentiment_agent,
        data_orchestrator_agent
    ]
)

app = App(root_agent=root_agent, name="app")