from google.adk.agents import Agent
from app.sub_agents.simulation_agent.tools import simulate_bond_risk


simulation_agent = Agent(
    name="SimulationAgent",
    model=None,  # Tool-only agent (no LLM)
    instruction=(
        "You are a bond yield risk simulation agent. "
        "You do not perform forecasting, sentiment analysis, or data access. "
        "Given forecasted bond yields and a regime hint, "
        "run Monte Carlo simulations to compute yield VaR "
        "and yield ranges in basis points. "
        "Return structured JSON only."
    ),
    tools=[simulate_bond_risk]
)
