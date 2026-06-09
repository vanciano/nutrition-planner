"""Plan tab API: phase-adaptive day plan + meal detail.

GET /api/plan?phase=   -> goal/rationale/tip + focus levers + per-slot meal pools.
GET /api/meals/{id}?phase= -> full meal detail (macros, micros, ingredients, mapping).

Meal selection respects the signed-in user's saved diets/allergies (read via the
profile store) and surfaces the phase's focus nutrients. Warehouse reads run
on-behalf-of the user (their forwarded token), like the profile store.
"""
from fastapi import APIRouter, HTTPException, Query, Request

import db
import phase_copy
import recommend
from config import get_logger

logger = get_logger(__name__)
router = APIRouter()

_DEMO_KEY = "demo@local"


def _user_key(request: Request) -> str:
    return request.headers.get("x-forwarded-email") or _DEMO_KEY


def _user_token(request: Request) -> str | None:
    # Meal dictionaries live in team7; query on-behalf-of the user (None locally).
    return request.headers.get("x-forwarded-access-token")


def _require_phase(phase: str) -> str:
    p = (phase or "").lower()
    if p not in phase_copy.PHASES:
        raise HTTPException(status_code=400, detail=f"unknown phase '{phase}'")
    return p


@router.get("/plan")
def get_plan(request: Request, phase: str = Query("menstrual")):
    phase = _require_phase(phase)
    token = _user_token(request)
    profile = db.get_profile(_user_key(request), user_token=token)
    day = recommend.build_day(phase, profile, user_token=token)
    copy = phase_copy.PHASE_COPY[phase]
    return {
        "phase": phase,
        "goal": copy["goal"],
        "rationale": copy["rationale"],
        "tip": {"short": copy["tip_short"], "long": copy["tip_long"]},
        "focus": day["focus"],
        "slots": day["slots"],
    }


@router.get("/meals/{meal_id}")
def get_meal(meal_id: str, request: Request, phase: str = Query("menstrual")):
    phase = _require_phase(phase)
    meal = recommend.meal_detail(meal_id, phase, user_token=_user_token(request))
    if meal is None:
        raise HTTPException(status_code=404, detail=f"meal '{meal_id}' not found")
    return meal
