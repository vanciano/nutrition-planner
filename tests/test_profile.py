"""Profile API — exercised against the in-memory fallback (no DB needed).

A DB-backed round-trip is provided as an ``integration`` test; it is skipped
unless a real Lakebase is configured.
"""
import os

import pytest

import db


@pytest.fixture(autouse=True)
def _clear_store():
    """Reset the in-memory profile store + backend-log flag between tests."""
    db._MEM.clear()
    db._logged_backend = False
    yield
    db._MEM.clear()


def test_get_profile_defaults_when_empty(client):
    resp = client.get("/api/profile")
    assert resp.status_code == 200
    assert resp.json() == {"energy_target": 2000, "diets": [], "allergies": []}


def test_put_then_get_round_trip(client):
    payload = {"energy_target": 2200, "diets": ["Pescatarian"], "allergies": ["Nuts", "Soy"]}
    put = client.put("/api/profile", json=payload)
    assert put.status_code == 200
    assert put.json() == payload

    got = client.get("/api/profile").json()
    assert got == payload


@pytest.mark.parametrize(
    "sent,expected",
    [(9999, 3200), (100, 1400), (2000, 2000)],
)
def test_energy_target_clamped(client, sent, expected):
    resp = client.put("/api/profile", json={"energy_target": sent, "diets": [], "allergies": []})
    assert resp.status_code == 200
    assert resp.json()["energy_target"] == expected


def test_profiles_isolated_per_user(client):
    client.put(
        "/api/profile",
        json={"energy_target": 1800, "diets": ["Vegan"], "allergies": []},
        headers={"x-forwarded-email": "alice@flo.health"},
    )
    client.put(
        "/api/profile",
        json={"energy_target": 2600, "diets": ["Pescatarian"], "allergies": ["Dairy"]},
        headers={"x-forwarded-email": "bob@flo.health"},
    )

    alice = client.get("/api/profile", headers={"x-forwarded-email": "alice@flo.health"}).json()
    bob = client.get("/api/profile", headers={"x-forwarded-email": "bob@flo.health"}).json()

    assert alice == {"energy_target": 1800, "diets": ["Vegan"], "allergies": []}
    assert bob == {"energy_target": 2600, "diets": ["Pescatarian"], "allergies": ["Dairy"]}


def test_invalid_energy_target_rejected(client):
    # Non-int energy_target fails Pydantic validation -> 422.
    resp = client.put(
        "/api/profile",
        json={"energy_target": "lots", "diets": [], "allergies": []},
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_warehouse_round_trip():
    """Round-trip against the real team7 warehouse table (skipped without one)."""
    import warehouse
    from config import settings

    if not db._use_warehouse():
        pytest.skip("warehouse not configured (DATABRICKS_WAREHOUSE_ID is unset/test-wh)")
    key = f"pytest-{os.getpid()}@flo.health"
    try:
        saved = db.upsert_profile(
            key, {"energy_target": 2100, "diets": ["Vegan"], "allergies": ["Nuts"]}
        )
        assert saved == {"energy_target": 2100, "diets": ["Vegan"], "allergies": ["Nuts"]}
        assert db.get_profile(key) == saved
    finally:
        warehouse.query(
            f"DELETE FROM {settings.user_profiles_table} WHERE user_key = :user_key",
            params={"user_key": key},
        )
