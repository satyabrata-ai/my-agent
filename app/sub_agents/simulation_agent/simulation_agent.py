from app.sub_agents.simulation_agent.tools import simulate_bond_risk


def build_simulation_agent(Agent):
    """
    Factory function to build the SimulationAgent.
    This is called ONLY at runtime, never during tests.
    """
    return Agent(
        name="SimulationAgent",
        model="none",  # ADK requires a string or BaseLlm
        instruction=(
            "You are a bond yield risk simulation agent. "
            "Given forecasted bond yields and a regime hint, "
            "run Monte Carlo simulations to compute yield VaR "
            "and yield ranges in basis points. "
            "Return structured JSON only."
        ),
        tools=[simulate_bond_risk]
    )
