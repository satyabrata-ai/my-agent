from app.simulation.simulation_engine import simulate_yield_changes, compute_metrics


def run_risk_simulation(
    ForecastedYields: dict,
    RegimeHint: str = "normal",
    ConfidenceScore: float | None = None
):
    """
    Entry point called by SimulationAgent tools
    """
    results = {}

    for tenor in ForecastedYields.keys():
        simulated_changes = simulate_yield_changes(tenor, RegimeHint)
        results[tenor] = compute_metrics(simulated_changes)

    return results
