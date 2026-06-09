import warehouse


_FAKE_ROWS = [
    {"cycle_phase": "menstrual", "iron_mg": 18, "_rescued_data": "junk"},
    {"cycle_phase": "follicular", "iron_mg": 14, "_rescued_data": "junk"},
    {"cycle_phase": "ovulation", "iron_mg": 12, "_rescued_data": "junk"},
    {"cycle_phase": "luteal", "iron_mg": 16, "_rescued_data": "junk"},
]


def test_get_phases_ok(client, monkeypatch):
    monkeypatch.setattr(
        warehouse, "query", lambda *a, **k: [dict(r) for r in _FAKE_ROWS]
    )
    resp = client.get("/api/phases")
    assert resp.status_code == 200
    body = resp.json()
    assert "phases" in body
    phases = body["phases"]
    assert len(phases) == 4
    # _rescued_data must be stripped from every row
    for row in phases:
        assert "_rescued_data" not in row
    returned = {p["cycle_phase"] for p in phases}
    assert returned == {"menstrual", "follicular", "ovulation", "luteal"}


def test_get_phases_query_error_returns_500(client, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("warehouse blew up")

    monkeypatch.setattr(warehouse, "query", boom)
    resp = client.get("/api/phases")
    assert resp.status_code == 500
    assert resp.json() == {"detail": "Internal server error"}
