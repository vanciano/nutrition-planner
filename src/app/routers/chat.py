"""AI chat -> actionable nutrition guidance via the Foundation Model API."""
from fastapi import APIRouter, Request
from pydantic import BaseModel

from config import get_logger, settings
import llm
import retrieval

logger = get_logger(__name__)
router = APIRouter()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[Message]
    phase: str | None = None


def _user_token(request: Request) -> str | None:
    if settings.auth_mode != "obo":
        return None
    return request.headers.get("x-forwarded-access-token")


@router.post("/chat")
def chat(body: ChatRequest, request: Request):
    messages = [m.model_dump() for m in body.messages]
    last_user = next(
        (m["content"] for m in reversed(messages) if m["role"] == "user"), ""
    )
    context = retrieval.context_for(
        last_user, phase=body.phase, user_token=_user_token(request)
    )
    reply = llm.chat(messages, phase_context=context)
    return {"reply": reply}
