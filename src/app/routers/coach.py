"""AI Coach — follow-up Q&A about the user's recommended meals.

Additive feature: a chat endpoint grounded in the SAME selection the Plan tab
uses (current phase + profile + the recommended day plan + focus nutrients), so
the assistant can answer follow-ups like "swap my lunch for something lighter"
or "why salmon this week?". Reuses llm.client() — does not modify the existing
nutrition /api/chat path.
"""
from fastapi import APIRouter, Request
from pydantic import BaseModel

import coach_context
import db
import llm
from config import get_logger, settings

logger = get_logger(__name__)
router = APIRouter()

_DEMO_KEY = "demo@local"

COACH_SYSTEM_PROMPT = (
    "You are Flo's cycle coach inside the Flo app. The user is looking at a meal "
    "plan recommended for their current menstrual cycle phase, and is asking "
    "follow-up questions about it. Answer using the provided grounding context — "
    "cite this week's focus nutrients and the user's recommended meals, and always "
    "respect their dietary preferences and allergies (never suggest a food they "
    "avoid; meals are not guaranteed allergen-free). If they ask about exercise or "
    "movement, give gentle, phase-appropriate guidance (follicular/ovulation often "
    "suit higher intensity; luteal/menstrual often suit lower-impact movement and "
    "recovery) — as what many women find helpful, not prescriptive. Use a warm, "
    "hedged tone ('some women find…', 'this may help…'), keep replies short and "
    "skimmable, never frame food as restriction or weight loss, and never give "
    "medical diagnoses — suggest a clinician for medical concerns."
)


class Message(BaseModel):
    role: str
    content: str


class CoachRequest(BaseModel):
    messages: list[Message]
    phase: str | None = None


def _user_key(request: Request) -> str:
    return request.headers.get("x-forwarded-email") or _DEMO_KEY


def _user_token(request: Request) -> str | None:
    # Grounding reads team7 (plan + profile) on-behalf-of the user, like the
    # plan/profile endpoints. None locally -> warehouse uses SP/profile creds.
    return request.headers.get("x-forwarded-access-token")


@router.post("/coach")
def coach(body: CoachRequest, request: Request):
    token = _user_token(request)
    profile = db.get_profile(_user_key(request), user_token=token)
    context = coach_context.coach_context(body.phase, profile, user_token=token)

    msgs = [
        {"role": "system", "content": COACH_SYSTEM_PROMPT},
        {"role": "system", "content": f"Grounding context (the user's current plan):\n{context}"},
    ]
    msgs.extend(m.model_dump() for m in body.messages)

    resp = llm.client().chat.completions.create(
        model=settings.llm_endpoint, messages=msgs, max_tokens=600
    )
    reply = resp.choices[0].message.content or ""
    logger.info("coach reply: %d chars (context=%dB)", len(reply), len(context))
    return {"reply": reply}
