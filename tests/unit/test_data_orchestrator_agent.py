import pytest

from app.sub_agents.data_orchestrator import data_orchestrator_agent
from app.sub_agents.data_orchestrator import tools as da_tools


def test_agent_import_and_tools():
    assert data_orchestrator_agent.name == "DataOrchestrator"
    # Agent should expose listed tools
    tool_names = [t.__name__ for t in data_orchestrator_agent.tools]
    expected = {"discover_bq_tables", "query_table", "get_baseline_metrics", "list_upcoming_events"}
    assert expected.issubset(set(tool_names))


def test_baseline_metrics_no_bq_available():
    # In a dev environment without google-cloud-bigquery, the tool should return an error or no_data
    res = da_tools.get_baseline_metrics("AAPL")
    assert isinstance(res, dict)
    assert "status" in res
