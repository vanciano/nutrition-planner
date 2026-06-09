"""Integration test against a real Databricks warehouse.

Skipped unless RUN_INTEGRATION=1 and a real DATABRICKS_WAREHOUSE_ID are set
(see conftest.pytest_collection_modifyitems).
"""
import pytest

EXPECTED_PHASES = {"menstrual", "follicular", "ovulation", "luteal"}


@pytest.mark.integration
def test_phases_against_real_warehouse(client):
    resp = client.get("/api/phases")
    assert resp.status_code == 200
    phases = resp.json()["phases"]
    assert len(phases) >= 4

    found = {(p.get("cycle_phase") or "").lower() for p in phases}
    assert found.issuperset(EXPECTED_PHASES), (
        f"expected at least {EXPECTED_PHASES}, got {found}"
    )
