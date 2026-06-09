"""Static, clinically-approved copy + small mappings for the Plan tab.

The phase goal / rationale / tip text is NOT in any warehouse table — it is the
hedged, medically-reviewed copy from the PRD clinical knowledge base, so it lives
here as a constant. Everything *numeric* (meals, nutrients, evidence levels) comes
from the warehouse; this module only supplies prose and a few lookup maps.

Three UI phases ship (menstrual / follicular / luteal). The DB also has an
``ovulation`` phase, which is clinically folded into follicular and is not exposed.
"""

# UI phase -> the `phase` value used in focus_nutrients_by_phase.
PHASE_TO_FOCUS = {
    "menstrual": "Menstruation",
    "follicular": "Follicular",
    "luteal": "Luteal",
}

PHASES = ("menstrual", "follicular", "luteal")

# Slot order + display labels/times (mirrors the design's SLOT_META).
SLOTS = ("breakfast", "lunch", "snack", "dinner")
SLOT_META = {
    "breakfast": {"label": "Breakfast", "time": "8:30 AM"},
    "lunch": {"label": "Lunch", "time": "1:00 PM"},
    "snack": {"label": "Snack", "time": "4:00 PM"},
    "dinner": {"label": "Dinner", "time": "7:30 PM"},
}

# Per-phase goal line, hedged rationale, and the single "Tip for today".
PHASE_COPY = {
    "menstrual": {
        "goal": "Support energy and comfort during your period",
        "rationale": (
            "Some women experience cramps and low energy during their period. This "
            "week's plan focuses on foods that may help support comfort and keep your "
            "energy steady."
        ),
        "tip_short": "Pair iron-rich foods with a little vitamin C to absorb more.",
        "tip_long": (
            "While you're bleeding, your body draws on its iron stores. The plant iron "
            "in lentils, spinach and seeds is absorbed better alongside vitamin C — a "
            "squeeze of citrus, some peppers or tomato does the job. Small pairings, "
            "not big changes."
        ),
    },
    "follicular": {
        "goal": "Build your nutritional foundations",
        "rationale": (
            "This is often when women feel at their best — a good time to build strong "
            "nutritional habits that support you all cycle long."
        ),
        "tip_short": "Rising energy loves whole-food fuel and healthy fats.",
        "tip_long": (
            "As estrogen climbs, your energy and appetite for activity often rise too. "
            "Whole grains, eggs and healthy fats give your body steady fuel and the B "
            "vitamins it uses to build toward ovulation."
        ),
    },
    "luteal": {
        "goal": "Support satiety and comfort as PMS symptoms may emerge",
        "rationale": (
            "Some women notice more appetite and cravings before their period. This "
            "week's plan focuses on satisfying, nutrient-dense meals to support your "
            "energy, mood, and comfort."
        ),
        "tip_short": "Magnesium and B6 can ease tension and steady mood now.",
        "tip_long": (
            "In the days before your period, magnesium-rich foods (dark chocolate, "
            "seeds, leafy greens) can help relax tense muscles, while B6 from bananas, "
            "fish and poultry supports steady mood. Gentle, satisfying meals help with "
            "cravings too."
        ),
    },
}

# Map a focus_nutrients_by_phase.evidence_level string -> a visual tier.
# Colours mirror the design's evidence-badge palette.
_TIER_STYLE = {
    "good": {"tier": "good", "color": "#12824a", "tint": "#E4F5EC"},
    "moderate": {"tier": "moderate", "color": "#B0760F", "tint": "#FBF0DC"},
    "general": {"tier": "general", "color": "#6B6B73", "tint": "#EEEEF1"},
}


def evidence_style(level: str) -> dict:
    """Return {label, tier, color, tint} for a DB evidence_level string."""
    s = (level or "").strip().lower()
    if "well established" in s or "good" in s or "strong" in s:
        tier = "good"
    elif "moderate" in s or "some evidence" in s:
        tier = "moderate"
    else:
        tier = "general"
    return {"label": level or "General guidance", **_TIER_STYLE[tier]}


# Map a focus nutrient *name* (focus_nutrients_by_phase.nutrient) to the token
# vocabulary used in cycle_meal_plans.key_nutrients (";"-delimited). Names not in
# the meal vocabulary (e.g. "Complex carbohydrates", "Tryptophan") map to None and
# simply don't constrain meal selection.
def nutrient_token(name: str) -> str | None:
    n = (name or "").lower()
    if "omega" in n:
        return "omega3"
    if "iron" in n:
        return "iron"
    if "vitamin c" in n or "vitamin-c" in n:
        return "vitamin_c"
    if "magnesium" in n:
        return "magnesium"
    if "calcium" in n:
        return "calcium"
    if "folate" in n or "folic" in n:
        return "folate"
    if "protein" in n:
        return "protein"
    if "fiber" in n or "fibre" in n:
        return "fiber"
    if "b6" in n or "b vitamin" in n or "b-vitamin" in n:
        return "b6"
    return None


# token -> display label for the meal "key nutrient" tag.
TOKEN_LABEL = {
    "iron": "Iron",
    "magnesium": "Magnesium",
    "omega3": "Omega-3",
    "vitamin_c": "Vitamin C",
    "calcium": "Calcium",
    "folate": "Folate",
    "protein": "Protein",
    "fiber": "Fibre",
    "b6": "Vitamin B6",
}
