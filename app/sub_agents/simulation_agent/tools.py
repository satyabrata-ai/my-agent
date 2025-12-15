from app.simulation.simulation_agent import run_risk_simulation


def simulate_bond_risk(
    ForecastedYields: dict,
    RegimeHint: str = "normal",
    ConfidenceScore: float | None = None
):
    """
    Tool wrapper for Simulation Agent.

    Expected input:
    {
      "ForecastedYields": { "5Y": 0.041 },
      "RegimeHint": "normal",
      "ConfidenceScore": 0.82
    }
    """

    return run_risk_simulation(
        ForecastedYields=ForecastedYields,
        RegimeHint=RegimeHint,
        ConfidenceScore=ConfidenceScore
    )
