from app.sub_agents.simulation_agent.engine import (
    simulate_yield_changes,
    compute_metrics,
    TENOR_MAP,
    STRESS_REGIMES
)


def simulate_bond_risk(
    ForecastedYields: dict,
    RegimeHint: str = "normal",
    ConfidenceScore: float | None = None
):
    """
    Simulate bond yield risk using Monte Carlo methods.
    
    Args:
        ForecastedYields: Dict mapping tenor (e.g., "5Y") to forecasted yield value
        RegimeHint: Market regime - "calm", "normal", or "stress" (default: "normal")
        ConfidenceScore: Optional confidence score (not used in current implementation)
    
    Returns:
        Dict with VaR and yield range metrics for each tenor, all JSON-serializable
        Format: {
            "5Y": {"VaR_95_YieldBps": float, "YieldRange_Bps": [float, float], "SimCount": int},
            ...
        }
    """
    # Validate regime
    if RegimeHint not in STRESS_REGIMES:
        return {
            "error": f"Invalid RegimeHint '{RegimeHint}'. Must be one of: {list(STRESS_REGIMES.keys())}"
        }
    
    results = {}
    
    for tenor in ForecastedYields.keys():
        # Validate tenor
        if tenor not in TENOR_MAP:
            results[tenor] = {
                "error": f"Invalid tenor '{tenor}'. Must be one of: {list(TENOR_MAP.keys())}"
            }
            continue
        
        try:
            simulated_changes = simulate_yield_changes(tenor, RegimeHint)
            # compute_metrics returns all Python native types (float, int)
            results[tenor] = compute_metrics(simulated_changes)
        except Exception as e:
            results[tenor] = {
                "error": str(e)
            }

    return results
