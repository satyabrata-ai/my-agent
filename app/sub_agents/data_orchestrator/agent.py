from google.adk.agents import Agent
from app.config import config
from .tools import (
    discover_bq_tables,
    query_table,
    get_baseline_metrics,
    list_upcoming_events,
)


data_orchestrator_agent = Agent(
    name="DataOrchestrator",
    model=config.AGENT_MODEL,
    description="Provides BigQuery-backed market data ingestion, normalization and baseline metrics",
    instruction="""
    You are the Data Orchestrator. Provide low-latency access to market data, compute baseline
    metrics (historical volatility, latest price), list upcoming events, and expose a SQL query interface.
    Use existing BigQuery dataset configured in app.config.BIGQUERY_DATASET.
    Return JSON-serializable structures for downstream agents.
    """,
    tools=[
        discover_bq_tables,
        query_table,
        get_baseline_metrics,
        list_upcoming_events,
    ],
)
