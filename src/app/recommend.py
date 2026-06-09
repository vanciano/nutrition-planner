"""Meal recommendation engine for the Plan tab.

Given a cycle phase + the user's profile (diets / allergies), build a one-day plan
(breakfast / lunch / snack / dinner) from the warehouse meal dictionaries, where the
phase's *focus nutrients* are surfaced in the served meals.

Strategy (confirmed: "prefer + guarantee-day"):
  1. Pull the phase's focus nutrients (focus_nutrients_by_phase) -> a set of tokens.
  2. Per slot, fetch candidate meals (cycle_meal_plans + np_meal_nutrition + allergens
     + image), filtered in SQL by the user's allergies (exclude) and diets (require).
  3. Rank candidates by how many focus tokens their key_nutrients hit; keep a small pool.
  4. Guarantee-day pass: if a focus nutrient isn't covered by the top picks, promote a
     candidate that covers it. Never leave a slot empty (fall back to unfiltered).

All numbers come from the warehouse; only the ranking/serialisation is here.
"""
from __future__ import annotations

from config import get_logger, settings
import phase_copy
import warehouse

logger = get_logger(__name__)

# Profile allergy label -> np_meal_allergens boolean column (whitelist; never user SQL).
_ALLERGEN_COL = {
    "Nuts": "contains_nuts",
    "Dairy": "contains_dairy",
    "Gluten": "contains_gluten",
    "Shellfish": "contains_shellfish",
    "Eggs": "contains_eggs",
    "Soy": "contains_soy",
    "Sesame": "contains_sesame",
}
# Profile diet label -> dietary_tags token.
_DIET_TAG = {
    "Vegetarian": "vegetarian",
    "Vegan": "vegan",
    "Pescatarian": "pescatarian",
    "Dairy-free": "dairy_free",
    "Gluten-free": "gluten_free",
}

_POOL_SIZE = 6

# Focus-nutrient cache (service-principal only; per-user OBO never cached).
_focus_cache: dict[str, list[dict]] | None = None


# --- focus nutrients ---------------------------------------------------------
def focus_nutrients(phase: str, user_token: str | None = None) -> list[dict]:
    """Return the phase's focus levers: [{nutrient, tagline, token, evidence{...}}]."""
    global _focus_cache
    if user_token is None and _focus_cache is not None:
        return _focus_cache.get(phase, [])

    rows = warehouse.query(
        f"SELECT phase, nutrient, evidence_level, tagline FROM {settings.focus_nutrients_table}",
        user_token=user_token,
    )
    by_phase: dict[str, list[dict]] = {p: [] for p in phase_copy.PHASES}
    focus_label_to_ui = {v: k for k, v in phase_copy.PHASE_TO_FOCUS.items()}
    for r in rows:
        ui_phase = focus_label_to_ui.get((r.get("phase") or "").strip())
        if not ui_phase:
            continue
        by_phase[ui_phase].append(
            {
                "nutrient": r.get("nutrient"),
                "tagline": r.get("tagline"),
                "token": phase_copy.nutrient_token(r.get("nutrient") or ""),
                "evidence": phase_copy.evidence_style(r.get("evidence_level") or ""),
            }
        )
    if user_token is None:
        _focus_cache = by_phase
    return by_phase.get(phase, [])


def _focus_tokens(levers: list[dict]) -> set[str]:
    return {lv["token"] for lv in levers if lv.get("token")}


# --- candidate meals ---------------------------------------------------------
def _candidate_sql(allergies: list[str], diets: list[str]) -> tuple[str, dict]:
    """Build the candidate query for a phase across ALL slots (one round-trip).

    Allergy columns + the slot list are whitelisted constants (safe to inline);
    diet/phase values are passed as named params. Slots are bucketed in Python.
    """
    clauses = []
    params: dict = {}
    for a in allergies:
        col = _ALLERGEN_COL.get(a)
        if col:
            # contains_* columns are BOOLEAN in the warehouse; exclude meals that have the allergen.
            clauses.append(f"AND NOT COALESCE(a.{col}, false)")
    for i, d in enumerate(diets):
        tag = _DIET_TAG.get(d)
        if tag:
            params[f"diet{i}"] = f"%{tag}%"
            clauses.append(f"AND lower(COALESCE(c.dietary_tags, '')) LIKE :diet{i}")
    slot_list = ", ".join(f"'{s}'" for s in phase_copy.SLOTS)  # constants
    sql = f"""
        SELECT
          c.meal_id, c.cycle_phase, c.meal_type, c.meal_name, c.description,
          c.key_nutrients, c.prep_time_min, c.dietary_tags,
          COALESCE(n.calories_kcal, c.calories) AS calories,
          n.protein_g, n.fiber_g,
          COALESCE(n.iron_mg, c.iron_mg)         AS iron_mg,
          COALESCE(n.magnesium_mg, c.magnesium_mg) AS magnesium_mg,
          COALESCE(n.omega3_g, c.omega3_g)       AS omega3_g,
          COALESCE(n.vitamin_c_mg, c.vitamin_c_mg) AS vitamin_c_mg,
          n.vitamin_b6_mg, n.calcium_mg, n.zinc_mg,
          d.image_url, i.icon
        FROM {settings.cycle_meals_table} c
        LEFT JOIN {settings.meal_nutrition_table} n ON c.meal_id = n.meal_id
        LEFT JOIN {settings.meal_allergens_table} a ON c.meal_id = a.meal_id
        LEFT JOIN {settings.meal_images_table}    i ON c.meal_id = i.meal_id
        LEFT JOIN {settings.meal_images_direct_table} d ON c.meal_id = d.meal_id
        WHERE c.cycle_phase = :phase AND c.meal_type IN ({slot_list})
        {' '.join(clauses)}
    """
    return sql, params


def _tokens(key_nutrients: str | None) -> list[str]:
    return [t.strip() for t in (key_nutrients or "").split(";") if t.strip()]


def _num(v) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _serialize(row: dict, focus: set[str], slot: str) -> dict:
    toks = _tokens(row.get("key_nutrients"))
    # primary tag = first focus token present, else first key nutrient.
    tag = next((t for t in toks if t in focus), toks[0] if toks else None)
    desc = (row.get("description") or "").strip()
    benefit = desc.split(". ")[0].rstrip(".") if desc else ""
    return {
        "meal_id": row.get("meal_id"),
        "name": row.get("meal_name"),
        "slot": slot,
        "meal_type": row.get("meal_type"),
        "description": desc,
        "benefit": benefit,
        "key_nutrients": toks,
        "tag": tag,
        "tag_label": phase_copy.TOKEN_LABEL.get(tag, tag.title() if tag else ""),
        "macros": {
            "protein_g": round(_num(row.get("protein_g")), 1),
            "fiber_g": round(_num(row.get("fiber_g")), 1),
            "calories": round(_num(row.get("calories"))),
        },
        "micros": {
            "iron_mg": round(_num(row.get("iron_mg")), 1),
            "magnesium_mg": round(_num(row.get("magnesium_mg")), 1),
            "omega3_g": round(_num(row.get("omega3_g")), 2),
            "vitamin_c_mg": round(_num(row.get("vitamin_c_mg")), 1),
            "vitamin_b6_mg": round(_num(row.get("vitamin_b6_mg")), 2),
            "calcium_mg": round(_num(row.get("calcium_mg")), 0),
        },
        "image_url": row.get("image_url"),
        "icon": row.get("icon") or "🍽️",
        "prep_time_min": row.get("prep_time_min"),
        "dietary_tags": [t.strip() for t in (row.get("dietary_tags") or "").split(";") if t.strip()],
    }


def _score(meal: dict, focus: set[str]) -> tuple:
    hits = len(set(meal["key_nutrients"]) & focus)
    # tiebreak: summed magnitude of the focus micros present.
    mag = 0.0
    mi = meal["micros"]
    if "iron" in focus:
        mag += mi["iron_mg"] / 18
    if "magnesium" in focus:
        mag += mi["magnesium_mg"] / 320
    if "omega3" in focus:
        mag += mi["omega3_g"] / 1.6
    if "vitamin_c" in focus:
        mag += mi["vitamin_c_mg"] / 75
    if "calcium" in focus:
        mag += mi["calcium_mg"] / 1000
    if "b6" in focus:
        mag += mi["vitamin_b6_mg"] / 1.9
    return (hits, round(mag, 3))


def _fetch_candidates(phase: str, profile: dict, focus: set[str], user_token: str | None) -> list[dict]:
    """All candidate meals for the phase (every slot) in one warehouse query."""
    allergies = profile.get("allergies") or []
    diets = profile.get("diets") or []
    sql, params = _candidate_sql(allergies, diets)
    params["phase"] = phase
    rows = warehouse.query(sql, params=params, user_token=user_token)
    return [_serialize(r, focus, (r.get("meal_type") or "").lower()) for r in rows]


def _bucket(meals: list[dict], focus: set[str]) -> dict[str, list[dict]]:
    """Group meals by slot, rank each pool by focus-nutrient match, trim."""
    pools: dict[str, list[dict]] = {s: [] for s in phase_copy.SLOTS}
    for m in meals:
        if m["slot"] in pools:
            pools[m["slot"]].append(m)
    for slot in pools:
        pools[slot].sort(key=lambda m: _score(m, focus), reverse=True)
        pools[slot] = pools[slot][:_POOL_SIZE]
    return pools


# --- whole-day plan ----------------------------------------------------------
def build_day(phase: str, profile: dict, user_token: str | None = None) -> dict:
    """Return {focus, slots:[{slot,label,time,pool:[meal]}]} for the phase.

    One query fetches every slot's candidates (filtered by diet/allergy); a second
    unfiltered query only runs as a fallback if filtering empties a slot.
    Guarantee-day: reorder pools so the day's top picks collectively cover the
    focus nutrients where possible.
    """
    levers = focus_nutrients(phase, user_token=user_token)
    focus = _focus_tokens(levers)

    pools = _bucket(_fetch_candidates(phase, profile, focus, user_token), focus)

    # fallback: if filters emptied any slot, top it up from the unfiltered set.
    missing = [s for s in phase_copy.SLOTS if not pools[s]]
    if missing and (profile.get("diets") or profile.get("allergies")):
        extra = _bucket(_fetch_candidates(phase, {}, focus, user_token), focus)
        for s in missing:
            pools[s] = extra[s]

    # guarantee-day: cover each focus token with at least one top pick if any pool can.
    covered: set[str] = set()
    for slot in phase_copy.SLOTS:
        if pools[slot]:
            covered |= set(pools[slot][0]["key_nutrients"]) & focus
    for token in focus - covered:
        for slot in phase_copy.SLOTS:
            pool = pools[slot]
            idx = next((i for i, m in enumerate(pool) if token in m["key_nutrients"]), None)
            if idx and idx > 0:  # found below the top -> promote it
                pool.insert(0, pool.pop(idx))
                covered |= set(pool[0]["key_nutrients"]) & focus
                break

    slots = [
        {
            "slot": slot,
            "label": phase_copy.SLOT_META[slot]["label"],
            "time": phase_copy.SLOT_META[slot]["time"],
            "pool": pools[slot],
        }
        for slot in phase_copy.SLOTS
        if pools[slot]  # drop a slot only if it has no meals at all
    ]
    return {"focus": levers, "slots": slots}


# --- single meal detail ------------------------------------------------------
def meal_detail(meal_id: str, phase: str, user_token: str | None = None) -> dict | None:
    """Full detail for one meal: nutrition + ingredients + allergens + phase mapping."""
    rows = warehouse.query(
        f"""
        SELECT
          c.meal_id, c.cycle_phase, c.meal_type, c.meal_name, c.description,
          c.key_nutrients, c.prep_time_min, c.dietary_tags,
          COALESCE(n.calories_kcal, c.calories) AS calories,
          n.protein_g, n.fiber_g,
          COALESCE(n.iron_mg, c.iron_mg)           AS iron_mg,
          COALESCE(n.magnesium_mg, c.magnesium_mg) AS magnesium_mg,
          COALESCE(n.omega3_g, c.omega3_g)         AS omega3_g,
          COALESCE(n.vitamin_c_mg, c.vitamin_c_mg) AS vitamin_c_mg,
          n.vitamin_b6_mg, n.calcium_mg, n.zinc_mg,
          d.image_url, i.icon
        FROM {settings.cycle_meals_table} c
        LEFT JOIN {settings.meal_nutrition_table} n ON c.meal_id = n.meal_id
        LEFT JOIN {settings.meal_images_table}    i ON c.meal_id = i.meal_id
        LEFT JOIN {settings.meal_images_direct_table} d ON c.meal_id = d.meal_id
        WHERE c.meal_id = :meal_id
        LIMIT 1
        """,
        params={"meal_id": meal_id},
        user_token=user_token,
    )
    if not rows:
        return None

    levers = focus_nutrients(phase, user_token=user_token)
    focus = _focus_tokens(levers)
    meal = _serialize(rows[0], focus, rows[0].get("meal_type") or "")

    ings = warehouse.query(
        f"""
        SELECT food_name, grams, is_primary
        FROM {settings.meal_ingredients_table}
        WHERE meal_id = :meal_id
        ORDER BY is_primary DESC, grams DESC
        """,
        params={"meal_id": meal_id},
        user_token=user_token,
    )
    meal["ingredients"] = [
        {"food_name": r.get("food_name"), "grams": _num(r.get("grams"))} for r in ings
    ]
    # focus nutrient labels this phase emphasises (for the "supports your phase" line).
    meal["phase_focus"] = [
        phase_copy.TOKEN_LABEL.get(lv["token"], lv["nutrient"])
        for lv in levers
        if lv.get("token")
    ][:3]
    meal["phase"] = phase
    return meal
