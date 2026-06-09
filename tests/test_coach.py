"""AI Coach endpoint tests — warehouse + LLM client stubbed."""
import pytest

import llm
import recommend
import warehouse

_FOCUS = [
    {"phase": "Menstruation", "nutrient": "Iron", "evidence_level": "Well established",
     "tagline": "Supports energy levels during your period"},
    {"phase": "Menstruation", "nutrient": "Omega-3s (EPA/DHA)", "evidence_level": "Some evidence",
     "tagline": "May help reduce period cramps"},
]


def _meal(meal_id, slot, key_nutrients, name):
    return {
        "meal_id": meal_id, "cycle_phase": "menstrual", "meal_type": slot, "meal_name": name,
        "description": "A nourishing dish.", "key_nutrients": key_nutrients, "prep_time_min": 20,
        "dietary_tags": "vegetarian", "calories": 400, "protein_g": 20.0, "fiber_g": 8.0,
        "iron_mg": 6.0, "magnesium_mg": 80.0, "omega3_g": 0.5, "vitamin_c_mg": 30.0,
        "vitamin_b6_mg": 0.4, "calcium_mg": 120.0, "zinc_mg": 2.0, "image_url": None, "icon": "🍽️",
    }


_MEALS = [
    _meal("MEAL-0001", "breakfast", "iron;protein", "Iron Spinach Omelette"),
    _meal("MEAL-0002", "lunch", "omega3;iron", "Sardine Salad"),
    _meal("MEAL-0003", "snack", "vitamin_c;iron", "Citrus Trail Mix"),
    _meal("MEAL-0004", "dinner", "iron;magnesium", "Beef & Broccoli"),
]


def _fake_query(sql_text, params=None, user_token=None):
    if "focus_nutrients_by_phase" in sql_text:
        return [dict(r) for r in _FOCUS]
    if "cycle_meal_plans c" in sql_text:
        return [dict(r) for r in _MEALS]
    return []


class _FakeMessage:
    def __init__(self, content):
        self.content = content


class _FakeChoice:
    def __init__(self, content):
        self.message = _FakeMessage(content)


class _FakeResp:
    def __init__(self, content):
        self.choices = [_FakeChoice(content)]


class _FakeCompletions:
    def __init__(self, sink):
        self._sink = sink

    def create(self, model=None, messages=None, max_tokens=None):
        self._sink["messages"] = messages
        self._sink["model"] = model
        return _FakeResp("REPLY")


class _FakeClient:
    def __init__(self, sink):
        self.chat = type("Chat", (), {"completions": _FakeCompletions(sink)})()


@pytest.fixture(autouse=True)
def _stub(monkeypatch):
    recommend._focus_cache = None
    monkeypatch.setattr(warehouse, "query", _fake_query)
    yield
    recommend._focus_cache = None


def test_coach_ok_grounds_in_phase_and_plan(client, monkeypatch):
    sink = {}
    monkeypatch.setattr(llm, "client", lambda: _FakeClient(sink))

    resp = client.post("/api/coach", json={
        "messages": [{"role": "user", "content": "why salmon this week?"}],
        "phase": "menstrual",
    })
    assert resp.status_code == 200
    assert resp.json() == {"reply": "REPLY"}

    # the LLM saw a system coach prompt, a grounding context, then the user msg
    sent = sink["messages"]
    assert sent[0]["role"] == "system" and "cycle coach" in sent[0]["content"].lower()
    grounding = sent[1]["content"]
    assert "Iron" in grounding and "Iron Spinach Omelette" in grounding
    assert sent[-1]["content"] == "why salmon this week?"


def test_coach_respects_profile_prefs_in_grounding(client, monkeypatch):
    sink = {}
    monkeypatch.setattr(llm, "client", lambda: _FakeClient(sink))
    # seed a profile via the in-memory store (test-wh backend)
    import db
    db.upsert_profile("demo@local", {"energy_target": 2000, "diets": ["Pescatarian"], "allergies": ["Nuts"]})

    resp = client.post("/api/coach", json={
        "messages": [{"role": "user", "content": "what can I snack on?"}],
        "phase": "menstrual",
    })
    assert resp.status_code == 200
    grounding = sink["messages"][1]["content"]
    assert "Pescatarian" in grounding and "Nuts" in grounding


def test_coach_llm_error_returns_500(client, monkeypatch):
    def boom():
        raise RuntimeError("llm exploded")
    monkeypatch.setattr(llm, "client", boom)

    resp = client.post("/api/coach", json={
        "messages": [{"role": "user", "content": "hi"}], "phase": "menstrual",
    })
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}
