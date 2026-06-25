"""
Lawn Concierge — Custom MCP Server

Exposes lawn care tools via the Model Context Protocol (MCP).
The ADK orchestrator connects to this server via stdio subprocess.

Run directly for debugging:
    python -m mcp_server.server
"""

from mcp.server.fastmcp import FastMCP

from mcp_server.tools.weather import get_weather_forecast, get_current_conditions
from mcp_server.tools.lawn_advisor import (
    get_mowing_schedule,
    get_fertilizing_schedule,
    get_aeration_schedule,
    get_lawn_care_advice,
)
from mcp_server.tools.diagnosis import (
    diagnose_lawn_problem,
    get_pest_prevention_schedule,
    get_pest_library,
)

# ─── Create the MCP server ────────────────────────────────────────────────────
mcp = FastMCP(
    name="lawn-tools",
    instructions=(
        "You are the Lawn Concierge tool server. "
        "Provide accurate, evidence-based lawn care advice. "
        "Always consider the user's grass type and location when giving recommendations."
    ),
)


# ─── Weather Tools ────────────────────────────────────────────────────────────

@mcp.tool()
async def weather_forecast(location: str, days: int = 7) -> dict:
    """
    Get a multi-day weather forecast and watering advice for a location.

    Use this tool when the user asks about:
    - Whether they need to water their lawn
    - Upcoming rain that might affect lawn care plans
    - Weather conditions for mowing, fertilizing, or treating the lawn

    Args:
        location: City name or 'City,CountryCode' (e.g., 'Austin,US', 'Portland,US').
        days: Number of forecast days (1–7). Default is 7.
    """
    return await get_weather_forecast(location, days)


@mcp.tool()
async def current_weather(location: str) -> dict:
    """
    Get current weather conditions for a location.

    Use this for immediate lawn care decisions (e.g., 'is it a good day to mow?').

    Args:
        location: City name or 'City,CountryCode'.
    """
    return await get_current_conditions(location)


# ─── Lawn Care Tools ──────────────────────────────────────────────────────────

@mcp.tool()
def mowing_schedule(
    grass_type: str,
    current_month: str | None = None,
    lawn_size_sqft: int = 1000,
) -> dict:
    """
    Get mowing height and frequency recommendations for a grass type.

    Use this when the user asks:
    - How often should I mow?
    - What height should I set my mower?
    - When should I start/stop mowing for the season?

    Args:
        grass_type: Grass type — one of: bermuda, st_augustine, kentucky_bluegrass,
                    fescue, zoysia, centipede.
        current_month: Current month name (e.g., 'July'). Auto-detected if omitted.
        lawn_size_sqft: Lawn area in square feet for mow time estimate.
    """
    return get_mowing_schedule(grass_type, current_month, lawn_size_sqft)


@mcp.tool()
def fertilizing_schedule(
    grass_type: str,
    current_month: str | None = None,
    lawn_size_sqft: int = 1000,
) -> dict:
    """
    Get fertilizer type, timing, and quantity recommendations for a grass type.

    Use this when the user asks:
    - When should I fertilize my lawn?
    - What fertilizer should I use?
    - How much fertilizer do I need?

    Args:
        grass_type: Grass type — one of: bermuda, st_augustine, kentucky_bluegrass,
                    fescue, zoysia, centipede.
        current_month: Current month name. Auto-detected if omitted.
        lawn_size_sqft: Lawn area in square feet for quantity estimate.
    """
    return get_fertilizing_schedule(grass_type, current_month, lawn_size_sqft)


@mcp.tool()
def aeration_schedule(
    grass_type: str,
    current_month: str | None = None,
) -> dict:
    """
    Get a core aeration (and overseeding tie-in) recommendation for a grass type.

    Use this when the user asks about soil compaction, thatch buildup,
    overseeding timing, or when building a full seasonal/treatment plan —
    aeration should be part of any complete lawn care plan, not just
    mowing and fertilizing.

    Args:
        grass_type: Grass type — one of: bermuda, st_augustine, kentucky_bluegrass,
                    fescue, zoysia, centipede.
        current_month: Current month name. Auto-detected if omitted.
    """
    return get_aeration_schedule(grass_type, current_month)


@mcp.tool()
def lawn_care_advice(
    grass_type: str,
    concern: str,
    current_month: str | None = None,
) -> dict:
    """
    Get general seasonal lawn care advice for a specific concern.

    Use this when the user asks open-ended questions like:
    - My lawn looks bad, what should I do?
    - How do I prepare my lawn for summer?
    - Why is my lawn patchy?

    Args:
        grass_type: Grass type.
        concern: Description of the issue or question (e.g., 'lawn is yellowing',
                 'preparing for summer heat', 'overseeding bare spots').
        current_month: Current month name. Auto-detected if omitted.
    """
    return get_lawn_care_advice(grass_type, concern, current_month)


# ─── Diagnosis Tools ──────────────────────────────────────────────────────────

@mcp.tool()
def diagnose_problem(
    symptoms: list[str],
    grass_type: str | None = None,
    current_month: str | None = None,
) -> dict:
    """
    Diagnose a lawn pest, weed, or disease problem from symptoms.

    Use this when the user describes visible lawn problems like:
    - Patches, spots, or discoloration
    - Insects or damage patterns
    - Unusual growth or wilting

    Args:
        symptoms: List of observed symptoms. Be descriptive, e.g.:
                  ['yellowing circular patches', 'spongy turf', 'birds pecking'].
        grass_type: Optional grass type to narrow results.
        current_month: Optional month to filter seasonal pests.
    """
    return diagnose_lawn_problem(symptoms, grass_type, current_month)


@mcp.tool()
def pest_prevention_schedule(
    grass_type: str | None = None,
    current_month: str | None = None,
) -> dict:
    """
    Get a PROACTIVE pest/weed/disease prevention schedule for this month and
    the next two months — unlike diagnose_problem (which is reactive and
    requires observed symptoms), this surfaces preventive treatments that
    should happen on a calendar basis before any problem is visible.

    Use this whenever building a seasonal care plan or treatment plan, even
    if the user hasn't described any active symptoms — proactive pest
    control should be part of any complete lawn care plan.

    Args:
        grass_type: Optional grass type to narrow which pests are relevant.
        current_month: Optional current month (e.g. 'July'). Auto-detected if omitted.
    """
    return get_pest_prevention_schedule(grass_type, current_month)


@mcp.tool()
def pest_weed_library() -> dict:
    """
    Return the full catalog of common lawn pests, weeds, and diseases.

    Use this when the user wants to browse available diagnoses or learn what
    pests are common in their area/season.
    """
    return get_pest_library()


# ─── Entry Point ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # Run as a stdio MCP server (used by ADK MCPToolset)
    mcp.run(transport="stdio")
