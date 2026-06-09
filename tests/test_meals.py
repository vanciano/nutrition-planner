"""Plan tab API tests — warehouse stubbed, in-memory profile (test-wh)."""
import pytest

import recommend
import warehouse


# --- fixture rows ------------------------------------------------------------
_FOCUS = [
    {"phase": "Menstruation", "nutrient": "Iron", "evidence_level": "Well established",
     "tagline": "Supports energy levels during your period"},
    {"phase": "Menstruation", "nutrient": "Omega-3s (EPA/DHA)", "evidence_level": "Some evidence",
     "tagline": "May help reduce period cramps"},
    {"phase": "Menstruation", "nutrient": "Vitamin C", "evidence_level": "Well established",
     "tagline": "Helps your body absorb iron more effectively"},
]


def _meal(meal_id, slot, key_nutrients, **over):
    row = {
        "meal_id": meal_id, "cycle_phase": "menstrual", "meal_type": slot,
        "meal_name": f"{slot.title()} {meal_id}",
        "description": "A nourishing dish. Second sentence.",
        "key_nutrients": key_nutrients, "prep_time_min": 20, "dietary_tags": "vegetarian",
        "calories": 400, "protein_g": 20.0, "fiber_g": 8.0,
        "iron_mg": 5.0, "magnesium_mg": 80.0, "omega3_g": 0.5, "vitamin_c_mg": 30.0,
        "vitamin_b6_mg": 0.4, "calcium_mg": 120.0, "zinc_mg": 2.0,
        "image_url": "http://img/x.jpg", "icon": "🍽️",
    }
    row.update(over)
    return row


# top pick of each slot collectively covers iron + omega3 + vitamin_c
_CANDIDATES = {
    "breakfast": [_meal("MEAL-0001", "breakfast", "iron;protein"),
                  _meal("MEAL-0010", "breakfast", "magnesium;fiber")],
    "lunch": [_meal("MEAL-0002", "lunch", "omega3;iron"),
              _meal("MEAL-0011", "lunch", "protein")],
    "snack": [_meal("MEAL-0003", "snack", "vitamin_c;iron"),
              _meal("MEAL-0012", "snack", "magnesium")],
    "dinner": [_meal("MEAL-0004", "dinner", "iron;magnesium"),
               _meal("MEAL-0013", "dinner", "fiber")],
}
_INGREDIENTS = [
    {"food_name": "Spinach, raw", "grams": 80.0, "is_primary": True},
    {"food_name": "Lentils, cooked", "grams": 150.0, "is_primary": False},
]


def _fake_query(sql_text, params=None, user_token=None):
    params = params or {}
    s = sql_text
    if "focus_nutrients_by_phase" in s:
        return [dict(r) for r in _FOCUS]
    if "np_meal_ingredients" in s:
        return [dict(r) for r in _INGREDIENTS]
    if "WHERE c.meal_id = :meal_id" in s:  # single meal detail
        mid = params.get("meal_id")
        return [_meal(mid, "breakfast", "iron;protein")] if mid == "MEAL-0001" else []
    if "cycle_meal_plans c" in s:  # candidate pool — all slots in one query
        return [dict(r) for slot_rows in _CANDIDATES.values() for r in slot_rows]
    return []


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    recommend._focus_cache = None  # avoid cross-test cache bleed
    monkeypatch.setattr(warehouse, "query", _fake_query)
    yield
    recommend._focus_cache = None


# --- candidate SQL filters ---------------------------------------------------
def test_candidate_sql_applies_allergy_and_diet_filters():
    sql, params = recommend._candidate_sql(["Nuts"], ["Vegan"])
    assert "contains_nuts" in sql
    assert ":diet0" in sql
    assert params["diet0"] == "%vegan%"


def test_candidate_sql_unknown_labels_ignored():
    sql, params = recommend._candidate_sql(["Bogus"], ["Nonsense"])
    assert "contains_" not in sql
    assert params == {}


# --- /api/plan ---------------------------------------------------------------
def test_get_plan_ok(client):
    resp = client.get("/api/plan?phase=menstrual")
    assert resp.status_code == 200
    body = resp.json()
    assert body["phase"] == "menstrual"
    assert body["goal"] and body["tip"]["short"]
    assert len(body["focus"]) == 3
    assert len(body["slots"]) == 4
    for s in body["slots"]:
        assert s["pool"], f"slot {s['slot']} empty"
        assert s["pool"][0]["macros"]["calories"] > 0


def test_plan_surfaces_focus_nutrients_across_the_day(client):
    body = client.get("/api/plan?phase=menstrual").json()
    focus_tokens = {lv["token"] for lv in body["focus"] if lv["token"]}
    assert focus_tokens == {"iron", "omega3", "vitamin_c"}
    served = set()
    for s in body["slots"]:
        served |= set(s["pool"][0]["key_nutrients"])
    assert focus_tokens <= served  # guarantee-day: every focus nutrient appears


def test_plan_bad_phase_400(client):
    assert client.get("/api/plan?phase=ovulation").status_code == 400


# --- /api/meals/{id} ---------------------------------------------------------
def test_meal_detail_ok(client):
    resp = client.get("/api/meals/MEAL-0001?phase=menstrual")
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"]
    assert body["ingredients"][0]["food_name"] == "Spinach, raw"
    assert body["phase_focus"]  # phase emphasis labels present
    assert "iron" in body["key_nutrients"]


def test_meal_detail_unknown_404(client):
    assert client.get("/api/meals/NOPE?phase=menstrual").status_code == 404
