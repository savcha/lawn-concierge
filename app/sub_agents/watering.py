"""
Watering Sub-Agent

Specializes in watering schedule recommendations based on weather forecasts,
grass type, and soil conditions. Delegates to the MCP server for weather data.
"""

import os
from google.adk.agents import Agent
from mcp.client.stdio import StdioServerParameters
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams


def _mcp_toolset() -> MCPToolset:
    """Create an MCPToolset connected to the custom lawn tools MCP server."""
    return MCPToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command="python",
                args=["-m", "mcp_server.server"],
                env={**os.environ},
            ),
        ),
        # Only expose weather-related tools to this sub-agent
        tool_filter=["weather_forecast", "current_weather"],
    )


watering_agent = Agent(
    name="watering_agent",
    model=os.environ.get("AGENT_MODEL", "gemini-2.5-flash"),
    description=(
        "Handles all watering schedule and irrigation questions. "
        "Use this agent when the user asks about: when to water, how much to water, "
        "whether upcoming rain means they should skip watering, drought advice, "
        "or optimal watering times."
    ),
    instruction="""You are the Watering Specialist for the Lawn Concierge service.

Your job is to provide personalized watering recommendations based on:
- Local weather forecast (rain, temperature, humidity)
- Grass type and its water requirements
- Time of year and seasonal context

When giving watering advice:
1. ALWAYS fetch the weather forecast first using the weather_forecast tool.
2. Factor in expected rainfall — if >1 inch of rain is forecast in the next 3 days,
   advise skipping supplemental watering.
3. Recommend watering in the early morning (5–9am) to minimize evaporation and
   reduce disease risk.
4. Advise deep, infrequent watering (1–2x per week) over daily shallow watering.
5. In extreme heat (>95°F), suggest light afternoon misting to cool the canopy
   without promoting fungal disease.

Standard water requirements by grass type (inches/week):
- Bermuda: 1.0"   |  St. Augustine: 1.0"  |  Zoysia: 0.75"
- Fescue: 1.0"    |  Kentucky Bluegrass: 1.25"  |  Centipede: 0.75"

If you don't have the user's location or grass type, ask for them before giving advice.
Do NOT answer questions about mowing, fertilizing, pests, or calendar scheduling —
transfer those back to the orchestrator.
""",
    tools=[_mcp_toolset()],
)
