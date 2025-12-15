import pytest

from app.sub_agents.simulation_agent.tools import simulate_bond_risk


def test_simulate_bond_risk_single_tenor():
    """
    Unit test for simulate_bond_risk with a single bond tenor (5Y)
    """

    # ---------- Arrange ----------
    input_payload = {
        "ForecastedYields": {"5Y": 0.041},
        "RegimeHint": "normal",
        "ConfidenceScore": 0.82
    }

    # ---------- Act ----------
    result = simulate_bond_risk(
        ForecastedYields=input_payload["ForecastedYields"],
        RegimeHint=input_payload["RegimeHint"],
        ConfidenceScore=input_payload["ConfidenceScore"]
    )

    # ---------- Assert ----------
    assert "5Y" in result, "Missing 5Y result"

    metrics = result["5Y"]

    assert "VaR_95_YieldBps" in metrics
    assert "YieldRange_Bps" in metrics
    assert "SimCount" in metrics

    assert isinstance(metrics["VaR_95_YieldBps"], (int, float))
    assert isinstance(metrics["YieldRange_Bps"], list)
    assert len(metrics["YieldRange_Bps"]) == 2

    low, high = metrics["YieldRange_Bps"]
    assert low < high, "Yield range lower bound must be < upper bound"

    assert metrics["SimCount"] == 10000
