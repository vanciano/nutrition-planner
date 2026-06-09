"""Cycle-phase nutrient goals, read from the read-only UC sample data."""
from fastapi import APIRouter, Request

from config import get_logger, settings
import warehouse

logger = get_logger(__name__)
router = APIRouter()


def _user_token(request: Request) -> str | None:
    # OBO only when explicitly enabled; otherwise None -> service-principal auth.
    if settings.auth_mode != "obo":
        return None
    return request.headers.get("x-forwarded-access-token")


@router.get("/phases")
def get_phases(request: Request):
    rows = warehouse.query(
        f"SELECT * FROM {settings.phase_goals_table} ORDER BY cycle_phase",
        user_token=_user_token(request),
    )
    # drop the Delta _rescued_data helper column if present
    for r in rows:
        r.pop("_rescued_data", None)
    return {"phases": rows}
