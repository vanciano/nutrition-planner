"""Grounding context for the AI Coach chat.

Builds a compact, plain-text block from the SAME selection the Plan tab uses —
phase goal/rationale, this week's focus nutrients (+ evidence), today's
recommended meal per slot, and the user's diets/allergies — so the assistant's
meal advice stays consistent with the Plan. Reuses recommend.* and phase_copy.
"""
from config import get_logger
import phase_copy
import recommend

logger = get_logger(__name__)


def _meal_line(slot_label: str, meal: dict) -> str:
    m = meal["macros"]
    nut = ", ".join(meal.get("key_nutrients") or []) or "—"
    return (
        f"- {slot_label}: {meal['name']} "
        f"(key nutrients: {nut}; ~{m['calories']} kcal, {m['protein_g']}g protein, {m['fiber_g']}g fibre)"
    )


def coach_context(phase: str | None, profile: dict, user_token: str | None = None) -> str:
    """Return a grounding string for the LLM, or a generic note if phase is unknown."""
    diets = profile.get("diets") or []
    allergies = profile.get("allergies") or []
    prefs = []
    if diets:
        prefs.append(f"follows: {', '.join(diets)}")
    if allergies:
        prefs.append(f"avoids (allergies): {', '.join(allergies)}")
    prefs_line = "User preferences — " + ("; ".join(prefs) if prefs else "none set") + "."

    p = (phase or "").lower()
    if p not in phase_copy.PHASES:
        return (
            "No specific cycle phase selected. Give general, supportive cycle-aware "
            "nutrition guidance. " + prefs_line
        )

    copy = phase_copy.PHASE_COPY[p]
    parts = [
        f"Current cycle phase: {p}.",
        f"Phase goal: {copy['goal']}.",
        f"Rationale: {copy['rationale']}",
    ]

    try:
        levers = recommend.focus_nutrients(p, user_token=user_token)
        if levers:
            foci = "; ".join(f"{lv['nutrient']} ({lv['evidence']['label']}) — {lv['tagline']}" for lv in levers)
            parts.append(f"This week's focus nutrients: {foci}.")
    except Exception:  # noqa: BLE001 - grounding is best-effort; never fail the chat
        logger.warning("coach_context: focus_nutrients lookup failed", exc_info=True)

    try:
        day = recommend.build_day(p, profile, user_token=user_token)
        lines = [_meal_line(s["label"], s["pool"][0]) for s in day["slots"] if s["pool"]]
        if lines:
            parts.append("Today's recommended plan (already tailored to the user's preferences):\n" + "\n".join(lines))
    except Exception:  # noqa: BLE001
        logger.warning("coach_context: build_day failed", exc_info=True)

    parts.append(prefs_line)
    return "\n".join(parts)
