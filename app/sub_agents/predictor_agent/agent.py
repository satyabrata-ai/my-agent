from google.adk.agents import Agent
from app.config import config
from .tools import (
    yield_curve_tool
)
from .prompt import PREDICTOR_AGENT_PROMPT

predictor_agent = Agent(
    name="PredictorAgent",
    model=config.AGENT_MODEL,
    description="High-performance financial sentiment analyzer with persistent memory, low-latency caching, and automatic GCS data discovery",
    instruction=PREDICTOR_AGENT_PROMPT,
    tools =[yield_curve_tool]
)