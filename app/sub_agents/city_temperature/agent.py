from google.adk.agents import Agent
from .tools import get_city_temperature

temperature_agent = Agent(
    model='gemini-2.5-flash',
    name='temperature_agent',
    description='Specialized agent that provides temperature and weather information for cities',
    instruction='You are a weather information expert. Answer questions about temperature and weather conditions for countries using the get_city_temperature tool. Provide temperature in Celsius and current weather conditions.',
    tools=[get_city_temperature]
)