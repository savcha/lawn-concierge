"""
Lawn care knowledge tools for the Lawn Concierge MCP server.

Provides evidence-based advice on mowing, fertilizing, and general lawn care
based on grass type, climate zone, and season.
"""

from typing import Any
from datetime import date


# ─── Grass Type Knowledge Base ────────────────────────────────────────────────
# Maps grass types to their care profiles.
GRASS_PROFILES: dict[str, dict] = {
    "bermuda": {
        "climate": "warm-season",
        "mow_height_in": (0.5, 1.5),
        "mow_frequency_summer": "every 5–7 days",
        "mow_frequency_other": "every 10–14 days",
        "fertilize_schedule": ["April", "June", "August"],
        "fertilize_npk": "21-7-14",
        "water_per_week_in": 1.0,
        "dormant_months": ["November", "December", "January", "February", "March"],
        "notes": "Goes dormant (brown) in cool weather — this is normal.",
    },
    "st_augustine": {
        "climate": "warm-season",
        "mow_height_in": (3.0, 4.0),
        "mow_frequency_summer": "every 7–10 days",
        "mow_frequency_other": "every 14 days",
        "fertilize_schedule": ["March", "June", "September"],
        "fertilize_npk": "15-0-15",
        "water_per_week_in": 1.0,
        "dormant_months": ["December", "January", "February"],
        "notes": "Sensitive to chinch bugs and gray leaf spot. Keep mow height high.",
    },
    "kentucky_bluegrass": {
        "climate": "cool-season",
        "mow_height_in": (2.5, 3.5),
        "mow_frequency_summer": "every 7–10 days",
        "mow_frequency_other": "every 5–7 days",
        "fertilize_schedule": ["September", "October", "May"],
        "fertilize_npk": "32-0-8",
        "water_per_week_in": 1.25,
        "dormant_months": ["July", "August"],  # summer dormancy under heat stress
        "notes": "Self-repairs via rhizomes. Fertilize heavily in fall, lightly in spring.",
    },
    "fescue": {
        "climate": "cool-season",
        "mow_height_in": (3.0, 4.0),
        "mow_frequency_summer": "every 10–14 days",
        "mow_frequency_other": "every 7–10 days",
        "fertilize_schedule": ["September", "November", "April"],
        "fertilize_npk": "16-4-8",
        "water_per_week_in": 1.0,
        "dormant_months": [],  # stays green year-round in most climates
        "notes": "Bunch grass — does not self-repair. Overseed bare spots in fall.",
    },
    "zoysia": {
        "climate": "warm-season",
        "mow_height_in": (1.0, 2.5),
        "mow_frequency_summer": "every 7–10 days",
        "mow_frequency_other": "every 14 days",
        "fertilize_schedule": ["May", "July"],
        "fertilize_npk": "15-5-10",
        "water_per_week_in": 0.75,
        "dormant_months": ["November", "December", "January", "February", "March"],
        "notes": "Very drought tolerant once established. Slow to green up in spring.",
    },
    "centipede": {
        "climate": "warm-season",
        "mow_height_in": (1.5, 2.5),
        "mow_frequency_summer": "every 7–14 days",
        "mow_frequency_other": "every 14–21 days",
        "fertilize_schedule": ["May"],
        "fertilize_npk": "15-0-15",
        "water_per_week_in": 0.75,
        "dormant_months": ["November", "December", "January", "February", "March"],
        "notes": "Low-maintenance. Over-fertilizing causes decline. Minimal nitrogen needed.",
    },
}


def get_mowing_schedule(
    grass_type: str,
    current_month: str | None = None,
    lawn_size_sqft: int = 1000,
) -> dict[str, Any]:
    """
    Get a mowing schedule recommendation for a grass type.

    Args:
        grass_type: Type of grass (bermuda, st_augustine, kentucky_bluegrass,
                    fescue, zoysia, centipede).
        current_month: Month name (e.g. 'June'). Defaults to current month.
        lawn_size_sqft: Lawn size in square feet (for time estimate).

    Returns:
        dict with mow_height_in, frequency, is_dormant, tips, estimated_minutes.
    """
    grass_type = grass_type.lower().replace(" ", "_").replace("-", "_")

    if grass_type not in GRASS_PROFILES:
        available = ", ".join(GRASS_PROFILES.keys())
        return {
            "error": f"Unknown grass type '{grass_type}'. Supported: {available}",
            "supported_types": list(GRASS_PROFILES.keys()),
        }

    profile = GRASS_PROFILES[grass_type]
    month = current_month or date.today().strftime("%B")

    # Determine season context
    summer_months = {"May", "June", "July", "August", "September"}
    is_summer = month in summer_months
    is_dormant = month in profile["dormant_months"]

    # Estimate mow time: ~1 min per 100 sqft for a push mower
    est_minutes = max(15, lawn_size_sqft // 100)

    return {
        "grass_type": grass_type,
        "mow_height_range_in": f"{profile['mow_height_in'][0]}–{profile['mow_height_in'][1]}",
        "recommended_height_in": profile["mow_height_in"][1],  # err on the taller side
        "frequency": profile["mow_frequency_summer"] if is_summer else profile["mow_frequency_other"],
        "is_dormant": is_dormant,
        "dormant_advice": (
            "Grass is likely dormant this month. Mow only if actively growing; "
            "keep traffic minimal to avoid damaging crowns."
        ) if is_dormant else None,
        "tips": [
            "Never remove more than 1/3 of the blade height in a single mow.",
            "Mow when grass is dry to prevent clumping and disease spread.",
            "Keep mower blades sharp — dull blades tear grass and increase disease risk.",
            profile["notes"],
        ],
        "estimated_minutes": est_minutes,
    }


def get_fertilizing_schedule(
    grass_type: str,
    current_month: str | None = None,
    lawn_size_sqft: int = 1000,
) -> dict[str, Any]:
    """
    Get a fertilizing schedule and product recommendation for a grass type.

    Args:
        grass_type: Type of grass.
        current_month: Month name. Defaults to current month.
        lawn_size_sqft: Lawn size in square feet (for quantity estimate).

    Returns:
        dict with next_application, npk_ratio, quantity_lbs, annual_schedule, tips.
    """
    grass_type = grass_type.lower().replace(" ", "_").replace("-", "_")

    if grass_type not in GRASS_PROFILES:
        available = ", ".join(GRASS_PROFILES.keys())
        return {
            "error": f"Unknown grass type '{grass_type}'. Supported: {available}",
            "supported_types": list(GRASS_PROFILES.keys()),
        }

    profile = GRASS_PROFILES[grass_type]
    month = current_month or date.today().strftime("%B")

    schedule = profile["fertilize_schedule"]
    is_dormant = month in profile["dormant_months"]

    # Find the next upcoming application month
    months_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ]
    current_idx = months_order.index(month) if month in months_order else 0
    next_app = None
    for m in schedule:
        m_idx = months_order.index(m)
        if m_idx >= current_idx:
            next_app = m
            break
    if next_app is None and schedule:
        next_app = schedule[0] + " (next year)"

    # Rough quantity: ~4 lbs per 1,000 sqft per application (standard slow-release)
    qty_lbs = round((lawn_size_sqft / 1000) * 4, 1)

    return {
        "grass_type": grass_type,
        "npk_ratio": profile["fertilize_npk"],
        "annual_schedule": schedule,
        "next_application_month": next_app,
        "quantity_lbs_per_1000sqft": 4.0,
        "estimated_quantity_lbs": qty_lbs,
        "is_dormant_period": is_dormant,
        "dormant_advice": (
            "Do NOT fertilize during dormancy — nutrients won't be absorbed and "
            "may burn the lawn when it breaks dormancy."
        ) if is_dormant else None,
        "product_tips": [
            f"Look for a slow-release fertilizer with N-P-K ratio close to {profile['fertilize_npk']}.",
            "Apply when soil is moist but grass blades are dry.",
            "Water lightly after application to activate granules.",
            "Never fertilize stressed, heat-damaged grass.",
        ],
    }


def get_aeration_schedule(
    grass_type: str,
    current_month: str | None = None,
) -> dict[str, Any]:
    """
    Get a core aeration (and tie-in overseeding) recommendation for a grass type.

    Args:
        grass_type: Type of grass (bermuda, st_augustine, kentucky_bluegrass,
                    fescue, zoysia, centipede).
        current_month: Month name. Defaults to current month.

    Returns:
        dict with recommended_months, frequency, is_recommended_now, method, tips.
    """
    grass_type = grass_type.lower().replace(" ", "_").replace("-", "_")

    if grass_type not in GRASS_PROFILES:
        available = ", ".join(GRASS_PROFILES.keys())
        return {
            "error": f"Unknown grass type '{grass_type}'. Supported: {available}",
            "supported_types": list(GRASS_PROFILES.keys()),
        }

    profile = GRASS_PROFILES[grass_type]
    month = current_month or date.today().strftime("%B")
    climate = profile["climate"]

    if climate == "cool-season":
        recommended_months = ["September", "October"]
        season_note = (
            "Aerate cool-season grass in early fall, while it's actively growing and "
            "before winter dormancy — this is also the ideal window to overseed bare "
            "or thin areas right after aerating."
        )
        overseed_tie_in = (
            "Overseed immediately after aerating — the holes left by the aerator give "
            "seed direct soil contact for much better germination."
        )
    else:
        recommended_months = ["May", "June"]
        season_note = (
            "Aerate warm-season grass in late spring to early summer, once it's fully "
            "green and actively growing — aerating during dormancy can damage the lawn."
        )
        overseed_tie_in = (
            "Warm-season grasses spread via stolons/rhizomes and usually self-repair "
            "after aeration without needing overseeding."
        )

    is_recommended_now = month in recommended_months
    is_dormant = month in profile["dormant_months"]

    return {
        "grass_type": grass_type,
        "recommended_months": recommended_months,
        "is_recommended_now": is_recommended_now,
        "is_dormant_period": is_dormant,
        "dormant_warning": (
            "Do NOT aerate during dormancy — the lawn can't recover from the "
            "disturbance until it's actively growing again."
        ) if is_dormant else None,
        "frequency": (
            "Annually for heavily-used or clay/compacted soil; every 2–3 years for "
            "average home lawns with light traffic."
        ),
        "method": (
            "Use a core (plug) aerator, not a spike aerator — core aeration physically "
            "removes soil plugs and relieves compaction; spiking just pokes holes and "
            "can make compaction worse."
        ),
        "overseed_tie_in": overseed_tie_in,
        "tips": [
            season_note,
            "Water the day before aerating so the soil is moist enough for the tines to penetrate.",
            "Leave the soil plugs on the lawn to break down naturally — they return nutrients to the soil.",
        ],
    }


def get_lawn_care_advice(
    grass_type: str,
    concern: str,
    current_month: str | None = None,
) -> dict[str, Any]:
    """
    Get general seasonal lawn care advice for a grass type and current concern.

    Args:
        grass_type: Type of grass.
        concern: Free-text concern (e.g. 'lawn is yellowing', 'patchy growth',
                 'preparing for summer', 'overseeding').
        current_month: Month name. Defaults to current month.

    Returns:
        dict with advice, priority_actions, and next_steps.
    """
    grass_type_key = grass_type.lower().replace(" ", "_").replace("-", "_")
    profile = GRASS_PROFILES.get(grass_type_key)
    month = current_month or date.today().strftime("%B")

    concern_lower = concern.lower()

    # Build context-aware advice
    advice_parts = []
    priority_actions = []

    if profile:
        is_dormant = month in profile["dormant_months"]
        climate = profile["climate"]

        if is_dormant:
            advice_parts.append(
                f"{grass_type} is a {climate} grass and is likely dormant in {month}. "
                "Brown color is normal — avoid heavy traffic and aggressive treatments."
            )
            priority_actions.append("Reduce or eliminate watering to match rainfall only.")
            priority_actions.append("Hold all fertilizer applications until green-up.")

        if "yellow" in concern_lower or "yello" in concern_lower:
            advice_parts.append(
                "Yellowing can indicate: (1) nitrogen deficiency — apply a balanced fertilizer, "
                "(2) overwatering — check soil drainage, (3) iron chlorosis — apply chelated iron, "
                "or (4) fungal disease — inspect for irregular patterns."
            )
            priority_actions.append("Conduct a soil test to identify nutrient deficiencies.")
            priority_actions.append("Check irrigation schedule — overwatering is a common cause.")

        if "patch" in concern_lower or "bare" in concern_lower or "thin" in concern_lower:
            if climate == "cool-season":
                advice_parts.append(
                    "For cool-season grasses, fall (September–October) is the best time to overseed bare patches. "
                    "Prepare the area by raking out dead material and loosening the top 1/4 inch of soil."
                )
            else:
                advice_parts.append(
                    "For warm-season grasses, late spring to early summer is ideal for patching. "
                    "Use sod plugs or sprigs for best results rather than seed."
                )
            priority_actions.append("Identify the cause of bare patches before reseeding (disease, insects, drought).")

        if "water" in concern_lower or "drought" in concern_lower or "dry" in concern_lower:
            advice_parts.append(
                f"{grass_type} needs approximately {profile['water_per_week_in']} inch(es) of water per week. "
                "Water deeply and infrequently (1–2x per week) rather than daily shallow watering. "
                "Best time to water is early morning (5–9am) to reduce evaporation and fungal risk."
            )
            priority_actions.append(f"Target {profile['water_per_week_in']} inch/week via rain + irrigation.")

    else:
        advice_parts.append(
            f"Grass type '{grass_type}' not found in the knowledge base. "
            "Providing general lawn care advice."
        )

    # Generic seasonal advice
    summer_months = {"May", "June", "July", "August", "September"}
    if month in summer_months:
        advice_parts.append(
            "General summer care: raise your mowing height by 0.5–1 inch to shade roots and retain moisture. "
            "Avoid fertilizing during heat stress periods."
        )
    elif month in {"September", "October", "November"}:
        advice_parts.append(
            "Fall is ideal for aeration, overseeding (cool-season grasses), and a final fertilizer application."
        )
    elif month in {"March", "April"}:
        advice_parts.append(
            "Spring green-up: light fertilizer application once actively growing, "
            "pre-emergent herbicide for crabgrass prevention, and resume mowing schedule."
        )

    return {
        "grass_type": grass_type,
        "month": month,
        "concern": concern,
        "advice": " ".join(advice_parts) or "Maintain regular mowing, watering, and fertilizing per schedule.",
        "priority_actions": priority_actions or ["Continue regular maintenance schedule."],
        "next_steps": [
            "Monitor lawn weekly and note any changes.",
            "Keep a lawn journal: date, weather, treatments applied.",
            "Consult your local cooperative extension office for region-specific advice.",
        ],
    }
