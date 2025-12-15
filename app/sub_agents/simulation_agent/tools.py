from app.sub_agents.simulation_agent.engine import (
    simulate_yield_changes,
    compute_metrics
)


def simulate_bond_risk(
    ForecastedYields: dict,
    RegimeHint: str = "normal",
    ConfidenceScore: float | None = None
):
    results = {}

    for tenor in ForecastedYields.keys():
        simulated_changes = simulate_yield_changes(tenor, RegimeHint)
        results[tenor] = compute_metrics(simulated_changes)

    return results
