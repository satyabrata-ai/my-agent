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
        RegimeHint: Market regime - "calm", "normal", or "stress"
        ConfidenceScore: Optional confidence score from predictive agent

    Returns:
        Structured JSON output to be interpreted by Gemini (Agent model)
    """

    # Validate regime
    if RegimeHint not in STRESS_REGIMES:
        return {
            "status": "error",
            "message": f"Invalid RegimeHint '{RegimeHint}'. Must be one of {list(STRESS_REGIMES.keys())}"
        }

    results = {}

    for tenor in ForecastedYields.keys():
        if tenor not in TENOR_MAP:
            results[tenor] = {
                "error": f"Invalid tenor '{tenor}'. Must be one of {list(TENOR_MAP.keys())}"
            }
            continue

        try:
            simulated_changes = simulate_yield_changes(
                tenor=tenor,
                regime=RegimeHint
            )
            results[tenor] = compute_metrics(simulated_changes)

        except Exception as e:
            results[tenor] = {"error": str(e)}

    # High-level interpretation hints (NOT LLM-generated)
    interpretation = {
        "market_regime": RegimeHint,
        "confidence_score": ConfidenceScore,
        "risk_level": (
            "high" if RegimeHint == "stress"
            else "moderate" if RegimeHint == "normal"
            else "low"
        ),
        "guidance": (
            "Downside yield risk is elevated across the curve."
            if RegimeHint == "stress"
            else "Yield risk is present but contained."
            if RegimeHint == "normal"
            else "Yield volatility remains subdued."
        )
    }

    return {
        "status": "ok",
        "simulation_results": results,
        "interpretation": interpretation
    }
