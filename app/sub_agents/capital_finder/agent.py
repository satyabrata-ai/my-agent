from google.adk.agents import Agent
from .tools import get_capital_by_country


capital_finder_agent = Agent(
    model='gemini-2.5-flash',
    name='capital_finder_agent',
    description='Specialized agent that provides information about country capitals',
    instruction='You are a capital city expert. Answer questions about capitals of countries using the get_capital_by_country tool. Provide accurate capital city information in a clear format.',
    tools=[get_capital_by_country]
)