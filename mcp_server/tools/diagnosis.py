"""
Pest and weed diagnosis tools for the Lawn Concierge MCP server.

Provides identification and treatment recommendations for common lawn
pests, weeds, and diseases based on user-described symptoms.
"""

from typing import Any


# ─── Common Lawn Pests ────────────────────────────────────────────────────────
PESTS: list[dict] = [
    {
        "name": "Chinch Bug",
        "symptoms": ["yellowing", "browning", "patches", "hot", "sunny", "spreading"],
        "affected_grasses": ["st_augustine", "zoysia", "bermuda"],
        "season": ["June", "July", "August", "September"],
        "treatment": "Apply bifenthrin or permethrin insecticide. Water thoroughly before and after.",
        "prevention": "Maintain proper watering — stressed lawns attract chinch bugs.",
        "severity": "high",
    },
    {
        "name": "Grubs (White Grubs)",
        "symptoms": ["spongy", "turf lifts", "birds pecking", "dead patches", "wilting", "brown"],
        "affected_grasses": ["kentucky_bluegrass", "fescue", "bermuda", "st_augustine"],
        "season": ["July", "August", "September"],
        "treatment": "Apply imidacloprid or chlorantraniliprole in early summer (preventive) or trichlorfon (curative).",
        "prevention": "Apply preventive grub control in May–June before eggs hatch.",
        "severity": "high",
    },
    {
        "name": "Sod Webworm",
        "symptoms": ["chewed blades", "moths flying", "brown patches", "scalped appearance", "night damage"],
        "affected_grasses": ["kentucky_bluegrass", "fescue", "bermuda", "zoysia"],
        "season": ["June", "July", "August"],
        "treatment": "Apply Bacillus thuringiensis (Bt) for organic control, or carbaryl/permethrin.",
        "prevention": "Reduce thatch layer — webworms thrive in thatch.",
        "severity": "medium",
    },
    {
        "name": "Mole Crickets",
        "symptoms": ["tunneling", "raised soil", "spongy", "dying grass", "irregular damage"],
        "affected_grasses": ["bermuda", "st_augustine", "zoysia", "centipede"],
        "season": ["March", "April", "May", "June"],
        "treatment": "Apply fipronil or bifenthrin in late spring when nymphs are small.",
        "prevention": "Bait treatments most effective in April–May.",
        "severity": "high",
    },
    {
        "name": "Armyworms",
        "symptoms": ["rapid defoliation", "skeletonized blades", "caterpillars", "overnight damage"],
        "affected_grasses": ["bermuda", "fescue", "kentucky_bluegrass", "st_augustine"],
        "season": ["August", "September", "October"],
        "treatment": "Apply spinosad or pyrethroid immediately — armyworms can destroy a lawn in days.",
        "prevention": "Monitor in late summer; treat at first sighting.",
        "severity": "critical",
    },
]

# ─── Common Lawn Weeds ────────────────────────────────────────────────────────
WEEDS: list[dict] = [
    {
        "name": "Crabgrass",
        "symptoms": ["wide blades", "spreading low", "summer annual", "light green", "coarse texture"],
        "type": "grassy weed",
        "treatment_pre": "Apply pre-emergent herbicide (prodiamine or dithiopyr) in early spring before soil reaches 55°F.",
        "treatment_post": "Apply quinclorac or fenoxaprop post-emergently when plants are young.",
        "prevention": "Maintain thick, healthy turf — crabgrass exploits thin areas.",
    },
    {
        "name": "Dandelion",
        "symptoms": ["yellow flowers", "broad leaves", "rosette", "taproot", "seed puffs"],
        "type": "broadleaf weed",
        "treatment_pre": "Pre-emergent is not effective on dandelions.",
        "treatment_post": "Apply 2,4-D or triclopyr broadleaf herbicide in fall or spring.",
        "prevention": "Maintain dense, healthy turf and mow at proper height.",
    },
    {
        "name": "Nutsedge",
        "symptoms": ["triangular stem", "yellow-green", "faster growth", "clumps", "waxy leaves"],
        "type": "sedge",
        "treatment_pre": "Apply halosulfuron-methyl or sulfentrazone pre-emergently.",
        "treatment_post": "Apply halosulfuron-methyl (Sedgehammer) post-emergently.",
        "prevention": "Improve drainage — nutsedge thrives in wet, poorly drained areas.",
    },
    {
        "name": "Clover",
        "symptoms": ["three-leaflet", "white flowers", "low-growing", "spreading patches"],
        "type": "broadleaf weed",
        "treatment_pre": "Not applicable.",
        "treatment_post": "Apply 2,4-D + mecoprop (MCPP) combination product.",
        "prevention": "Fertilize with nitrogen — clover fixes its own nitrogen and outcompetes fertilized turf.",
    },
    {
        "name": "Dollar Spot",
        "symptoms": ["small circular spots", "silver dollar size", "bleached", "morning dew", "cobwebby"],
        "type": "fungal disease",
        "treatment_pre": "Preventive fungicides (propiconazole) during warm, humid weather.",
        "treatment_post": "Apply propiconazole, thiophanate-methyl, or azoxystrobin fungicide.",
        "prevention": "Fertilize adequately with nitrogen, water deeply in morning, reduce humidity.",
    },
    {
        "name": "Brown Patch",
        "symptoms": ["large circular patches", "brown ring", "night temps above 70F", "humid", "irregular"],
        "type": "fungal disease",
        "treatment_pre": "Apply preventive fungicide (azoxystrobin) in June–July.",
        "treatment_post": "Apply azoxystrobin, trifloxystrobin, or propiconazole.",
        "prevention": "Avoid watering in evening, improve air circulation, reduce nitrogen in summer.",
    },
]


def diagnose_lawn_problem(
    symptoms: list[str],
    grass_type: str | None = None,
    current_month: str | None = None,
) -> dict[str, Any]:
    """
    Diagnose a lawn problem based on observed symptoms.

    Args:
        symptoms: List of observed symptoms (e.g. ['yellowing patches', 'spongy turf',
                  'birds pecking at lawn']).
        grass_type: Optional grass type to narrow diagnosis.
        current_month: Optional current month (e.g. 'July') to filter seasonal pests.

    Returns:
        dict with top_matches (ranked), treatment_plan, and prevention tips.
    """
    # Normalize symptoms for matching
    symptom_text = " ".join(s.lower() for s in symptoms)

    grass_key = None
    if grass_type:
        grass_key = grass_type.lower().replace(" ", "_").replace("-", "_")

    from datetime import date as _date
    month = current_month or _date.today().strftime("%B")

    matches: list[dict] = []

    # Score pests
    for pest in PESTS:
        score = sum(1 for kw in pest["symptoms"] if kw in symptom_text)
        if score == 0:
            continue
        # Boost if grass type matches
        if grass_key and grass_key in pest["affected_grasses"]:
            score += 2
        # Boost if season matches
        if month in pest.get("season", []):
            score += 1
        matches.append({
            "type": "pest",
            "name": pest["name"],
            "score": score,
            "treatment": pest["treatment"],
            "prevention": pest["prevention"],
            "severity": pest["severity"],
            "affected_grasses": pest["affected_grasses"],
        })

    # Score weeds/diseases
    for weed in WEEDS:
        score = sum(1 for kw in weed["symptoms"] if kw in symptom_text)
        if score == 0:
            continue
        matches.append({
            "type": weed["type"],
            "name": weed["name"],
            "score": score,
            "treatment_pre": weed["treatment_pre"],
            "treatment_post": weed["treatment_post"],
            "prevention": weed["prevention"],
            "severity": "medium",
        })

    # Sort by score descending
    matches.sort(key=lambda x: x["score"], reverse=True)
    top_matches = matches[:3]

    if not top_matches:
        return {
            "diagnosis": "No specific issue identified from the symptoms provided.",
            "recommendation": (
                "Consider: (1) soil test for nutrient deficiencies, "
                "(2) checking irrigation coverage, "
                "(3) consulting your local cooperative extension office."
            ),
            "top_matches": [],
        }

    best = top_matches[0]

    return {
        "diagnosis": f"Most likely issue: {best['name']} ({best['type']})",
        "confidence": "high" if best["score"] >= 3 else "medium" if best["score"] == 2 else "low",
        "top_matches": [
            {k: v for k, v in m.items() if k != "score"}
            for m in top_matches
        ],
        "immediate_action": (
            top_matches[0].get("treatment") or top_matches[0].get("treatment_post")
        ),
        "general_advice": (
            "Always read and follow pesticide/herbicide label directions. "
            "For fungal diseases, improve cultural practices first before applying fungicides."
        ),
    }


_MONTHS_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]

# Preventive (not symptom-triggered) weed/disease treatments, keyed by the
# month their pre-emergent/preventive application should happen.
_PREVENTIVE_WEED_ACTIONS: list[dict] = [
    {
        "name": "Crabgrass",
        "months": ["February", "March", "April"],
        "action": "Apply pre-emergent herbicide (prodiamine or dithiopyr) before soil reaches 55°F.",
    },
    {
        "name": "Dollar Spot",
        "months": ["May", "June"],
        "action": "Apply preventive fungicide (propiconazole) before warm, humid weather sets in.",
    },
    {
        "name": "Brown Patch",
        "months": ["June", "July"],
        "action": "Apply preventive fungicide (azoxystrobin) ahead of peak summer humidity.",
    },
]


def get_pest_prevention_schedule(
    grass_type: str | None = None,
    current_month: str | None = None,
) -> dict[str, Any]:
    """
    Get a PROACTIVE pest/weed/disease prevention schedule — unlike
    diagnose_lawn_problem (which is reactive and needs observed symptoms),
    this surfaces preventive treatments that should happen on a calendar
    basis before any problem is visible.

    Use this when building a seasonal care plan or treatment plan, not just
    when the user describes an active problem.

    Args:
        grass_type: Optional grass type to narrow which pests are relevant.
        current_month: Optional current month (e.g. 'July'). Defaults to
                       the current month.

    Returns:
        dict with due_now (preventive actions for this month), upcoming
        (next 2 months), and general_tips.
    """
    from datetime import date as _date

    month = current_month or _date.today().strftime("%B")
    grass_key = grass_type.lower().replace(" ", "_").replace("-", "_") if grass_type else None
    month_idx = _MONTHS_ORDER.index(month) if month in _MONTHS_ORDER else 0
    next_months = [
        _MONTHS_ORDER[(month_idx + offset) % 12] for offset in (1, 2)
    ]

    def _relevant(affected_grasses: list[str]) -> bool:
        return not grass_key or grass_key in affected_grasses

    due_now: list[dict] = []
    upcoming: list[dict] = []

    for pest in PESTS:
        if not _relevant(pest["affected_grasses"]):
            continue
        entry = {
            "name": pest["name"],
            "type": "pest",
            "action": pest["prevention"],
            "severity": pest["severity"],
        }
        if month in pest.get("season", []):
            due_now.append(entry)
        elif any(m in pest.get("season", []) for m in next_months):
            upcoming.append(entry)

    for weed in _PREVENTIVE_WEED_ACTIONS:
        entry = {"name": weed["name"], "type": "weed/disease", "action": weed["action"]}
        if month in weed["months"]:
            due_now.append(entry)
        elif any(m in weed["months"] for m in next_months):
            upcoming.append(entry)

    return {
        "month": month,
        "grass_type": grass_key,
        "due_now": due_now,
        "upcoming": upcoming,
        "general_tips": [
            "Preventive treatment is cheaper and more effective than curative treatment — "
            "apply before pests/disease appear, not after.",
            "Always read and follow the product label for application rates and timing.",
        ],
    }


def get_pest_library() -> dict[str, Any]:
    """
    Return the full pest and weed library for browsing.

    Returns:
        dict with pests list and weeds list.
    """
    return {
        "pests": [
            {"name": p["name"], "severity": p["severity"], "season": p["season"]}
            for p in PESTS
        ],
        "weeds_and_diseases": [
            {"name": w["name"], "type": w["type"]}
            for w in WEEDS
        ],
    }
