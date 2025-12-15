# app/agent.py
import datetime
from zoneinfo import ZoneInfo

from google.adk.agents import Agent
from google.adk.apps.app import App

import os
import google.auth

from app.sub_agents.news_sentiment_agent import news_sentiment_agent
from app.sub_agents.event_impact_agent import event_impact_agent
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
        "Delegate news analysis to NewsSentimentAgent. "
        "Delegate event impact analysis, volatility analysis, and bond trading signals to EventImpactCorrelationAgent. "
        "Return their outputs clearly and professionally."
    ),
    sub_agents=[
        news_sentiment_agent,
        event_impact_agent
    ]
)

app = App(root_agent=root_agent, name="app")