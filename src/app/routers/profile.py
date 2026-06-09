"""User profile (energy target + dietary preferences + allergies).

Persisted per signed-in user via the profile store (Lakebase in production,
in-memory fallback locally). The user identity is the Databricks-forwarded
email; local dev (no header) collapses to a single ``demo@local`` key.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

import db
from config import get_logger

logger = get_logger(__name__)
router = APIRouter()

_DEMO_KEY = "demo@local"


class ProfileBody(BaseModel):
    energy_target: int
    diets: list[str] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)


def _user_key(request: Request) -> str:
    # Databricks Apps injects/overwrites X-Forwarded-Email at its proxy, so it is
    # trustworthy ONLY because the app is reachable solely through that proxy. If the
    # app were ever exposed directly, a client could spoof this header to read/write
    # another user's profile. Local dev has no proxy -> single shared demo key.
    return request.headers.get("x-forwarded-email") or _DEMO_KEY


def _user_token(request: Request) -> str | None:
    # Profiles live in the team7 schema, which the app service principal cannot access
    # but the signed-in user can (via the app's `sql` user_api_scope). So always run
    # profile queries on-behalf-of the user, regardless of the app's AUTH_MODE. None
    # locally -> the warehouse layer uses the profile/SP credentials instead.
    return request.headers.get("x-forwarded-access-token")


@router.get("/profile")
def get_profile(request: Request):
    return db.get_profile(_user_key(request), user_token=_user_token(request))


@router.put("/profile")
def put_profile(body: ProfileBody, request: Request):
    # db.upsert_profile cleans + clamps (energy_target to CAL bounds) before storing.
    return db.upsert_profile(
        _user_key(request), body.model_dump(), user_token=_user_token(request)
    )
