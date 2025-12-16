from app.sub_agents.simulation_agent.tools import simulate_bond_risk
from app.config import config

def build_simulation_agent(Agent):
    """
    Factory function to build the SimulationAgent.
    This is called ONLY at runtime, never during tests.
    """
    return Agent(
        name="SimulationAgent",
        model=config.AGENT_MODEL, # ADK requires a string or BaseLlm
        instruction=(
                "You are a senior fixed-income risk analyst.\n\n"
                "Your role:\n"
                "1. Call the tool `simulate_bond_risk` when yield forecasts are provided.\n"
                "2. After the tool returns JSON results, DO NOT repeat the raw JSON.\n"
                "3. Produce a clear, executive-ready narrative that:\n"
                "   - Explains downside yield risk (VaR) across 5Y, 10Y, and 30Y tenors\n"
                "   - Compares curve behavior (front vs long end)\n"
                "   - Interprets results in the context of the market regime\n"
                "   - Uses cautious, decision-oriented language\n\n"
                "Assume the simulation numbers are correct and must not be recalculated."
        ),
        tools=[simulate_bond_risk]
    )
